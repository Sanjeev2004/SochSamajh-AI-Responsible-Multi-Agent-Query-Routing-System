from __future__ import annotations

from dataclasses import replace

from agents.retriever import Retriever
from core.config import Settings
from services import retrieval_service


SETTINGS = Settings.load()


def test_retrieval_service_respects_disabled_setting(monkeypatch) -> None:
    called = {"value": False}

    def fake_retrieve_context(*args, **kwargs) -> str:
        called["value"] = True
        return "should not be used"

    monkeypatch.setattr(retrieval_service, "retrieve_context", fake_retrieve_context)
    disabled_settings = replace(SETTINGS, enable_retriever=False)

    assert retrieval_service.get_retrieved_context("test query", "medical", disabled_settings) == ""
    assert called["value"] is False


def test_retrieval_service_uses_retriever_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(retrieval_service, "retrieve_context", lambda query, domain: f"{domain}:{query}")
    enabled_settings = replace(SETTINGS, enable_retriever=True)

    assert retrieval_service.get_retrieved_context("test query", "legal", enabled_settings) == "legal:test query"


def test_retriever_falls_back_to_file_based_context() -> None:
    retriever = Retriever()
    retriever._ready = False
    retriever._init_attempted = True
    retriever._fallback_chunks = []

    context = retriever.get_relevant_context("What are symptoms of diabetes?", domain="medical")

    assert "Source (" in context
    assert "diabetes" in context.lower()
