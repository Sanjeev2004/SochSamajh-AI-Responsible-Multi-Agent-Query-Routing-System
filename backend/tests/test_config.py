from __future__ import annotations

from core.config import Settings


def test_groq_provider_uses_groq_key_model_and_base_url(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test-key")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    settings = Settings.load()

    assert settings.llm_provider == "groq"
    assert settings.openai_api_key == "gsk-test-key"
    assert settings.openai_model == "llama-3.3-70b-versatile"
    assert settings.openai_base_url == "https://api.groq.com/openai/v1"


def test_openai_provider_remains_default(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    settings = Settings.load()

    assert settings.llm_provider == "openai"
    assert settings.openai_api_key == "sk-test-key"
    assert settings.openai_model == "gpt-4o-mini"
