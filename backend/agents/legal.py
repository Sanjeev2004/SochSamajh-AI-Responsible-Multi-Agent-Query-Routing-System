from __future__ import annotations

from langsmith import traceable

from core.config import Settings, logger
from core.state import AgentResponse, ClassificationOutput
from agents.base import call_llm
from services.retrieval_service import get_retrieval_result

LEGAL_DISCLAIMER = (
    "This is general legal information, not legal advice. Laws vary by jurisdiction; consult a licensed attorney."
)


@traceable(name="legal_agent")
def run_legal_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    try:
        # 1. Retrieve Context
        retrieval = get_retrieval_result(query=query, domain="legal", settings=settings)
        context = retrieval.context
        urgency_instruction = ""
        if classification.risk_level == "high":
            urgency_instruction = (
                "If user may be in immediate danger, start with an 'Immediate safety' section before legal process details. "
            )

        # 2. Augment Prompt with retrieved context
        system_prompt = (
            "You are a legal information assistant. Provide general, high-level information only. "
            "Do NOT provide definitive legal advice. Note that laws vary by jurisdiction. "
            "Use the provided context to answer if relevant. If the context is not relevant, ignore it. "
            f"{urgency_instruction}"
            f"\n\nContext:\n{context}\n\n"
            "Keep response short, readable, and plain text. Use simple bullet points when needed. "
            "Give practical, lawful next steps when possible: what to do now, what records to collect, where to file, and who to contact. "
            "If the user asks for process, complaint, notice, rights, or documents, answer with concrete next-step bullets. "
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
            disclaimers=[LEGAL_DISCLAIMER],
            safety_notes=[],
            sources=retrieval.sources,
        )
    except Exception as exc:
        logger.exception("Legal agent fell back to static response: %s", exc)
        fallback = (
            "I can provide general legal information and concepts. However, laws vary significantly by jurisdiction "
            "and your specific circumstances matter. For advice applicable to your situation, please consult with "
            "a licensed attorney in your area who can review the specific details of your case and provide guidance "
            "based on applicable local laws."
        )
        return AgentResponse(
            content=fallback,
            disclaimers=[LEGAL_DISCLAIMER],
            safety_notes=[],
        )
