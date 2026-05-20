from __future__ import annotations

from langsmith import traceable

from core.config import Settings, logger
from core.state import AgentResponse, ClassificationOutput
from agents.base import call_llm
from agents.utils import _context_hint, MAX_QUERY_LENGTH
from services.retrieval_service import get_retrieval_result, RetrievalResult
import re

CRISIS_RE = re.compile(
    r"\b(give up|can't cope|no point|hopeless|want to disappear|end it)\b",
    re.IGNORECASE,
)
MENTAL_RE = re.compile(
    r"\b(depress|anxi|panic|stress|overwhelm|mental|lonely)\b", 
    re.IGNORECASE
)

MEDICAL_DISCLAIMER = "This is general educational information and not medical advice. Please consult a qualified healthcare professional."





def _fallback_medical_response(query: str, classification: ClassificationOutput, context: str) -> str:
    query_lower = query.lower()
    lines: list[str] = []

    if CRISIS_RE.search(query_lower):
        lines.insert(0, "iCall helpline: 9152987821 (free, confidential)")
        lines.insert(0, "If you are in distress, please reach out for support:")

    if classification.risk_level == "high":
        lines.extend(
            [
                "Immediate action:",
                "- This sounds potentially urgent. Seek emergency or same-day in-person medical care now, especially if symptoms are severe or worsening.",
                "- Do not drive yourself if you feel faint, breathless, confused, or have chest pain.",
                "- Keep a trusted person with you if possible while arranging care.",
                "",
            ]
        )
    elif classification.risk_level == "medium":
        lines.extend(
            [
                "What this may mean:",
                "- Your symptoms need monitoring and may need a clinician's assessment if they persist, worsen, or involve a child, pregnancy, older age, or chronic illness.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "General explanation:",
                "- This looks like a lower-risk medical information query, so I can share general educational guidance.",
                "",
            ]
        )

    safe_actions = [
        "Rest, drink fluids if you can tolerate them, and avoid self-prescribing strong medicines or antibiotics.",
        "Write down symptom start time, temperature if fever is present, medicines taken, allergies, and existing conditions.",
        "Contact a qualified doctor if symptoms last more than 24-48 hours, keep returning, or you are worried.",
    ]
    if any(term in query_lower for term in ("fever", "bukhar", "body pain")):
        safe_actions.insert(0, "For fever/body pain, track temperature and hydration; seek care sooner if fever is high, persistent, or with rash, severe weakness, breathing trouble, or confusion.")
    if any(term in query_lower for term in ("chest", "breath", "saans", "left arm", "sweating")):
        safe_actions.insert(0, "Chest symptoms, sweating, left-arm pain, or breathing difficulty should be treated as urgent.")
    if any(term in query_lower for term in ("dog bite", "bite", "rabies")):
        safe_actions.insert(0, "For animal bites, wash the wound with soap and running water and get urgent advice about rabies/tetanus prevention.")

    lines.append("Safe next steps:")
    lines.extend(f"- {action}" for action in safe_actions[:4])
    lines.extend(
        [
            "",
            "Seek urgent care if:",
            "- Breathing becomes difficult, pain is severe, you feel faint/confused, bleeding is heavy, or symptoms are rapidly worsening.",
            "- There is chest pain, stroke-like symptoms, poisoning, seizure, severe dehydration, or pregnancy-related bleeding.",
        ]
    )

    return "\n".join(lines).strip() + _context_hint(context)


@traceable(name="medical_agent")
def run_medical_agent(
    query: str, 
    classification: ClassificationOutput, 
    settings: Settings,
    user_context: str | None = None
) -> AgentResponse:
    query = query[:MAX_QUERY_LENGTH]
    try:
        retrieval = get_retrieval_result(query=query, domain="medical", settings=settings)
        context = retrieval.context
    except Exception as exc:
        logger.warning("Medical retrieval failed, proceeding without context: %s", exc)
        retrieval = RetrievalResult(context="", sources=[])
        context = ""
        
    seen = set()
    unique_sources = []
    for s in retrieval.sources:
        if s.source not in seen:
            seen.add(s.source)
            unique_sources.append(s)
            
    try:
        urgency_instruction = ""
        if classification.risk_level == "high":
            urgency_instruction = (
                "Start with an 'Immediate action' section in 2-3 bullets. "
                "Clearly advise emergency care for red flags, and include one 'What not to do' bullet when relevant. "
            )
        elif classification.risk_level == "medium":
            urgency_instruction = (
                "Include a 'Warning signs' section that should prompt urgent in-person medical evaluation. "
            )

        base_prompt = (
            "You are a medical information assistant. Provide educational, high-level information only. "
            "Do NOT diagnose, prescribe, or provide dosages. Encourage professional medical help when appropriate. "
            "Do not say the user likely has a specific disease; say symptoms can happen with several conditions. "
            "Use the provided context to answer if relevant. If the context is not relevant, ignore it. "
        )
        prompt_parts = [base_prompt]
        if urgency_instruction:
            prompt_parts.append(urgency_instruction)
            
        if user_context:
            prompt_parts.append(f"\nUser's Personal Document Context:\n{user_context[:4000]}\n")
            
        prompt_parts.append(f"\nGeneral Knowledge Base Context:\n{context}\n")
        prompt_parts.append(
            "Keep response short, readable, and plain text. Use hyphen bullets only. "
            "Use these plain section labels when possible: What this may mean:, Safe next steps:, Seek urgent care if:. "
            "Put each practical action or warning sign on its own hyphen bullet. "
            "For urgent-sounding symptoms, mention warning signs that should prompt emergency or same-day in-person care. "
            "Do not use markdown tables, heading markers, or pipe-separated formatting."
        )
        system_prompt = "\n".join(prompt_parts)

        temperature = 0.4 if MENTAL_RE.search(query) else 0.2
        content = call_llm(
            query=query,
            system_prompt=system_prompt,
            settings=settings,
            temperature=temperature
        )

        return AgentResponse(
            content=content,
            disclaimers=[MEDICAL_DISCLAIMER],
            safety_notes=[],
            sources=unique_sources,
        )
    except Exception as exc:
        if "LLM calls are disabled" in str(exc):
            logger.info("Medical agent using offline fallback because LLM calls are disabled.")
        else:
            logger.exception("Medical agent fell back to static response: %s", exc)
        fallback = _fallback_medical_response(query, classification, context)
        return AgentResponse(
            content=fallback,
            disclaimers=[MEDICAL_DISCLAIMER],
            safety_notes=[],
            sources=unique_sources,
        )
