from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from langsmith import traceable

from core.config import logger
from core.graph import run_router

TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"
OUTPUT_PATH = Path(__file__).parent / "eval_results.jsonl"


@traceable(name="eval_case")
def run_case(case: dict[str, Any]) -> dict[str, Any]:
    state = run_router(case["query"])
    classification = state["classification"]
    safety_flags = state["safety_flags"]

    expected_domain = case.get("expected_domain")
    expected_risk = case.get("expected_risk")
    expected_self_harm = case.get("expected_self_harm")
    expected_illegal = case.get("expected_illegal")

    result = {
        "id": case["id"],
        "query": case["query"],
        "domain": classification.domain,
        "risk_level": classification.risk_level,
        "self_harm": classification.self_harm,
        "illegal_request": classification.illegal_request,
        "expected_domain": expected_domain,
        "expected_risk": expected_risk,
        "expected_self_harm": expected_self_harm,
        "expected_illegal": expected_illegal,
        "match_domain": classification.domain == expected_domain,
        "match_risk": classification.risk_level == expected_risk,
        "match_self_harm": expected_self_harm is None or classification.self_harm == expected_self_harm,
        "match_illegal": expected_illegal is None or classification.illegal_request == expected_illegal,
        "high_risk": safety_flags.high_risk,
    }

    if not result["match_domain"] or not result["match_risk"]:
        logger.warning("Misclassification detected", extra={"case_id": case["id"]})

    if safety_flags.high_risk or safety_flags.self_harm or safety_flags.illegal_request:
        logger.info("Safety-flagged output", extra={"case_id": case["id"]})

    return result


def main() -> None:
    cases = json.loads(TEST_CASES_PATH.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        results.append(run_case(case))

    OUTPUT_PATH.write_text("\n".join(json.dumps(r) for r in results), encoding="utf-8")

    total = len(results)
    domain_acc = sum(r["match_domain"] for r in results) / total
    risk_acc = sum(r["match_risk"] for r in results) / total

    print(f"Cases: {total}")
    print(f"Domain accuracy: {domain_acc:.2f}")
    print(f"Risk accuracy: {risk_acc:.2f}")
    print(f"Results written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
