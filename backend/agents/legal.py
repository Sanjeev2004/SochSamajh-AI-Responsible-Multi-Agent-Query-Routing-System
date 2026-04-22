from __future__ import annotations

from langsmith import traceable

from core.config import Settings, logger
from core.state import AgentResponse, ClassificationOutput
from agents.base import call_llm
from services.retrieval_service import get_retrieval_result

LEGAL_DISCLAIMER = (
    "This is general legal information, not legal advice. Laws vary by jurisdiction; consult a licensed attorney."
)


def _context_hint(context: str) -> str:
    if not context.strip():
        return ""
    first_line = next((line.strip() for line in context.splitlines() if line.strip()), "")
    if not first_line:
        return ""
    return f"\n\nRelevant retrieved note:\n- {first_line[:260]}"


def _fallback_legal_response(query: str, classification: ClassificationOutput, context: str) -> str:
    query_lower = query.lower()
    lines: list[str] = []

    if classification.risk_level == "high":
        lines.extend(
            [
                "Immediate safety:",
                "- If there is violence, threat, stalking, wrongful detention, or immediate danger, contact emergency services or local police first.",
                "- Move to a safer place if possible and contact a trusted person before focusing on documents.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "General legal explanation:",
                "- This looks like a practical legal-process question. The exact remedy depends on your city/state, documents, deadlines, and facts.",
                "",
            ]
        )

    steps = [
        "Create a short timeline with dates, amounts, people involved, and what was promised or refused.",
        "Collect proof: agreement, payment records, messages, emails, photos, notices, receipts, and ID/reference numbers.",
        "Send important communication in writing and keep delivery proof or acknowledgement.",
        "Speak with a licensed local lawyer or legal aid clinic before filing formal proceedings.",
    ]
    if any(term in query_lower for term in ("landlord", "deposit", "rent", "tenant")):
        steps.insert(0, "For a deposit dispute, check the rent agreement clause, payment proof, handover condition photos, and written demands already sent.")
    if "fir" in query_lower or "police" in query_lower:
        steps.insert(0, "For FIR/police issues, keep a copy of your written complaint and note the police station, date, officer name, and diary/reference number if given.")
    if any(term in query_lower for term in ("salary", "termination", "employer")):
        steps.insert(0, "For employment disputes, preserve offer letter, payslips, attendance proof, termination notice, and work communication.")

    lines.append("Practical next steps:")
    lines.extend(f"- {step}" for step in steps[:5])
    lines.extend(
        [
            "",
            "What to avoid:",
            "- Do not threaten, forge documents, delete messages, or rely only on verbal communication.",
            "- Do not miss limitation periods or official deadlines; ask a local professional if timing matters.",
        ]
    )

    return "\n".join(lines).strip() + _context_hint(context)


@traceable(name="legal_agent")
def run_legal_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    retrieval = get_retrieval_result(query=query, domain="legal", settings=settings)
    context = retrieval.context
    try:
        # 1. Retrieve Context
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
        fallback = _fallback_legal_response(query, classification, context)
        return AgentResponse(
            content=fallback,
            disclaimers=[LEGAL_DISCLAIMER],
            safety_notes=[],
            sources=retrieval.sources,
        )
