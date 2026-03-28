from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _round_metrics(values: dict[str, Any]) -> dict[str, Any]:
    rounded: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, float):
            rounded[key] = round(value, 4)
        else:
            rounded[key] = value
    return rounded


def classification_report(
    expected_labels: list[str],
    predicted_labels: list[str],
    labels: list[str],
) -> dict[str, Any]:
    per_label: dict[str, dict[str, Any]] = {}
    total_support = len(expected_labels)
    weighted_precision = 0.0
    weighted_recall = 0.0
    weighted_f1 = 0.0

    for label in labels:
        tp = sum(1 for exp, pred in zip(expected_labels, predicted_labels) if exp == label and pred == label)
        fp = sum(1 for exp, pred in zip(expected_labels, predicted_labels) if exp != label and pred == label)
        fn = sum(1 for exp, pred in zip(expected_labels, predicted_labels) if exp == label and pred != label)
        support = sum(1 for exp in expected_labels if exp == label)

        precision = _safe_divide(tp, tp + fp)
        recall = _safe_divide(tp, tp + fn)
        f1 = _safe_divide(2 * precision * recall, precision + recall)

        weighted_precision += precision * support
        weighted_recall += recall * support
        weighted_f1 += f1 * support

        per_label[label] = _round_metrics(
            {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": support,
            }
        )

    macro_precision = mean(per_label[label]["precision"] for label in labels) if labels else 0.0
    macro_recall = mean(per_label[label]["recall"] for label in labels) if labels else 0.0
    macro_f1 = mean(per_label[label]["f1"] for label in labels) if labels else 0.0

    accuracy = _safe_divide(
        sum(1 for exp, pred in zip(expected_labels, predicted_labels) if exp == pred),
        len(expected_labels),
    )

    return {
        "accuracy": round(accuracy, 4),
        "per_label": per_label,
        "macro_avg": _round_metrics(
            {
                "precision": macro_precision,
                "recall": macro_recall,
                "f1": macro_f1,
                "support": total_support,
            }
        ),
        "weighted_avg": _round_metrics(
            {
                "precision": _safe_divide(weighted_precision, total_support),
                "recall": _safe_divide(weighted_recall, total_support),
                "f1": _safe_divide(weighted_f1, total_support),
                "support": total_support,
            }
        ),
    }


def confusion_matrix(
    expected_labels: list[str],
    predicted_labels: list[str],
    labels: list[str],
) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {}
    for expected in labels:
        row: dict[str, int] = {}
        for predicted in labels:
            row[predicted] = sum(
                1
                for exp, pred in zip(expected_labels, predicted_labels)
                if exp == expected and pred == predicted
            )
        matrix[expected] = row
    return matrix


def top_confusions(
    matrix: dict[str, dict[str, int]],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    confusions: list[dict[str, Any]] = []
    for expected, row in matrix.items():
        for predicted, count in row.items():
            if expected == predicted or count == 0:
                continue
            confusions.append(
                {
                    "expected": expected,
                    "predicted": predicted,
                    "count": count,
                }
            )

    confusions.sort(key=lambda item: (-item["count"], item["expected"], item["predicted"]))
    return confusions[:limit]


def binary_metrics(expected: list[bool], predicted: list[bool]) -> dict[str, Any]:
    tp = sum(1 for exp, pred in zip(expected, predicted) if exp and pred)
    tn = sum(1 for exp, pred in zip(expected, predicted) if not exp and not pred)
    fp = sum(1 for exp, pred in zip(expected, predicted) if not exp and pred)
    fn = sum(1 for exp, pred in zip(expected, predicted) if exp and not pred)

    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    accuracy = _safe_divide(tp + tn, len(expected))

    return _round_metrics(
        {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_positive_rate": _safe_divide(fp, fp + tn),
            "false_negative_rate": _safe_divide(fn, fn + tp),
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "support_positive": sum(1 for value in expected if value),
            "support_negative": sum(1 for value in expected if not value),
        }
    )


def latency_summary(latencies: list[float]) -> dict[str, float]:
    if not latencies:
        return {"count": 0, "mean_seconds": 0.0, "p50_seconds": 0.0, "p95_seconds": 0.0, "p99_seconds": 0.0}

    sorted_latencies = sorted(latencies)

    def percentile(value: float) -> float:
        if len(sorted_latencies) == 1:
            return sorted_latencies[0]
        index = value * (len(sorted_latencies) - 1)
        lower_index = int(index)
        upper_index = min(len(sorted_latencies) - 1, lower_index + 1)
        if lower_index == upper_index:
            return sorted_latencies[lower_index]
        fraction = index - lower_index
        lower_value = sorted_latencies[lower_index]
        upper_value = sorted_latencies[upper_index]
        return lower_value + (upper_value - lower_value) * fraction

    return _round_metrics(
        {
            "count": len(sorted_latencies),
            "mean_seconds": mean(sorted_latencies),
            "p50_seconds": percentile(0.50),
            "p95_seconds": percentile(0.95),
            "p99_seconds": percentile(0.99),
        }
    )


def label_distribution(values: list[str]) -> dict[str, int]:
    counts = Counter(values)
    return dict(sorted(counts.items()))
