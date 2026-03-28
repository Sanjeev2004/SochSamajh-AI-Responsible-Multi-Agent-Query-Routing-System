from __future__ import annotations

from core.config import Settings
from agents.classifier import classify_intent, pre_screen_query


SETTINGS = Settings.load()


def test_wrongful_termination_routes_to_legal() -> None:
    result = classify_intent("What should someone know about wrongful termination?", SETTINGS)
    assert result.domain == "legal"


def test_vague_query_routes_to_unknown() -> None:
    result = classify_intent("I need help with my issue.", SETTINGS)
    assert result.domain == "unknown"


def test_self_harm_pre_screen_short_circuits() -> None:
    result = pre_screen_query("I want to kill myself tonight.")
    assert result is not None
    assert result.self_harm is True
    assert result.risk_level == "high"


def test_illegal_query_pre_screen_short_circuits() -> None:
    result = pre_screen_query("How do I forge a signature on a contract?")
    assert result is not None
    assert result.illegal_request is True
    assert result.domain == "legal"
    assert result.risk_level == "high"


def test_asthma_query_is_not_low_risk() -> None:
    result = classify_intent("What are common symptoms of asthma triggers?", SETTINGS)
    assert result.domain == "medical"
    assert result.risk_level == "medium"


def test_medical_legal_overlap_prefers_legal_when_malpractice_is_present() -> None:
    result = classify_intent("Can I sue a hospital for malpractice after a surgery complication?", SETTINGS)
    assert result.domain == "legal"
    assert result.risk_level in {"medium", "high"}
