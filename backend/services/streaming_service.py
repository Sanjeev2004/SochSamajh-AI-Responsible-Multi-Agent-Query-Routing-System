"""
services/streaming_service.py
Streaming pipeline: classify → build prompt → yield SSE events.

The endpoint calls build_sse_stream() and wraps it in a FastAPI StreamingResponse.
Each Server-Sent Event (SSE) follows the format:
  data: <json payload>\n\n

Event types (sent as JSON with a "type" field):
  - "metadata"  : classification result + disclaimers (sent first)
  - "token"     : one text chunk from the LLM
  - "done"      : signals stream end, includes full assembled text + sources
  - "error"     : something went wrong
"""
from __future__ import annotations

import json
import re
import uuid
from collections.abc import Generator

from core.config import Settings, logger
from core.state import ClassificationOutput, Domain
from agents.classifier import classify_intent
from agents.base import stream_llm
from services.retrieval_service import get_retrieval_result


# ── Prompt builders (mirror the logic in medical.py / legal.py) ───────────────

MEDICAL_DISCLAIMER = (
    "This is general educational information and not medical advice. "
    "Please consult a qualified healthcare professional."
)
LEGAL_DISCLAIMER = (
    "This is general legal information, not legal advice. "
    "Laws vary by jurisdiction; consult a licensed attorney."
)

CRISIS_RE = re.compile(
    r"\b(give up|can't cope|no point|hopeless|want to disappear|end it)\b",
    re.IGNORECASE,
)
MENTAL_RE = re.compile(
    r"\b(depress|anxi|panic|stress|overwhelm|mental|lonely)\b",
    re.IGNORECASE,
)


def _build_medical_prompt(
    query: str,
    classification: ClassificationOutput,
    context: str,
    user_context: str | None,
) -> tuple[str, float]:
    urgency = ""
    if classification.risk_level == "high":
        urgency = (
            "Start with an 'Immediate action' section in 2-3 bullets. "
            "Clearly advise emergency care for red flags, and include one 'What not to do' bullet when relevant. "
        )
    elif classification.risk_level == "medium":
        urgency = "Include a 'Warning signs' section that should prompt urgent in-person medical evaluation. "

    parts = [
        "You are a medical information assistant. Provide educational, high-level information only. "
        "Do NOT diagnose, prescribe, or provide dosages. Encourage professional medical help when appropriate. "
        "Do not say the user likely has a specific disease; say symptoms can happen with several conditions. "
        "Use the provided context to answer if relevant. If the context is not relevant, ignore it. "
    ]
    if urgency:
        parts.append(urgency)
    if user_context:
        parts.append(f"\nUser's Personal Document Context:\n{user_context[:4000]}\n")
    parts.append(f"\nGeneral Knowledge Base Context:\n{context}\n")
    parts.append(
        "Keep response short, readable, and plain text. Use hyphen bullets only. "
        "Use these plain section labels when possible: What this may mean:, Safe next steps:, Seek urgent care if:. "
        "Put each practical action or warning sign on its own hyphen bullet. "
        "Do not use markdown tables, heading markers, or pipe-separated formatting."
    )
    temperature = 0.4 if MENTAL_RE.search(query) else 0.2
    return "\n".join(parts), temperature


def _build_legal_prompt(
    classification: ClassificationOutput,
    context: str,
    user_context: str | None,
) -> tuple[str, float]:
    urgency = ""
    if classification.risk_level == "high":
        urgency = "If user may be in immediate danger, start with an 'Immediate safety' section before legal process details. "

    parts = [
        "You are a legal information assistant. Provide general, high-level information only. "
        "Do NOT provide definitive legal advice. Note that laws vary by jurisdiction. "
    ]
    if urgency:
        parts.append(urgency)
    if user_context:
        parts.append(f"\nUser's Personal Document Context:\n{user_context[:4000]}\n")
    parts.append(f"\nGeneral Knowledge Base Context:\n{context}\n")
    parts.append(
        "Keep response short, readable, and plain text. Use hyphen bullets only. "
        "Use these plain section labels when possible: General legal explanation:, Practical next steps:, What to avoid:. "
        "Put each practical action or warning on its own hyphen bullet. "
        "Give practical, lawful next steps when possible. "
        "Do not use markdown tables, heading markers, or pipe-separated formatting."
    )
    return "\n".join(parts), 0.2


