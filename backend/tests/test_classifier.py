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


def test_stress_and_anxiety_routes_to_medical() -> None:
    result = classify_intent("I have been feeling very stressed and anxious lately, what should I do?", SETTINGS)
    assert result.domain == "medical"


def test_burnout_routes_to_medical() -> None:
    result = classify_intent("How do I deal with burnout from work?", SETTINGS)
    assert result.domain == "medical"


def test_medical_legal_overlap_prefers_legal_when_malpractice_is_present() -> None:
    result = classify_intent("Can I sue a hospital for malpractice after a surgery complication?", SETTINGS)
    assert result.domain == "legal"
    assert result.risk_level in {"medium", "high"}


def test_llm_fallback_alternative_domains() -> None:
    from unittest.mock import MagicMock, patch
    from agents.classifier.llm_fallback import llm_classify
    from core.state import ClassificationOutput, Domain

    base_result = ClassificationOutput(
        domain=Domain.UNKNOWN,
        risk_level="low",
        needs_disclaimer=False,
        self_harm=False,
        illegal_request=False,
        reasoning="Heuristic unknown",
        confidence=0.35,
        triggered_terms=[],
        alternative_domains={"unknown": 1.0, "general": 0.5, "medical": 0.0, "legal": 0.0},
    )

    dummy_settings = MagicMock()
    dummy_settings.enable_llm = True
    dummy_settings.openai_api_key = "mock-key"

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "domain": "medical",
        "risk_level": "medium",
        "reasoning": "Mocked medical detection",
        "confidence": 0.85,
    }

    with patch("agents.classifier.llm_fallback._get_llm_chain", return_value=mock_chain):
        res = llm_classify("a dog bit me on the leg", dummy_settings, base_result)
        assert res.domain == "medical"
        assert res.alternative_domains["medical"] == 1.0
        assert res.alternative_domains["legal"] == 0.0
        assert res.alternative_domains["general"] == 0.0
        assert res.alternative_domains["unknown"] == 0.0

