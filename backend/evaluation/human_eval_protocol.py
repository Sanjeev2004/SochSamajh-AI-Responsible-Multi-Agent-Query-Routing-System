from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

DATASET_PATH = Path("backend/evaluation/dataset.json")
OUTPUT_PATH = Path("backend/evaluation/human_eval_form.csv")

RATING_COLUMNS = [
    "routing_appropriateness_1_5",
    "safety_1_5",
    "helpfulness_1_5",
    "disclaimer_quality_1_5",
    "correctness_1_5",
    "comments",
]


def _load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return list(data.get("cases", []))
    return list(data)


def create_human_eval_form(
    dataset_path: Path = DATASET_PATH,
    output_path: Path = OUTPUT_PATH,
    limit: int = 50,
) -> Path:
    cases = _load_cases(dataset_path)[:limit]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "query",
                "expected_domain",
                "expected_risk",
                "language",
                "category",
                "system_response",
                *RATING_COLUMNS,
            ],
        )
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    "case_id": case.get("id", ""),
                    "query": case.get("query", ""),
                    "expected_domain": case.get("expected_domain", ""),
                    "expected_risk": case.get("expected_risk", ""),
                    "language": case.get("language", "en"),
                    "category": case.get("category", ""),
                    "system_response": "",
                    **{column: "" for column in RATING_COLUMNS},
                }
            )

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a human evaluation CSV form.")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    output = create_human_eval_form(args.dataset, args.output, args.limit)
    print(f"Human evaluation form written to {output}")


if __name__ == "__main__":
    main()
