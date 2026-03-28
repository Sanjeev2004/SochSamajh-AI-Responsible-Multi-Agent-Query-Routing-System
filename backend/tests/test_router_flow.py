from __future__ import annotations

from dataclasses import replace

import agents.general as general_agent
import agents.legal as legal_agent
import agents.medical as medical_agent
from core.config import Settings
from core.graph import run_router


SETTINGS = replace(Settings.load(), enable_retriever=False)


def test_router_flow_formats_legal_next_steps(monkeypatch) -> None:
    monkeypatch.setattr(legal_agent, "call_llm", lambda **kwargs: "Keep written records of the issue.")

    state = run_router(
        "My landlord is refusing to return my deposit. What should I do next?",
        settings=SETTINGS,
    )

    assert state["classification"].domain == "legal"
    assert "Practical next steps:" in state["response"].content
    assert "Collect and keep copies of key documents" in state["response"].content


def test_router_flow_adds_medical_critic_warning_when_llm_skips_doctor_guidance(monkeypatch) -> None:
    monkeypatch.setattr(medical_agent, "call_llm", lambda **kwargs: "Fever and headache can happen for many reasons.")

    state = run_router(
        "I have fever and severe headache for two days. Should I see a doctor urgently?",
        settings=SETTINGS,
    )

    assert state["classification"].domain == "medical"
    assert any("consulting a doctor" in note.lower() for note in state["response"].safety_notes)


def test_router_flow_unknown_queries_ask_for_clarification(monkeypatch) -> None:
    monkeypatch.setattr(
        general_agent,
        "call_llm",
        lambda **kwargs: "I need a bit more detail before I can guide you.",
    )

    state = run_router("I need help with my issue.", settings=SETTINGS)

    assert state["classification"].domain == "unknown"
    assert "To guide you better, please clarify:" in state["response"].content
