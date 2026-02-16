from __future__ import annotations

from langsmith import traceable

from core.state import AgentResponse, ClassificationOutput

CRISIS_RESOURCES = (
    "If you are in immediate danger or thinking about self-harm, please seek help now: "
    "Call or text 988 (U.S. Suicide & Crisis Lifeline) or text HOME to 741741 (Crisis Text Line)."
)


@traceable(name="safety_agent")
def run_safety_agent(query: str, classification: ClassificationOutput) -> AgentResponse:
    if classification.self_harm:
        content = (
            "I'm really sorry you're feeling this way. I can't help with anything that could hurt you. "
            "You deserve support, and you don't have to go through this alone. "
            "If you feel at risk, please reach out to a trusted person or professional right now."
        )
        safety_notes = [CRISIS_RESOURCES]
    elif classification.illegal_request:
        content = (
            "I can't help with illegal activities. If you're facing a legal issue, "
            "I can share general information about legal topics or help you find lawful alternatives."
        )
        safety_notes = []
    else:
        content = "I can't assist with that request."
        safety_notes = []

    return AgentResponse(content=content, disclaimers=[], safety_notes=safety_notes)
