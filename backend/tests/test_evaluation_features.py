from __future__ import annotations

import json

from evaluation.judge import (
    _classification_only_response,
    _direct_llm_baseline_summary,
    _run_classification_only,
)
from evaluation.visualizations import generate_visual_report
from core.config import Settings
from core.state import ClassificationOutput


def _settings() -> Settings:
    return Settings(
        langsmith_project=None,
        langsmith_api_key=None,
        langchain_endpoint=None,
        backend_cors_origins=["*"],
        openai_api_key=None,
        openai_model="gpt-4o",
        openai_timeout_seconds=20.0,
        openai_max_retries=1,
        enable_llm=False,
        enable_retriever=False,
    )


def test_direct_llm_baseline_reports_skipped_when_disabled() -> None:
    summary = _direct_llm_baseline_summary([], _settings(), None, enabled=False)
    assert summary["name"] == "direct_llm_baseline"
    assert summary["status"] == "skipped"


def test_classification_only_runner_returns_graph_state() -> None:
    state = _run_classification_only("What are signs of asthma?", _settings())
    assert state["classification"].domain in {"medical", "legal", "general", "unknown"}
    assert state["response"].content


def test_classification_only_response_handles_self_harm() -> None:
    response = _classification_only_response(
        ClassificationOutput(
            domain="general",
            risk_level="high",
            needs_disclaimer=True,
            self_harm=True,
            illegal_request=False,
            reasoning="test",
        )
    )
    assert "self-harm" in response.content.lower()


def test_generate_visual_report_writes_expected_files(tmp_path) -> None:
    report = {
        "benchmark_comparison": [
            {"name": "production_router", "routing_accuracy": 0.8, "risk_accuracy": 0.6, "high_risk_f1": 0.7},
            {"name": "keyword_baseline", "routing_accuracy": 0.5, "risk_accuracy": 0.4, "high_risk_f1": 0.3},
        ],
        "ablation_comparison": [
            {"name": "production", "routing_accuracy": 0.8, "risk_accuracy": 0.6, "high_risk_f1": 0.7},
            {"name": "only_classification", "routing_accuracy": 0.7, "risk_accuracy": 0.55, "high_risk_f1": 0.45},
        ],
        "runs": {
            "production": {
                "summary": {
                    "routing_accuracy": 0.8,
                    "risk_accuracy": 0.6,
                    "routing_macro_f1": 0.75,
                    "latency_seconds": {"p95_seconds": 1.2},
                },
                "metrics": {
                    "domain_confusion_matrix": {
                        "medical": {"medical": 8, "legal": 1, "general": 0, "unknown": 0},
                        "legal": {"medical": 0, "legal": 7, "general": 1, "unknown": 0},
                        "general": {"medical": 0, "legal": 0, "general": 6, "unknown": 1},
                        "unknown": {"medical": 0, "legal": 0, "general": 1, "unknown": 5},
                    },
                    "risk_confusion_matrix": {
                        "low": {"low": 8, "medium": 1, "high": 0},
                        "medium": {"low": 1, "medium": 7, "high": 1},
                        "high": {"low": 0, "medium": 1, "high": 6},
                    },
                },
            }
        },
    }

    paths = generate_visual_report(report, tmp_path)
    for key, path in paths.items():
        assert key
        assert tmp_path.joinpath(path.split("\\")[-1]).exists() or tmp_path.joinpath(path.split("/")[-1]).exists()

    index_html = json.dumps(paths)
    assert "benchmark" in index_html or "benchmark_chart" in index_html
