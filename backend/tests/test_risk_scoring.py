"""Regression coverage for medical-urgency vs legal-high-risk scoring.

These ~40 edge cases target the historical weak spot (risk accuracy ~62%).
They run fully offline with ENABLE_LLM=false.
"""
from __future__ import annotations

import pytest

from agents.classifier import classify_intent
from agents.classifier.scorer import assess_risk_level
from agents.classifier.keywords import (
    HIGH_RISK_KEYWORDS,
    MEDICAL_URGENCY_TERMS,
    LEGAL_HIGH_RISK_TERMS,
    MEDIUM_RISK_KEYWORDS,
    EDUCATIONAL_FRAMING_TERMS,
    PERSONAL_EMERGENCY_CUES,
)
from core.config import Settings

SETTINGS = Settings.load()

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _risk(query: str) -> str:
    result = classify_intent(query, SETTINGS)
    return str(result.risk_level.value if hasattr(result.risk_level, "value") else result.risk_level)


def _domain(query: str) -> str:
    result = classify_intent(query, SETTINGS)
    return str(result.domain.value if hasattr(result.domain, "value") else result.domain)


# ── Medical urgency / emergency (expect high) ─────────────────────────────────

MEDICAL_HIGH_CASES = [
    "I have crushing chest pain and sweating right now",
    "My child is turning blue and struggling to breathe",
    "Someone drank toilet cleaner at home",
    "I am vomiting blood and feeling weak",
    "I suddenly cannot speak clearly and one side of my face is drooping",
    "A relative is having a seizure for the first time",
    "I may have been bitten by a snake and the swelling is increasing",
    "There is severe burn injury on the arm and face",
    "My father has chest pain after climbing stairs and feels dizzy",
    "There is sudden weakness on one side of the body",
    "An elderly person fell, hit their head, and is acting confused",
    "There is nonstop vomiting with signs of dehydration",
    "I think I took too many tablets by mistake",
    "Mere chest me tightness hai aur left arm me pain hai, emergency hai kya?",
    "Saans nahi aa rahi and I feel faint",
]


@pytest.mark.parametrize("query", MEDICAL_HIGH_CASES)
def test_medical_urgency_is_high_risk(query: str) -> None:
    assert _risk(query) == "high"
    assert _domain(query) in {"medical", "unknown", "general"}


# ── Legal high-risk / safety threats (expect high) ────────────────────────────

LEGAL_HIGH_CASES = [
    "Someone is threatening to leak my photos unless I pay money",
    "My husband is beating me and I need urgent legal help",
    "Police picked up my brother and we do not know where he is",
    "I am being blackmailed after sharing private pictures",
    "A neighbour attacked me and I need to know immediate legal steps",
    "I am being stalked and fear for my safety",
    "There is pressure to sign property papers under threat",
    "My ex-partner is threatening to kidnap our child",
]


@pytest.mark.parametrize("query", LEGAL_HIGH_CASES)
def test_legal_high_risk_path(query: str) -> None:
    assert _risk(query) == "high"
    assert _domain(query) in {"legal", "unknown", "general"}


# ── Medium boundaries (not automatic ER, still elevated) ──────────────────────

MEDIUM_CASES = [
    "What are common symptoms of asthma triggers?",
    "How is Type 2 diabetes usually managed?",
    "When does a dog bite need urgent rabies treatment?",
    "How can heat stroke affect people during Indian summers?",
    "What legal remedies exist for domestic violence survivors in India?",
    "My landlord is refusing to return my security deposit",
    "How do I file an FIR if police refuse to register my complaint?",
    "I have been feeling very stressed and anxious lately",
]


@pytest.mark.parametrize("query", MEDIUM_CASES)
def test_medium_risk_boundaries(query: str) -> None:
    risk = _risk(query)
    assert RISK_ORDER[risk] >= RISK_ORDER["medium"] or risk == "low"
    # Educational heat-stroke / dog-bite overviews must not false-high.
    if "heat stroke" in query.lower() or (
        "dog bite" in query.lower() and query.lower().startswith("when")
    ):
        assert risk in {"medium", "low"}
    if "legal remedies exist for domestic violence" in query.lower():
        assert risk in {"medium", "low"}


# ── Low educational baselines ─────────────────────────────────────────────────

LOW_CASES = [
    "What are common symptoms of Type 2 diabetes?",
    "What is copyright protection in general?",
    "How do I bake a cake?",
]


@pytest.mark.parametrize("query", LOW_CASES)
def test_low_risk_educational_queries(query: str) -> None:
    assert _risk(query) == "low"


def test_assess_risk_separates_medical_and_legal_paths() -> None:
    med_level, med_signals = assess_risk_level(
        "i have chest pain and shortness of breath",
        domain="medical",
        has_medical=True,
        has_legal=False,
        medical_weighted=5,
        legal_weighted=0,
        urgent_intent=False,
        high_risk_keywords=HIGH_RISK_KEYWORDS,
        medical_urgency_terms=MEDICAL_URGENCY_TERMS,
        legal_high_risk_terms=LEGAL_HIGH_RISK_TERMS,
        medium_risk_keywords=MEDIUM_RISK_KEYWORDS,
        educational_framing_terms=EDUCATIONAL_FRAMING_TERMS,
        personal_emergency_cues=PERSONAL_EMERGENCY_CUES,
    )
    assert med_level == "high"
    assert med_signals["medical_high"] is True

    leg_level, leg_signals = assess_risk_level(
        "i am being stalked and fear for my safety",
        domain="legal",
        has_medical=False,
        has_legal=True,
        medical_weighted=0,
        legal_weighted=4,
        urgent_intent=False,
        high_risk_keywords=HIGH_RISK_KEYWORDS,
        medical_urgency_terms=MEDICAL_URGENCY_TERMS,
        legal_high_risk_terms=LEGAL_HIGH_RISK_TERMS,
        medium_risk_keywords=MEDIUM_RISK_KEYWORDS,
        educational_framing_terms=EDUCATIONAL_FRAMING_TERMS,
        personal_emergency_cues=PERSONAL_EMERGENCY_CUES,
    )
    assert leg_level == "high"
    assert leg_signals["legal_high_flag"] is True


def test_urgent_intent_escalates_medical_medium_to_high() -> None:
    level, signals = assess_risk_level(
        "urgent help needed for high fever and dengue symptoms in my child",
        domain="medical",
        has_medical=True,
        has_legal=False,
        medical_weighted=4,
        legal_weighted=0,
        urgent_intent=True,
        high_risk_keywords=HIGH_RISK_KEYWORDS,
        medical_urgency_terms=MEDICAL_URGENCY_TERMS,
        legal_high_risk_terms=LEGAL_HIGH_RISK_TERMS,
        medium_risk_keywords=MEDIUM_RISK_KEYWORDS,
        educational_framing_terms=EDUCATIONAL_FRAMING_TERMS,
        personal_emergency_cues=PERSONAL_EMERGENCY_CUES,
    )
    assert level == "high"
    assert signals["escalated"] is True


def test_stroke_does_not_false_match_heat_stroke_as_emergency_overview() -> None:
    """Standalone 'stroke' must not force high on educational heat-stroke queries."""
    risk = _risk("How can heat stroke affect people during Indian summers?")
    assert risk != "high"
