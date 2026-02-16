from __future__ import annotations

import re

from langsmith import traceable

from core.state import AgentResponse, ClassificationOutput


def _clean_markdown_noise(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    replacements = {
        "â": "-",
        "â": "-",
        "â": "-",
        "â": "'",
        "â": "'",
        "â": '"',
        "â": '"',
        "â¦": "...",
        "â¯": " ",
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
        line = re.sub(r"^#{1,6}\s*", "", line)
        # Remove bold/italic/code markers.
        line = line.replace("**", "").replace("__", "").replace("`", "")

        # Drop pure markdown table separator rows like |---|---|
        if re.fullmatch(r"\|?[\s:\-]+(\|[\s:\-]+)+\|?", line):
            continue

        # Convert pipe-delimited table rows into readable sentence fragments.
        if line.count("|") >= 2:
            cells = [cell.strip() for cell in line.strip("|").split("|") if cell.strip()]
            if cells:
                line = " - ".join(cells)

        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    # Limit excess blank lines.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


@traceable(name="response_formatter")
def run_formatter(response: AgentResponse, classification: ClassificationOutput) -> AgentResponse:
    disclaimers = list(response.disclaimers)
    if classification.needs_disclaimer and not disclaimers:
        if classification.domain == "medical":
            disclaimers.append("This is general educational information, not medical advice.")
        elif classification.domain == "legal":
            disclaimers.append("This is general legal information, not legal advice.")

    return AgentResponse(
        content=_clean_markdown_noise(response.content),
        disclaimers=disclaimers,
        safety_notes=response.safety_notes,
    )
