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
