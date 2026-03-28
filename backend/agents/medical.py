from __future__ import annotations

from langsmith import traceable

from core.config import Settings, logger
from core.state import AgentResponse, ClassificationOutput
from agents.base import call_llm
from services.retrieval_service import get_retrieved_context

MEDICAL_DISCLAIMER = "This is general educational information and not medical advice. Please consult a qualified healthcare professional."


@traceable(name="medical_agent")
def run_medical_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    try:
        # 1. Retrieve Context
        context = get_retrieved_context(query=query, domain="medical", settings=settings)
        urgency_instruction = ""
        if classification.risk_level == "high":
            urgency_instruction = (
                "Start with immediate triage guidance in 2-3 bullets and clearly advise emergency care if red flags are present. "
            )
        elif classification.risk_level == "medium":
            urgency_instruction = (
                "Include warning signs that should prompt urgent in-person medical evaluation. "
            )

        # 2. Augment Prompt
        system_prompt = (
            "You are a medical information assistant. Provide educational, high-level information only. "
            "Do NOT diagnose, prescribe, or provide dosages. Encourage professional medical help when appropriate. "
            "Use the provided context to answer if relevant. If the context is not relevant, ignore it. "
            f"{urgency_instruction}"
            f"\n\nContext:\n{context}\n\n"
            "Keep response short, readable, and plain text. Use simple bullet points when needed. "
            "Prefer this structure when possible: likely explanation, immediate safe actions, and when to seek care. "
            "For urgent-sounding symptoms, mention warning signs that should prompt emergency or same-day in-person care. "
            "Do not use markdown tables, heading markers, or pipe-separated formatting."
        )

        content = call_llm(
            query=query,
            system_prompt=system_prompt,
            settings=settings,
            temperature=0.2
        )

        return AgentResponse(
            content=content,
            disclaimers=[MEDICAL_DISCLAIMER],
            safety_notes=[],
        )
    except Exception as exc:
        logger.exception("Medical agent fell back to static response: %s", exc)
        fallback = (
            "I can provide general educational information about medical topics. For specific health concerns, "
            "including symptoms, diagnosis, or treatment, please consult with a qualified healthcare professional "
            "who can evaluate your individual situation. Every person's health needs are unique and require "
            "personalized medical assessment."
        )
        return AgentResponse(
            content=fallback,
            disclaimers=[MEDICAL_DISCLAIMER],
            safety_notes=[],
        )
