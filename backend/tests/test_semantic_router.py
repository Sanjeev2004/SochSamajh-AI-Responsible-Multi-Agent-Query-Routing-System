"""Offline-friendly semantic router tests (model is mocked)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from agents.classifier import classify_intent
from agents.router_semantic import SemanticRouter, get_semantic_router
from core.config import Settings

SETTINGS = Settings.load()


def test_semantic_router_is_lazy_and_safe_without_model() -> None:
    # Reset singleton state for isolation
    SemanticRouter._instance = None
    router = get_semantic_router()
    assert router.model is None
    assert router._load_attempted is False
    # predict should attempt load then return None if unavailable
    with patch.object(SemanticRouter, "_ensure_model", return_value=False):
        assert router.predict("dengue symptoms bukhar") is None


def test_predict_with_scores_returns_best_domain() -> None:
    SemanticRouter._instance = None
    router = get_semantic_router()
    fake_scores = {"medical": 0.71, "legal": 0.22, "general": 0.18}

    with patch.object(SemanticRouter, "_score_domains", return_value=fake_scores):
        result = router.predict_with_scores("mujhe dengue aur bukhar hai")

    assert result is not None
    best, score, scores = result
    assert best == "medical"
    assert score == 0.71
    assert scores["legal"] == 0.22


def test_classifier_uses_semantic_router_for_ambiguous_query() -> None:
    fake = MagicMock()
    fake.predict_with_scores.return_value = (
        "legal",
        0.66,
        {"legal": 0.66, "medical": 0.20, "general": 0.15},
    )

    with patch("agents.router_semantic.get_semantic_router", return_value=fake):
        # Force the cascade path via a vague/unknown-leaning query with a legal hint
        result = classify_intent(
            "not sure where to start with FIR police complaint and doctor or lawyer",
            SETTINGS,
        )

    fake.predict_with_scores.assert_called()
    assert str(result.domain.value if hasattr(result.domain, "value") else result.domain) in {
        "legal",
        "unknown",
        "medical",
    }


def test_classifier_survives_semantic_router_failure() -> None:
    with patch(
        "agents.router_semantic.get_semantic_router",
        side_effect=RuntimeError("boom"),
    ):
        # Vague / mid-confidence path triggers the semantic cascade.
        result = classify_intent("I need urgent guidance, not sure where to start", SETTINGS)

    assert result.domain in {"unknown", "general", "medical", "legal"}
    assert result.risk_level in {"low", "medium", "high"}
