from __future__ import annotations

from langsmith import traceable

from core.state import AgentResponse, ClassificationOutput

@traceable(name="safety_critic")
def run_critic(response: AgentResponse, classification: ClassificationOutput, query: str) -> AgentResponse:
    content_lower = response.content.lower()

    if classification.domain == "medical":
        has_advice_warning = (
            "consult" in content_lower
            or "doctor" in content_lower
            or "medical professional" in content_lower
            or "healthcare professional" in content_lower
        )
        has_existing_warning = any(
            "doctor" in note.lower() or "medical" in note.lower() or "healthcare professional" in note.lower()
            for note in response.safety_notes
        )
        if not has_advice_warning and not has_existing_warning:
            response.safety_notes.append("CRITIC WARNING: Response did not explicitly advise consulting a doctor.")

    if classification.domain == "legal" and classification.risk_level == "high":
        has_legal_warning = "attorney" in content_lower or "lawyer" in content_lower or "counsel" in content_lower
        has_existing_warning = any("attorney" in note.lower() or "lawyer" in note.lower() or "counsel" in note.lower() for note in response.safety_notes)
        if not has_legal_warning and not has_existing_warning:
            response.safety_notes.append("CRITIC WARNING: High-risk legal query response missing attorney referral.")

    return response
