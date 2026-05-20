from __future__ import annotations

from dataclasses import replace

import agents.general as general_agent
from core.config import Settings
from core.state import ClassificationOutput


SETTINGS = replace(Settings.load(), enable_llm=True, enable_retriever=False)


def _classification() -> ClassificationOutput:
    return ClassificationOutput(
        domain="general",
        risk_level="low",
        needs_disclaimer=False,
        self_harm=False,
        illegal_request=False,
        reasoning="test",
    )


def test_wellbeing_query_uses_specific_llm_instruction(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_call_llm(**kwargs):
        captured["system_prompt"] = kwargs["system_prompt"]
        return "What to try now:\n- Take one small recovery break."

    monkeypatch.setattr(general_agent, "call_llm", fake_call_llm)

    response = general_agent.run_general_agent(
        "How do I deal with burnout from work?",
        _classification(),
        SETTINGS,
    )

    assert "burnout, stress, anxiety, or overwhelm" in captured["system_prompt"]
    assert "workload boundaries" in captured["system_prompt"]
    assert "section label on its own line" in captured["system_prompt"]
    assert "What to try now:" in response.content
    assert response.disclaimers


def test_wellbeing_fallback_is_not_ambiguity_template(monkeypatch) -> None:
    def fake_call_llm(**kwargs):
        raise RuntimeError("api unavailable")

    monkeypatch.setattr(general_agent, "call_llm", fake_call_llm)

    response = general_agent.run_general_agent(
        "I have been feeling very stressed and anxious lately, what should I do?",
        _classification(),
        SETTINGS,
    )

    assert "To guide you better, please clarify:" not in response.content
    assert "What to try now:" in response.content
    assert "Stress and anxiety" in response.content
    assert response.disclaimers


def test_explainer_query_uses_direct_answer_instruction(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_call_llm(**kwargs):
        captured["system_prompt"] = kwargs["system_prompt"]
        return "Machine learning lets computers learn patterns from data."

    monkeypatch.setattr(general_agent, "call_llm", fake_call_llm)

    response = general_agent.run_general_agent(
        "What is machine learning?",
        _classification(),
        SETTINGS,
    )

    assert "clear educational or explainer question" in captured["system_prompt"]
    assert "Do not ask for more information" in captured["system_prompt"]
    assert "Machine learning" in response.content


def test_explainer_fallback_does_not_use_clarification_template(monkeypatch) -> None:
    def fake_call_llm(**kwargs):
        raise RuntimeError("api unavailable")

    monkeypatch.setattr(general_agent, "call_llm", fake_call_llm)

    response = general_agent.run_general_agent(
        "What is machine learning?",
        _classification(),
        SETTINGS,
    )

    assert "To guide you better, please clarify:" not in response.content
    assert "could not reach the live LLM" in response.content
