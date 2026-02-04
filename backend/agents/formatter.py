from __future__ import annotations

from langsmith import traceable

from core.state import AgentResponse, ClassificationOutput


@traceable(name="response_formatter")
def run_formatter(response: AgentResponse, classification: ClassificationOutput) -> AgentResponse:
    disclaimers = list(response.disclaimers)
    if classification.needs_disclaimer and not disclaimers:
        if classification.domain == "medical":
            disclaimers.append("This is general educational information, not medical advice.")
        elif classification.domain == "legal":
            disclaimers.append("This is general legal information, not legal advice.")

    return AgentResponse(
        content=response.content.strip(),
        disclaimers=disclaimers,
        safety_notes=response.safety_notes,
    )
