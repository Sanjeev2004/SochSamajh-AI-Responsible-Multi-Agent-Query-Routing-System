from __future__ import annotations

import uuid
from langgraph.graph import StateGraph, END

from agents.classifier import pre_screen_query, classify_intent
from agents.general import run_general_agent
from agents.legal import run_legal_agent
from agents.medical import run_medical_agent
from agents.safety import run_safety_agent
from agents.formatter import run_formatter
from core.config import Settings, logger
from core.state import GraphState, SafetyFlags


settings = Settings.load()


def _apply_safety_flags(state: GraphState) -> GraphState:
    classification = state["classification"]
    flags = SafetyFlags(
        self_harm=classification.self_harm,
        illegal_request=classification.illegal_request,
        high_risk=classification.risk_level == "high",
    )
    state["safety_flags"] = flags
    return state


def pre_screen_node(state: GraphState) -> GraphState:
    query = state["query"]
    pre_screen = pre_screen_query(query)
    if pre_screen:
        logger.info("Pre-screen override triggered")
        state["classification"] = pre_screen
        state = _apply_safety_flags(state)
    return state


def classifier_node(state: GraphState) -> GraphState:
    query = state["query"]
    classification = classify_intent(query, settings)
    state["classification"] = classification
    state = _apply_safety_flags(state)
    return state


def medical_node(state: GraphState) -> GraphState:
    response = run_medical_agent(state["query"], state["classification"], settings)
    state["response"] = response
    return state


def legal_node(state: GraphState) -> GraphState:
    response = run_legal_agent(state["query"], state["classification"], settings)
    state["response"] = response
    return state


def general_node(state: GraphState) -> GraphState:
    response = run_general_agent(state["query"], state["classification"], settings)
    state["response"] = response
    return state


def safety_node(state: GraphState) -> GraphState:
    response = run_safety_agent(state["query"], state["classification"])
    state["response"] = response
    return state


def formatter_node(state: GraphState) -> GraphState:
    response = run_formatter(state["response"], state["classification"])
    state["response"] = response
    return state


def route_after_pre_screen(state: GraphState) -> str:
    classification = state.get("classification")
    # Pre-screen has highest priority for safety. If any high-risk signal is found,
    # bypass the LLM classifier to avoid unsafe handling.
    if classification and (classification.self_harm or classification.illegal_request or classification.risk_level == "high"):
        return "safety"
    return "classifier"


def route_after_classification(state: GraphState) -> str:
    classification = state["classification"]
    # Safety-first routing: any high-risk or disallowed intent goes directly to Safety Agent.
    if classification.self_harm or classification.illegal_request or classification.risk_level == "high":
        return "safety"
    # Domain routing based on structured classifier output.
    if classification.domain == "medical":
        return "medical"
    if classification.domain == "legal":
        return "legal"
    return "general"


def build_graph() -> StateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("pre_screen", pre_screen_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("medical", medical_node)
    graph.add_node("legal", legal_node)
    graph.add_node("general", general_node)
    graph.add_node("safety", safety_node)
    graph.add_node("formatter", formatter_node)

    graph.set_entry_point("pre_screen")
    graph.add_conditional_edges("pre_screen", route_after_pre_screen)
    graph.add_conditional_edges("classifier", route_after_classification)

    graph.add_edge("medical", "formatter")
    graph.add_edge("legal", "formatter")
    graph.add_edge("general", "formatter")
    graph.add_edge("formatter", END)
    graph.add_edge("safety", END)

    return graph


def run_router(query: str) -> GraphState:
    request_id = str(uuid.uuid4())
    graph = build_graph().compile()
    initial_state: GraphState = {
        "query": query,
        "request_id": request_id,
    }
    result = graph.invoke(initial_state)
    safety_flags = result.get("safety_flags")
    if safety_flags and (safety_flags.high_risk or safety_flags.self_harm or safety_flags.illegal_request):
        logger.info("Safety-flagged interaction", extra={"request_id": request_id})
    return result
