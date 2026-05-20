from __future__ import annotations

from agents.formatter import run_formatter
from core.state import AgentResponse, ClassificationOutput


def test_formatter_normalizes_markdown_bullets() -> None:
    response = AgentResponse(
        content="Next steps:\n* Drink fluids\n+ Rest\n- Call a doctor if worse",
        disclaimers=[],
    )
    classification = ClassificationOutput(
        domain="medical",
        risk_level="low",
        needs_disclaimer=True,
        self_harm=False,
        illegal_request=False,
        reasoning="test",
    )

    formatted = run_formatter(response, classification)

    assert "* Drink fluids" not in formatted.content
    assert "+ Rest" not in formatted.content
    assert "- Drink fluids" in formatted.content
    assert "- Rest" in formatted.content


def test_formatter_does_not_duplicate_existing_clarification() -> None:
    response = AgentResponse(
        content=(
            "To better understand your issue, can you please provide more context.\n"
            "- What happened?\n"
            "- When did it start?"
        ),
        disclaimers=[],
    )
    classification = ClassificationOutput(
        domain="unknown",
        risk_level="low",
        needs_disclaimer=False,
        self_harm=False,
        illegal_request=False,
        reasoning="test",
    )

    formatted = run_formatter(response, classification)

    assert formatted.content.count("To guide you better, please clarify:") == 0
    assert formatted.content.count("What happened?") == 1
