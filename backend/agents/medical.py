from __future__ import annotations

from langsmith import traceable

from core.config import Settings
from core.state import AgentResponse, ClassificationOutput
from agents.base import call_llm

MEDICAL_DISCLAIMER = "This is general educational information and not medical advice. Please consult a qualified healthcare professional."


@traceable(name="medical_agent")
def run_medical_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    try:
        system_prompt = (
            "You are a medical information assistant. Provide educational, high-level information only. "
            "Do NOT diagnose, prescribe, or provide dosages. Encourage professional medical help when appropriate. "
            "Keep response short, readable, and plain text. Use simple bullet points when needed. "
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
    except Exception:
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
