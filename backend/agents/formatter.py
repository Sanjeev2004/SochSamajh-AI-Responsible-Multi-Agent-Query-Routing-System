from __future__ import annotations

import re

from langsmith import traceable

from core.state import AgentResponse, ClassificationOutput

MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s*", re.MULTILINE)
EXCESS_BLANK_LINES_RE = re.compile(r"\n{3,}")
TABLE_SEPARATOR_RE = re.compile(r"\|?[\s:\-]+(\|[\s:\-]+)+\|?")
EMERGENCY_INTENT_RE = re.compile(r"\b(urgent|emergency|immediately|right now|asap|abhi|jaldi)\b", re.IGNORECASE)
LEGAL_ACTION_RE = re.compile(
    r"\b(next\s+step|what\s+should\s+i\s+do|process|procedure|documents?|file|complaint|notice|fir)\b",
    re.IGNORECASE,
)
MEDICAL_WARNING_RE = re.compile(
    r"\b(fever|headache|vomit|breathing|asthma|dengue|infection|bleeding|chest|pain|pregnancy)\b",
    re.IGNORECASE,
)

def _clean_markdown_noise(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    replacements = {
        "â€”": "-",
        "â€“": "-",
        "â€‘": "-",
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€ ": '"',
        "â€¦": "...",
        "â€¯": " ",
        "Â½": "1/2",
        "Â°F": " F",
        "Â°C": " C",
    }
    for bad, good in replacements.items():
        normalized = normalized.replace(bad, good)

    cleaned_lines: list[str] = []

    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue

        # Remove markdown heading markers.
        line = MARKDOWN_HEADING_RE.sub("", line)
        # Remove bold/italic/code markers.
        line = line.replace("**", "").replace("__", "").replace("`", "")

        # Drop pure markdown table separator rows like |---|---|
        if TABLE_SEPARATOR_RE.fullmatch(line):
            continue

        # Convert pipe-delimited table rows into readable sentence fragments.
        if line.count("|") >= 2:
            cells = [cell.strip() for cell in line.strip("|").split("|") if cell.strip()]
            if cells:
                line = " - ".join(cells)

        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    # Limit excess blank lines.
    cleaned = EXCESS_BLANK_LINES_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def _append_lines(base: str, heading: str, lines: list[str]) -> str:
    section = heading + "\n" + "\n".join(f"- {line}" for line in lines)
    if not base.strip():
        return section
    return base.rstrip() + "\n\n" + section


def _inject_medical_urgency(content: str) -> str:
    low = content.lower()
    if "immediate steps" in low or "call emergency" in low or "nearest emergency" in low:
        return content
    return _append_lines(
        content,
        "Immediate steps:",
        [
            "If symptoms are severe or getting worse, call local emergency services now.",
            "Do not drive yourself if you feel faint, breathless, or have chest pain.",
            "Seek urgent in-person evaluation at the nearest emergency department.",
            "Do not delay emergency care while waiting for an online answer.",
        ],
    )


def _inject_medical_warning_signs(content: str) -> str:
    low = content.lower()
    if "seek urgent care" in low or "warning signs" in low:
        return content
    return _append_lines(
        content,
        "Seek urgent care if:",
        [
            "Symptoms are getting worse, you feel faint, confused, or unusually weak.",
            "Breathing becomes difficult, pain becomes severe, or you cannot keep fluids down.",
            "You notice heavy bleeding, new chest symptoms, or pregnancy-related warning signs.",
        ],
    )


def _inject_legal_practical_steps(content: str, high_risk: bool) -> str:
    low = content.lower()
    if "practical next steps" in low:
        return content
    steps = [
        "Write a short timeline of what happened (dates, places, people involved).",
        "Collect and keep copies of key documents, messages, photos, and receipts.",
        "Send important communication in writing and keep acknowledgements.",
        "Contact a licensed local lawyer or legal aid clinic for jurisdiction-specific advice.",
    ]
    if high_risk:
        steps.insert(0, "If there is immediate threat or violence, contact emergency services/police right away.")
        steps.insert(1, "Move to a safer place if possible and contact a trusted person before handling paperwork.")
    return _append_lines(content, "Practical next steps:", steps)


def _inject_ambiguity_clarification(content: str, query: str) -> str:
    low = content.lower()
    if "to guide you better" in low or "please clarify" in low:
        return content
    lines = [
        "Is this mainly a medical issue, a legal issue, or something else?",
        "What happened, when did it start, and who is involved?",
        "What outcome do you want in the next 24-48 hours?",
    ]
    if EMERGENCY_INTENT_RE.search(query):
        lines.append("If anyone is in immediate danger, contact local emergency services now.")
    return _append_lines(content, "To guide you better, please clarify:", lines)


@traceable(name="response_formatter")
def run_formatter(response: AgentResponse, classification: ClassificationOutput, query: str = "") -> AgentResponse:
    disclaimers = list(response.disclaimers)
    content = _clean_markdown_noise(response.content)

    if classification.domain == "medical" and classification.risk_level == "high":
        content = _inject_medical_urgency(content)
    elif classification.domain == "medical" and classification.risk_level == "medium" and MEDICAL_WARNING_RE.search(query):
        content = _inject_medical_warning_signs(content)

    if classification.domain == "legal" and (
        classification.risk_level in {"medium", "high"} or LEGAL_ACTION_RE.search(query)
    ):
        content = _inject_legal_practical_steps(content, high_risk=classification.risk_level == "high")

    if classification.domain == "unknown":
        content = _inject_ambiguity_clarification(content, query)

    if classification.needs_disclaimer and not disclaimers:
        if classification.domain == "medical":
            disclaimers.append("This is general educational information, not medical advice.")
        elif classification.domain == "legal":
            disclaimers.append("This is general legal information, not legal advice.")

    return AgentResponse(
        content=content,
        disclaimers=disclaimers,
        safety_notes=response.safety_notes,
        sources=response.sources,
    )
