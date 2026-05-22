"""
classifier/scorer.py
Pure text-matching and scoring utilities.
No external dependencies — fully unit-testable in isolation.
"""
from __future__ import annotations

import math
import re
from typing import Iterable

from .keywords import NEGATION_PREFIXES, TYPO_CORRECTIONS, VAGUE_QUERY_TERMS



def correct_typos(text: str) -> str:
    """Lightweight token-level typo correction to improve keyword recall."""
    words = text.split()
    corrected = [TYPO_CORRECTIONS.get(w.lower(), w) for w in words]
    return " ".join(corrected)


def phrase_in_text(text: str, phrase: str) -> bool:
    """Return True if `phrase` appears as a whole word/phrase in `text`."""
    escaped = re.escape(phrase.lower()).replace(r"\ ", r"\s+")
    pattern = rf"(?<!\w){escaped}(?!\w)"
    return re.search(pattern, text) is not None


def is_negated(text_lower: str, phrase: str) -> bool:
    """Return True if `phrase` appears immediately after a negation word."""
    idx = text_lower.find(phrase)
    if idx == -1:
        return False
    window = text_lower[max(0, idx - 20): idx]
    return any(neg in window for neg in NEGATION_PREFIXES)


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    """Return True if any phrase from the collection is found in `text`."""
    text_lower = text.lower()
    return any(phrase_in_text(text_lower, phrase) for phrase in phrases)


def score_matches(text: str, phrases: Iterable[str]) -> int:
    """Count how many phrases are found (excluding negated occurrences)."""
    text_lower = text.lower()
    return sum(
        1
        for phrase in phrases
        if phrase_in_text(text_lower, phrase) and not is_negated(text_lower, phrase)
    )


def weighted_score(text: str, weighted_phrases: dict[str, int]) -> int:
    """Sum the weights of all non-negated matching phrases."""
    text_lower = text.lower()
    total = 0
    for phrase, weight in weighted_phrases.items():
        if phrase_in_text(text_lower, phrase) and not is_negated(text_lower, phrase):
            total += weight
    return total


def matched_terms(text: str, phrases: Iterable[str], limit: int = 8) -> list[str]:
    """Return up to `limit` matched phrases sorted by length (longest first)."""
    text_lower = text.lower()
    matches = [p for p in phrases if phrase_in_text(text_lower, p)]
    return sorted(matches, key=lambda p: (-len(p), p))[:limit]


def is_vague_query(text: str) -> bool:
    """Return True for short, generic queries with no clear domain signal."""
    text_lower = text.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s]", "", text_lower)

    if text_lower in VAGUE_QUERY_TERMS or normalized in VAGUE_QUERY_TERMS:
        return True

    generic_terms = (
        "help", "problem", "issue", "guidance",
        "situation", "advice", "kya karun", "guide",
    )
    word_count = len(normalized.split())

    if word_count <= 6 and any(t in normalized for t in generic_terms):
        return True
    if word_count <= 12 and any(
        t in normalized for t in ("next step", "urgent guidance", "figure this out")
    ):
        return True

    return False


def sigmoid_confidence(score_gap: float, base: float = 0.6) -> float:
    """Map score gap [0, ∞) → confidence [base, 0.95] using a smooth curve.

    Smaller gaps → confidence stays near `base`.
    Larger gaps  → confidence approaches 0.95 asymptotically.
    """
    return base + (0.95 - base) * (1 - math.exp(-score_gap * 0.4))
