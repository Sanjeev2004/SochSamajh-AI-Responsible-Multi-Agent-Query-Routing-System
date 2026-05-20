from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from langsmith import traceable

from core.state import AgentResponse, ClassificationOutput


# -------------------- CRITIC CONSTANTS --------------------

class CriticSeverity(str, Enum):
    WARNING = "WARNING"
    ERROR   = "ERROR"    # must be fixed before returning to user
    INFO    = "INFO"


@dataclass
class CriticNote:
    severity: CriticSeverity
    code: str          # machine-readable tag, e.g. "MISSING_DOCTOR_REFERRAL"
    message: str
    domain: str


# Phrases that indicate over-confident medical advice — dangerous for users
MEDICAL_OVERCONFIDENCE_PHRASES = frozenset([
    "you definitely have",
    "you certainly have",
    "this is definitely",
    "100% sure",
    "guaranteed to work",
    "take this medicine",
    "take these pills",
    "take this drug",
    "you don't need a doctor",
    "no need to see a doctor",
    "you will be fine without",
    "stop taking your medication",
    "replace your medication",
])

# Phrases that indicate over-confident legal advice — creates false legal expectations
LEGAL_OVERCONFIDENCE_PHRASES = frozenset([
    "you will definitely win",
    "you are guaranteed to win",
    "100% sure you will win",
    "no need for a lawyer",
    "you don't need an attorney",
    "this is definitely illegal",
    "you will get full compensation",
    "guaranteed compensation",
    "you cannot lose this case",
])

# Response must contain one of these if domain=medical
MEDICAL_DISCLAIMER_PHRASES = (
    "consult",
    "doctor",
    "medical professional",
    "healthcare professional",
    "seek medical advice",
    "see a physician",
)

# Response must contain one of these if domain=legal
LEGAL_DISCLAIMER_PHRASES = (
    "attorney",
    "lawyer",
    "legal counsel",
    "consult a legal",
    "seek legal advice",
    "qualified legal",
)

# Response to a self-harm query must contain crisis resources
CRISIS_RESOURCE_PHRASES = (
    "iCall",
    "vandrevala",
    "1800-599-0019",
    "1-800-273",
    "crisis",
    "helpline",
    "professional help",
    "reach out",
    "you are not alone",
    "mental health professional",
)

# Response to an illegal request must NOT answer the question — must be a refusal
REFUSAL_PHRASES = (
    "i cannot",
    "i can't",
    "i'm unable",
    "i am unable",
    "this is not something i can",
    "cannot assist",
    "not able to help with",
    "unable to provide",
    "this request",
    "this is illegal",
    "against the law",
    "i won't",
    "i will not",
)

# Phrases that signal a vague non-answer — bad UX
VAGUE_RESPONSE_INDICATORS = (
    "i don't know",
    "i am not sure",
    "i cannot say",
    "it depends",
    "maybe",
    "perhaps",
    "could be anything",
    "hard to say",
)

MIN_RESPONSE_LENGTH = 40  # characters — below this is almost certainly an error


# -------------------- HELPER --------------------

def _contains_any_phrase(text: str, phrases: tuple[str, ...] | frozenset[str]) -> bool:
    text_lower = text.lower()
    return any(phrase.lower() in text_lower for phrase in phrases)


def _contains_phrase_in_notes(notes: list[str], phrases: tuple[str, ...]) -> bool:
    combined = " ".join(notes).lower()
    return any(phrase.lower() in combined for phrase in phrases)


def _add_note(
    notes: list[CriticNote],
    severity: CriticSeverity,
    code: str,
    message: str,
    domain: str,
) -> None:
    notes.append(CriticNote(severity=severity, code=code, message=message, domain=domain))


# -------------------- CRITIC CHECKS --------------------

def _check_response_length(
    content: str, notes: list[CriticNote], domain: str
) -> None:
    if len(content.strip()) < MIN_RESPONSE_LENGTH:
        _add_note(
            notes,
            CriticSeverity.ERROR,
            "EMPTY_OR_TOO_SHORT",
            f"Response is too short ({len(content.strip())} chars). "
            "Likely an incomplete or failed generation.",
            domain,
        )


def _check_self_harm_response(
    content: str, classification: ClassificationOutput, notes: list[CriticNote]
) -> None:
    if not classification.self_harm:
        return
    has_crisis_resource = _contains_any_phrase(content, CRISIS_RESOURCE_PHRASES)
    has_in_notes = _contains_phrase_in_notes(
        [n.message for n in notes], CRISIS_RESOURCE_PHRASES
    )
    if not has_crisis_resource and not has_in_notes:
        _add_note(
            notes,
            CriticSeverity.ERROR,
            "MISSING_CRISIS_RESOURCE",
            "Self-harm query detected but response does not include "
            "crisis helpline or professional support resources. "
            "Add iCall (9152987821) or Vandrevala Foundation (1860-2662-345).",
            "general",
        )


def _check_illegal_request_response(
    content: str, classification: ClassificationOutput, notes: list[CriticNote]
) -> None:
    if not classification.illegal_request:
        return
    is_refusal = _contains_any_phrase(content, REFUSAL_PHRASES)
    if not is_refusal:
        _add_note(
            notes,
            CriticSeverity.ERROR,
            "MISSING_REFUSAL",
            "Illegal request detected but response does not contain a clear refusal. "
            "The response may be answering an unsafe question.",
            "legal",
        )


