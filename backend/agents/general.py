from __future__ import annotations

from langsmith import traceable

from core.config import Settings
from core.state import AgentResponse, ClassificationOutput
from agents.base import call_llm


@traceable(name="general_agent")
def run_general_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    try:
        ambiguity_instruction = ""
        if classification.domain == "unknown":
            ambiguity_instruction = (
                "The query is ambiguous. Ask 2-3 concise clarification questions to identify whether the issue is medical, legal, or general. "
                "Do not guess the domain too early. Help the user narrow it down with practical clarifying questions. "
            )
        system_prompt = (
            "You are a helpful general assistant. Answer clearly and safely in plain text. "
            "Keep response compact and readable. Use simple bullet points when needed. "
            "Do not use markdown tables, heading markers, or pipe-separated formatting. "
            f"{ambiguity_instruction}"
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
            "I can help, but I need a bit more detail first.\n\n"
            "To guide you better, please clarify:\n"
            "- Is this mainly a medical issue, a legal issue, or something else?\n"
            "- What happened, when did it start, and who is involved?\n"
            "- What outcome do you want in the next 24-48 hours?"
        )
        return AgentResponse(content=fallback, disclaimers=[], safety_notes=[])
