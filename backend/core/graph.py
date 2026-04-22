from __future__ import annotations

import time
import uuid

from langgraph.graph import END, StateGraph

from agents.classifier import classify_intent, pre_screen_query
from agents.critic import run_critic
from agents.formatter import run_formatter
from agents.general import run_general_agent
from agents.legal import run_legal_agent
from agents.medical import run_medical_agent
from agents.safety import run_safety_agent
from core.config import Settings, logger
from core.state import GraphState, SafetyFlags


def _trace(state: GraphState, step: str) -> None:
    state.setdefault("pipeline_trace", [])
    state["pipeline_trace"].append(step)


def _apply_safety_flags(state: GraphState) -> GraphState:
    classification = state["classification"]
    flags = SafetyFlags(
        self_harm=classification.self_harm,
        illegal_request=classification.illegal_request,
        high_risk=classification.risk_level == "high",
    )
    state["safety_flags"] = flags
    return state


def build_graph(settings: Settings) -> StateGraph:
    def pre_screen_node(state: GraphState) -> GraphState:
        _trace(state, "pre_screen")
        query = state["query"]
        pre_screen = pre_screen_query(query)
        if pre_screen:
            logger.info("Pre-screen override triggered", extra={"request_id": state.get("request_id", "unknown")})
            state["classification"] = pre_screen
            state = _apply_safety_flags(state)
        return state

    def classifier_node(state: GraphState) -> GraphState:
        _trace(state, "classifier")
        query = state["query"]
        classification = classify_intent(query, settings)
        state["classification"] = classification
        state = _apply_safety_flags(state)
        return state

    def medical_node(state: GraphState) -> GraphState:
        _trace(state, "medical_agent")
        state["response"] = run_medical_agent(state["query"], state["classification"], settings)
        return state

    def legal_node(state: GraphState) -> GraphState:
        _trace(state, "legal_agent")
        state["response"] = run_legal_agent(state["query"], state["classification"], settings)
        return state

    def general_node(state: GraphState) -> GraphState:
        _trace(state, "general_agent")
        state["response"] = run_general_agent(state["query"], state["classification"], settings)
        return state

    def safety_node(state: GraphState) -> GraphState:
        _trace(state, "safety_agent")
        state["response"] = run_safety_agent(state["query"], state["classification"])
        return state

    def critic_node(state: GraphState) -> GraphState:
        _trace(state, "critic")
        state["response"] = run_critic(state["response"], state["classification"], state["query"])
        return state

    def formatter_node(state: GraphState) -> GraphState:
        _trace(state, "formatter")
        state["response"] = run_formatter(state["response"], state["classification"], state["query"])
        return state

    def route_after_pre_screen(state: GraphState) -> str:
        classification = state.get("classification")
        if classification and (classification.self_harm or classification.illegal_request):
            return "safety"
        return "classifier"

    def route_after_classification(state: GraphState) -> str:
        classification = state["classification"]
        if classification.self_harm or classification.illegal_request:
            return "safety"
        if classification.domain == "medical":
            return "medical"
        if classification.domain == "legal":
            return "legal"
        return "general"

    graph = StateGraph(GraphState)
    graph.add_node("pre_screen", pre_screen_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("medical", medical_node)
    graph.add_node("legal", legal_node)
    graph.add_node("general", general_node)
    graph.add_node("safety", safety_node)
    graph.add_node("critic", critic_node)
    graph.add_node("formatter", formatter_node)

    graph.set_entry_point("pre_screen")
    graph.add_conditional_edges("pre_screen", route_after_pre_screen)
    graph.add_conditional_edges("classifier", route_after_classification)
    graph.add_edge("medical", "critic")
    graph.add_edge("legal", "critic")
    graph.add_edge("general", "critic")
    graph.add_edge("critic", "formatter")
    graph.add_edge("formatter", END)
    graph.add_edge("safety", END)
    return graph


DEFAULT_SETTINGS = Settings.load()
COMPILED_GRAPH = build_graph(DEFAULT_SETTINGS).compile()


def run_router(query: str, settings: Settings | None = None) -> GraphState:
    active_settings = settings or DEFAULT_SETTINGS
    compiled_graph = COMPILED_GRAPH if active_settings == DEFAULT_SETTINGS else build_graph(active_settings).compile()

    request_id = str(uuid.uuid4())
    started_at = time.perf_counter()
    initial_state: GraphState = {
        "query": query,
        "request_id": request_id,
        "pipeline_trace": [],
    }
    result = compiled_graph.invoke(initial_state)
    latency_seconds = round(time.perf_counter() - started_at, 4)
    classification = result.get("classification")
    safety_flags = result.get("safety_flags")

    log_payload = {
        "request_id": request_id,
        "latency_seconds": latency_seconds,
        "domain": classification.domain if classification else "unknown",
        "risk_level": classification.risk_level if classification else "unknown",
        "self_harm": safety_flags.self_harm if safety_flags else False,
        "illegal_request": safety_flags.illegal_request if safety_flags else False,
        "high_risk": safety_flags.high_risk if safety_flags else False,
        "retriever_enabled": active_settings.enable_retriever,
    }
    logger.info("Router request completed", extra=log_payload)
    return result
