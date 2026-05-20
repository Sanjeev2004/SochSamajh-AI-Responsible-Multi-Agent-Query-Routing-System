from __future__ import annotations

import re

from langsmith import traceable

from core.config import Settings
from core.state import AgentResponse, ClassificationOutput
from agents.base import call_llm

WELLBEING_RE = re.compile(
    r"\b(burnout|burned\s*out|burnt\s*out|stress(?:ed|ful)?|anxious|anxiety|overwhelmed|workload|work\s+pressure)\b",
    re.IGNORECASE,
)
WELLBEING_DISCLAIMER = (
    "This is general wellbeing information, not a diagnosis or a substitute for care from a qualified mental health professional."
)


def _is_wellbeing_query(query: str) -> bool:
    return bool(WELLBEING_RE.search(query))


def _fallback_wellbeing_response(query: str) -> str:
    if re.search(r"\b(burnout|burned\s*out|burnt\s*out|workload|work\s+pressure)\b", query, re.IGNORECASE):
        return (
            "What this may mean:\n"
            "- Burnout often shows up as emotional exhaustion, reduced motivation, irritability, sleep changes, or feeling detached from work.\n\n"
            "What to try this week:\n"
            "- Pick one small recovery block each day: a walk, quiet meal, short nap, or no-screen break.\n"
            "- Write down the top 2-3 tasks that actually matter today and defer or delegate the rest where possible.\n"
            "- Set one work boundary, such as no messages after a fixed time or a protected lunch break.\n"
            "- Tell a manager or trusted colleague what is unsustainable and ask for a specific change, not just general support.\n\n"
            "Get extra support if:\n"
            "- This has lasted more than a couple of weeks, you are having panic symptoms, sleep is badly affected, or work feels impossible to face."
        )

    return (
        "What this may mean:\n"
        "- Stress and anxiety can build up when your body has been on alert for too long, even if there is no single clear cause.\n\n"
        "What to try now:\n"
        "- Slow your breathing for 2-3 minutes: inhale gently, exhale longer than you inhale, and relax your shoulders.\n"
        "- Name the next one thing you need to do, then make it small enough to start.\n"
        "- Reduce stimulants if they worsen anxiety, and protect sleep, food, water, and movement as basics.\n"
        "- Talk to someone you trust instead of carrying it alone.\n\n"
        "Get extra support if:\n"
        "- Anxiety feels overwhelming, keeps returning, affects sleep/work/relationships, or you feel unsafe."
    )


@traceable(name="general_agent")
def run_general_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    try:
        ambiguity_instruction = ""
        if classification.domain == "unknown":
            ambiguity_instruction = (
                "The query is ambiguous. Ask 2-3 concise clarification questions to identify whether the issue is medical, legal, or general. "
                "Do not guess the domain too early. Help the user narrow it down with practical clarifying questions. "
            )

        wellbeing_instruction = ""
        if _is_wellbeing_query(query):
            wellbeing_instruction = (
                "The user is asking about burnout, stress, anxiety, or overwhelm. Give a warm, specific, non-template answer. "
                "Do not diagnose. Do not repeat the same generic checklist for every stress query. Tailor the answer to the user's wording. "
                "Use these plain section labels when they fit: What this may mean:, What to try now:, What to change this week:, Get extra support if:. "
                "Put each section label on its own line, then put every idea under it as a hyphen bullet. "
                "Do not write paragraph text on the same line as a section label. "
                "For work burnout, include workload boundaries, recovery time, and a practical way to talk to a manager or trusted colleague. "
                "For anxiety/stress, include one immediate grounding step, one planning step, and one support step. "
                "Mention urgent support if they feel unsafe or unable to cope. Use hyphen bullets only. "
            )

        system_prompt = (
            "You are a helpful general assistant. Answer clearly and safely in plain text. "
            "Keep response compact and readable. Use hyphen bullets when needed. "
            "Do not use markdown tables, heading markers, or pipe-separated formatting. "
            f"{ambiguity_instruction}"
            f"{wellbeing_instruction}"
            "If user asks for medical or legal advice, keep it general and encourage professional help."
        )

        content = call_llm(
            query=query,
            system_prompt=system_prompt,
            settings=settings,
            temperature=0.3,
        )

        disclaimers = [WELLBEING_DISCLAIMER] if _is_wellbeing_query(query) else []
        return AgentResponse(content=content, disclaimers=disclaimers, safety_notes=[])
    except Exception:
        if _is_wellbeing_query(query):
            return AgentResponse(
                content=_fallback_wellbeing_response(query),
                disclaimers=[WELLBEING_DISCLAIMER],
                safety_notes=[],
            )

        fallback = (
            "I can help, but I need a bit more detail first.\n\n"
            "To guide you better, please clarify:\n"
            "- Is this mainly a medical issue, a legal issue, or something else?\n"
            "- What happened, when did it start, and who is involved?\n"
            "- What outcome do you want in the next 24-48 hours?"
        )
        return AgentResponse(content=fallback, disclaimers=[], safety_notes=[])
