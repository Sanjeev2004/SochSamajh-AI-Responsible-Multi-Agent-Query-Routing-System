from __future__ import annotations

from langsmith import traceable

from core.config import Settings
from core.state import AgentResponse, ClassificationOutput
from agents.base import call_llm


@traceable(name="general_agent")
def run_general_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    try:
        system_prompt = (
            "You are a helpful general assistant. Answer clearly and safely in plain text. "
            "Keep response compact and readable. Use simple bullet points when needed. "
            "Do not use markdown tables, heading markers, or pipe-separated formatting. "
            "If user asks for medical or legal advice, keep it general and encourage professional help."
        )

        content = call_llm(
            query=query,
            system_prompt=system_prompt,
            settings=settings,
            temperature=0.3
        )

        return AgentResponse(content=content, disclaimers=[], safety_notes=[])
    except Exception:
        fallback = (
            "I'm here to help with general information and questions. Could you provide more details about "
            "what you'd like to know? I can assist with various topics including cooking, technology, "
            "general knowledge, and more. (Error: Unable to connect to AI)"
        )
        return AgentResponse(content=fallback, disclaimers=[], safety_notes=[])