def _build_general_prompt(classification: ClassificationOutput) -> tuple[str, float]:
    ambiguity = ""
    if classification.domain == Domain.UNKNOWN:
        ambiguity = (
            "The query is ambiguous. Ask 2-3 concise clarification questions to identify whether "
            "the issue is medical, legal, or general. Do not guess the domain too early. "
        )
    prompt = (
        "You are a helpful general assistant. Answer clearly and safely in plain text. "
        "Keep response compact and readable. Use hyphen bullets when needed. "
        "Do not use markdown tables, heading markers, or pipe-separated formatting. "
        f"{ambiguity}"
        "If user asks for medical or legal advice, keep it general and encourage professional help."
    )
    return prompt, 0.3


def _sse(payload: dict) -> str:
    """Format a dict as a Server-Sent Event line."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def build_sse_stream(
    query: str,
    settings: Settings,
    user_context: str | None = None,
) -> Generator[str, None, None]:
    """Core streaming generator. Yields SSE-formatted strings.

    Sequence of events:
      1. metadata  — classification + disclaimers (always)
      2. token×N   — LLM text chunks (if LLM is enabled)
      3. done      — full text + sources
      On any failure: error event.
    """
    request_id = str(uuid.uuid4())

    try:
        # ── Step 1: Classify ─────────────────────────────────────────────────
        classification = classify_intent(query, settings)

        # Build disclaimer list
        disclaimers: list[str] = []
        if classification.domain == Domain.MEDICAL:
            disclaimers.append(MEDICAL_DISCLAIMER)
        elif classification.domain == Domain.LEGAL:
            disclaimers.append(LEGAL_DISCLAIMER)

        # ── Step 2: Send metadata immediately ────────────────────────────────
        yield _sse({
            "type": "metadata",
            "request_id": request_id,
            "classification": classification.model_dump(),
            "disclaimers": disclaimers,
            "safety_flags": {
                "self_harm": classification.self_harm,
                "illegal_request": classification.illegal_request,
                "high_risk": classification.risk_level == "high",
            },
        })

        # ── Step 3: Retrieve context ──────────────────────────────────────────
        sources: list[dict] = []
        context = ""
        if settings.enable_retriever and classification.domain in {Domain.MEDICAL, Domain.LEGAL}:
            try:
                retrieval = get_retrieval_result(
                    query=query,
                    domain=classification.domain.value,
                    settings=settings,
                )
                context = retrieval.context
                seen: set[str] = set()
                for s in retrieval.sources:
                    if s.source not in seen:
                        seen.add(s.source)
                        sources.append(s.model_dump())
            except Exception as exc:
                logger.warning("Streaming retrieval failed: %s", exc)

        # ── Step 4: Build prompt ──────────────────────────────────────────────
        if classification.domain == Domain.MEDICAL:
            system_prompt, temperature = _build_medical_prompt(
                query, classification, context, user_context
            )
        elif classification.domain == Domain.LEGAL:
            system_prompt, temperature = _build_legal_prompt(
                classification, context, user_context
            )
        else:
            system_prompt, temperature = _build_general_prompt(classification)

        # ── Step 5: Stream tokens ─────────────────────────────────────────────
        full_text_parts: list[str] = []

        if settings.enable_llm:
            try:
                for chunk in stream_llm(
                    query=query,
                    system_prompt=system_prompt,
                    settings=settings,
                    temperature=temperature,
                ):
                    full_text_parts.append(chunk)
                    yield _sse({"type": "token", "text": chunk})
            except Exception as exc:
                logger.warning("Streaming LLM failed, falling back to error: %s", exc)
                yield _sse({"type": "error", "message": str(exc)})
                return
        else:
            # LLM disabled — send a single informational token
            fallback = (
                "LLM is currently disabled. Enable it by setting ENABLE_LLM=true "
                "and providing a valid API key."
            )
            full_text_parts.append(fallback)
            yield _sse({"type": "token", "text": fallback})

        # ── Step 6: Done ──────────────────────────────────────────────────────
        yield _sse({
            "type": "done",
            "request_id": request_id,
            "full_text": "".join(full_text_parts),
            "sources": sources,
        })

    except Exception as exc:
        logger.exception("Unhandled error in SSE stream: %s", exc)
        yield _sse({"type": "error", "message": f"Internal error: {exc}"})
