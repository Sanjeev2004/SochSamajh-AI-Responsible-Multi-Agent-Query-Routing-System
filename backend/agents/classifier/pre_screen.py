"""
classifier/pre_screen.py
Fast, deterministic safety pre-screen that runs before any LLM call.
Catches self-harm and illegal-intent queries with high precision.
"""
from __future__ import annotations

from langsmith import traceable

from core.state import ClassificationOutput
from .keywords import SELF_HARM_KEYWORDS, ILLEGAL_KEYWORDS
from .scorer import contains_any, matched_terms


@traceable(name="pre_screen")
def pre_screen_query(query: str) -> ClassificationOutput | None:
    """Scan the raw query for self-harm or illegal intent.

    Returns a ``ClassificationOutput`` if a hard safety boundary is triggered,
    or ``None`` if the query is safe to proceed through the normal pipeline.

    Important: This function intentionally operates on the *raw* query
    (no truncation, no typo correction) to avoid missing dangerous signals.
    """
    if contains_any(query, SELF_HARM_KEYWORDS):
        triggers = matched_terms(query, SELF_HARM_KEYWORDS)
        return ClassificationOutput(
            domain="general",
            risk_level="high",
            needs_disclaimer=True,
            self_harm=True,
            illegal_request=False,
            reasoning="Pre-screen detected self-harm intent.",
            confidence=0.98,
            triggered_terms=triggers,
            alternative_domains={"general": 0.98, "medical": 0.1, "legal": 0.05},
            explanation=(
                "The pre-screen matched self-harm language, so the normal router "
                "was bypassed for a safety response."
            ),
        )

    if contains_any(query, ILLEGAL_KEYWORDS):
        triggers = matched_terms(query, ILLEGAL_KEYWORDS)
        return ClassificationOutput(
            domain="legal",
            risk_level="high",
            needs_disclaimer=True,
            self_harm=False,
            illegal_request=True,
            reasoning="Pre-screen detected illegal intent.",
            confidence=0.96,
            triggered_terms=triggers,
            alternative_domains={"legal": 0.96, "general": 0.2, "medical": 0.05},
            explanation=(
                "The pre-screen matched illegal-intent language, so the system refused "
                "unsafe help and offered lawful alternatives."
            ),
        )

    return None
