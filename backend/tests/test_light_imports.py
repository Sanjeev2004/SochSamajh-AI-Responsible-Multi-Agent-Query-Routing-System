"""Ensure heavy ML stacks stay out of the import/graph path when flags are off."""
from __future__ import annotations

import importlib
import sys
from types import ModuleType


HEAVY_MODULES = (
    "sentence_transformers",
    "chromadb",
    "sklearn",
    "sklearn.metrics",
    "sklearn.metrics.pairwise",
)


def _purge_agent_modules(monkeypatch) -> None:
    for name in list(sys.modules):
        if (
            name in {"agents.classifier", "agents.router_semantic", "agents.retriever", "core.graph"}
            or name.startswith("agents.classifier.")
        ):
            monkeypatch.delitem(sys.modules, name, raising=False)


def _install_heavy_import_traps(monkeypatch) -> list[str]:
    """Replace heavy packages with sentinels that record any attribute access/import."""
    hits: list[str] = []

    class _Trap(ModuleType):
        def __getattr__(self, name: str):
            hits.append(f"{self.__name__}.{name}")
            raise ImportError(f"heavy module {self.__name__} must not load when disabled")

    for name in HEAVY_MODULES:
        monkeypatch.setitem(sys.modules, name, _Trap(name))
    return hits


def test_classifier_import_does_not_load_sentence_transformers(monkeypatch) -> None:
    _purge_agent_modules(monkeypatch)
    hits = _install_heavy_import_traps(monkeypatch)
    monkeypatch.setenv("ENABLE_SEMANTIC_ROUTER", "false")
    monkeypatch.setenv("ENABLE_RETRIEVER", "false")

    mod = importlib.import_module("agents.classifier")
    assert callable(mod.classify_intent)
    assert hits == []


def test_build_graph_with_flags_off_does_not_import_sentence_transformers(monkeypatch) -> None:
    _purge_agent_modules(monkeypatch)
    hits = _install_heavy_import_traps(monkeypatch)
    monkeypatch.setenv("ENABLE_SEMANTIC_ROUTER", "false")
    monkeypatch.setenv("ENABLE_RETRIEVER", "false")
    monkeypatch.setenv("ENABLE_LLM", "false")

    from core.config import Settings
    from core.graph import build_graph

    settings = Settings.load().model_copy(
        update={
            "enable_semantic_router": False,
            "enable_retriever": False,
            "enable_llm": False,
        }
    )
    graph = build_graph(settings)
    assert graph is not None

    from agents.classifier import classify_intent
    from agents.router_semantic import SemanticRouter

    SemanticRouter._instance = None
    result = classify_intent("hello, what is the capital of France?", settings)
    assert result.domain in {"general", "unknown", "medical", "legal"}

    # Even a direct predict call must no-op without touching ST when env is false.
    from agents.router_semantic import get_semantic_router

    assert get_semantic_router().predict("dengue symptoms") is None
    assert hits == []


def test_retriever_initialize_skips_heavy_imports_when_disabled(monkeypatch) -> None:
    _purge_agent_modules(monkeypatch)
    hits = _install_heavy_import_traps(monkeypatch)
    monkeypatch.setenv("ENABLE_RETRIEVER", "false")

    from agents.retriever import Retriever

    Retriever._instance = None
    retriever = Retriever()
    retriever._initialize()
    assert retriever._ready is False
    assert hits == []