def _check_medical_disclaimer(
    content: str,
    classification: ClassificationOutput,
    existing_notes: list[str],
    notes: list[CriticNote],
) -> None:
    if classification.domain != "medical":
        return

    has_disclaimer = _contains_any_phrase(content, MEDICAL_DISCLAIMER_PHRASES)
    has_in_existing = _contains_phrase_in_notes(existing_notes, MEDICAL_DISCLAIMER_PHRASES)

    if not has_disclaimer and not has_in_existing:
        _add_note(
            notes,
            CriticSeverity.WARNING,
            "MISSING_DOCTOR_REFERRAL",
            "Medical domain response does not advise consulting a doctor or healthcare professional.",
            "medical",
        )

    # Check for overconfident medical claims
    has_overconfidence = _contains_any_phrase(content, MEDICAL_OVERCONFIDENCE_PHRASES)
    if has_overconfidence:
        _add_note(
            notes,
            CriticSeverity.ERROR,
            "MEDICAL_OVERCONFIDENCE",
            "Response contains overconfident medical claims "
            "(e.g., definitive diagnosis or 'no need for a doctor'). "
            "This is unsafe and must be corrected.",
            "medical",
        )


def _check_legal_disclaimer(
    content: str,
    classification: ClassificationOutput,
    existing_notes: list[str],
    notes: list[CriticNote],
) -> None:
    if classification.domain != "legal":
        return

    # Require attorney referral for high OR medium risk
    if classification.risk_level in ("high", "medium"):
        has_disclaimer = _contains_any_phrase(content, LEGAL_DISCLAIMER_PHRASES)
        has_in_existing = _contains_phrase_in_notes(existing_notes, LEGAL_DISCLAIMER_PHRASES)

        if not has_disclaimer and not has_in_existing:
            severity = (
                CriticSeverity.ERROR
                if classification.risk_level == "high"
                else CriticSeverity.WARNING
            )
            _add_note(
                notes,
                severity,
                "MISSING_ATTORNEY_REFERRAL",
                f"{classification.risk_level.capitalize()}-risk legal query response "
                "missing attorney or legal counsel referral.",
                "legal",
            )

    # Check for overconfident legal claims
    has_overconfidence = _contains_any_phrase(content, LEGAL_OVERCONFIDENCE_PHRASES)
    if has_overconfidence:
        _add_note(
            notes,
            CriticSeverity.ERROR,
            "LEGAL_OVERCONFIDENCE",
            "Response contains overconfident legal claims "
            "(e.g., 'you will definitely win' or 'no need for a lawyer'). "
            "This is irresponsible legal guidance.",
            "legal",
        )


def _check_vague_response(
    content: str,
    classification: ClassificationOutput,
    notes: list[CriticNote],
) -> None:
    """Flag responses that are non-committal and provide no real value."""
    if classification.domain in ("medical", "legal") and classification.risk_level == "high":
        vague_count = sum(
            1 for phrase in VAGUE_RESPONSE_INDICATORS
            if phrase in content.lower()
        )
        if vague_count >= 2:
            _add_note(
                notes,
                CriticSeverity.WARNING,
                "VAGUE_HIGH_RISK_RESPONSE",
                f"High-risk {classification.domain} query received a vague response "
                f"with {vague_count} non-committal phrases. "
                "User may need clearer actionable guidance.",
                classification.domain,
            )


def _check_unknown_domain(
    content: str,
    classification: ClassificationOutput,
    notes: list[CriticNote],
) -> None:
    """If domain=unknown, response should ask for clarification, not guess an answer."""
    if classification.domain != "unknown":
        return
    clarification_phrases = (
        "clarify",
        "could you tell me more",
        "can you provide more details",
        "what specifically",
        "more information",
        "could you elaborate",
        "which aspect",
    )
    if not _contains_any_phrase(content, clarification_phrases):
        _add_note(
            notes,
            CriticSeverity.WARNING,
            "MISSING_CLARIFICATION_REQUEST",
            "Domain classified as 'unknown' but response does not ask the user "
            "to clarify their need. Should prompt for more detail.",
            "unknown",
        )


# -------------------- MAIN CRITIC --------------------

@traceable(name="safety_critic")
def run_critic(
    response: AgentResponse,
    classification: ClassificationOutput,
    query: str,
) -> AgentResponse:
    """
    Run all safety critic checks on an agent response.

    Each check appends a structured CriticNote. After all checks,
    the string representations are also appended to response.safety_notes
    for backward compatibility with downstream consumers that read plain strings.
    """
    structured_notes: list[CriticNote] = []
    existing_string_notes: list[str] = list(response.safety_notes)
    content = response.content

    _check_response_length(content, structured_notes, classification.domain)
    _check_self_harm_response(content, classification, structured_notes)
    _check_illegal_request_response(content, classification, structured_notes)
    _check_medical_disclaimer(content, classification, existing_string_notes, structured_notes)
    _check_legal_disclaimer(content, classification, existing_string_notes, structured_notes)
    _check_vague_response(content, classification, structured_notes)
    _check_unknown_domain(content, classification, structured_notes)

    # Append structured notes as readable strings to response.safety_notes
    for note in structured_notes:
        formatted = f"[{note.severity.value}:{note.code}] {note.message}"
        response.safety_notes.append(formatted)

    # Flag if any ERROR-level note exists — caller can decide to block/retry
    has_errors = any(n.severity == CriticSeverity.ERROR for n in structured_notes)
    if has_errors:
        error_codes = [n.code for n in structured_notes if n.severity == CriticSeverity.ERROR]
        response.safety_notes.append(
            f"[CRITIC:BLOCK_RECOMMENDED] ERROR-level issues found: {error_codes}. "
            "Consider blocking this response or triggering a retry."
        )

    return response
