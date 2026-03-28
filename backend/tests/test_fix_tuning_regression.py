from __future__ import annotations

import pytest

from agents.classifier import classify_intent
from agents.formatter import run_formatter
from core.config import Settings
from core.state import AgentResponse, ClassificationOutput


SETTINGS = Settings.load()

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


@pytest.mark.parametrize(
    ("query", "expected_domain", "minimum_risk"),
    [
        ("Chest pain with left arm pain and sweating since 20 minutes, emergency?", "medical", "high"),
        ("My child has high fever and is very weak since morning, what to do now?", "medical", "medium"),
        ("I drank floor cleaner and now vomiting, what should I do immediately?", "medical", "high"),
        ("Dog bite hua hai and vaccine status unknown, urgent treatment chahiye.", "medical", "high"),
        ("Pregnancy me bleeding ho rahi hai, kya emergency room jana chahiye?", "medical", "high"),
        ("Sudden breathing difficulty with asthma, urgent help please.", "medical", "high"),
        ("Face drooping and speech slurred since 10 minutes, should I go to emergency room?", "medical", "high"),
        ("Fever with vomiting and I cannot keep water down, urgent care needed?", "medical", "high"),
        ("Chest tightness and shortness of breath after climbing stairs, is this serious?", "medical", "high"),
        ("Landlord security deposit wapas nahi de raha, next legal step kya hai?", "legal", "medium"),
        ("Employer 2 months salary nahi de raha, complaint file ka process kya hai?", "legal", "medium"),
        ("FIR register na ho to next legal step kya hota hai?", "legal", "medium"),
        ("Wrongful termination ke against rights and notice process kya hota hai?", "legal", "medium"),
        ("Medical negligence complaint consumer court me kaise file karte hain?", "legal", "medium"),
        ("Domestic violence situation me immediate legal protection kaise milti hai?", "legal", "high"),
        ("Police picked up my brother, immediate legal help kya kare?", "legal", "high"),
        ("Hospital bill fraud lag raha hai, legal complaint kaise karu?", "legal", "medium"),
        ("Doctor ne galat treatment diya, compensation mil sakta hai?", "legal", "medium"),
        ("Tenant agreement me unfair deposit clause ho to legal notice bhej sakte hain?", "legal", "medium"),
        ("Salary nahi mili and step by step complaint process kya hota hai?", "legal", "medium"),
        ("Consumer court me documents needed kya hote hain for medical negligence complaint?", "legal", "medium"),
        ("Land dispute ke liye where to file complaint and what papers should I collect?", "legal", "medium"),
        ("I need urgent guidance.", "unknown", "low"),
        ("Please help, what should be my next step?", "unknown", "low"),
        ("Mujhe samajh nahi aa raha kya karun.", "unknown", "low"),
        ("Issue serious hai, guide karo asap.", "unknown", "medium"),
        ("Can you explain my situation?", "unknown", "low"),
        ("Need advice", "unknown", "low"),
        ("Can stress cause chest tightness or is it emergency?", "medical", "high"),
        ("I need legal and medical help both, not sure where to start.", "unknown", "low"),
        ("I am not sure if this is medical or legal, can you guide me?", "unknown", "low"),
        ("Need both legal and medical help after an accident, where do I start?", "unknown", "low"),
        ("Confused whether I need a doctor or lawyer first.", "unknown", "low"),
    ],
)
def test_fix_tuning_prompt_regression(query: str, expected_domain: str, minimum_risk: str) -> None:
    result = classify_intent(query, SETTINGS)
    assert result.domain == expected_domain
    assert RISK_ORDER[result.risk_level] >= RISK_ORDER[minimum_risk]


def test_formatter_adds_medical_immediate_steps_for_high_risk() -> None:
    response = AgentResponse(content="You may have a serious issue.")
    classification = ClassificationOutput(
        domain="medical",
        risk_level="high",
        needs_disclaimer=True,
        self_harm=False,
        illegal_request=False,
        reasoning="test",
    )

    formatted = run_formatter(response, classification, "chest pain and shortness of breath emergency")
    assert "Immediate steps:" in formatted.content


def test_formatter_adds_medical_warning_signs_for_medium_risk() -> None:
    response = AgentResponse(content="This may need closer attention.")
    classification = ClassificationOutput(
        domain="medical",
        risk_level="medium",
        needs_disclaimer=True,
        self_harm=False,
        illegal_request=False,
        reasoning="test",
    )

    formatted = run_formatter(response, classification, "Fever and vomiting for two days, should I see a doctor?")
    assert "Seek urgent care if:" in formatted.content


def test_formatter_adds_legal_practical_steps() -> None:
    response = AgentResponse(content="You may consider legal options.")
    classification = ClassificationOutput(
        domain="legal",
        risk_level="medium",
        needs_disclaimer=True,
        self_harm=False,
        illegal_request=False,
        reasoning="test",
    )

    formatted = run_formatter(response, classification, "What is my next legal step for salary non-payment?")
    assert "Practical next steps:" in formatted.content


def test_formatter_adds_unknown_clarification_questions() -> None:
    response = AgentResponse(content="I can help once I know more.")
    classification = ClassificationOutput(
        domain="unknown",
        risk_level="low",
        needs_disclaimer=False,
        self_harm=False,
        illegal_request=False,
        reasoning="test",
    )

    formatted = run_formatter(response, classification, "I need urgent guidance")
    assert "To guide you better, please clarify:" in formatted.content
    assert "immediate danger" in formatted.content.lower()
