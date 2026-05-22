from __future__ import annotations

from collections.abc import Generator

from openai import OpenAI
from core.config import Settings


def create_llm_client(settings: Settings) -> OpenAI:
    client_kwargs = {
        "api_key": settings.openai_api_key,
        "timeout": settings.openai_timeout_seconds,
        "max_retries": settings.openai_max_retries,
    }
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**client_kwargs)


def _check_llm_ready(settings: Settings) -> None:
    """Raise a clear RuntimeError if the LLM cannot be called."""
    if not settings.enable_llm:
        raise RuntimeError("LLM calls are disabled. Set ENABLE_LLM=true to enable.")
    if not settings.openai_api_key:
        key_name = "GROQ_API_KEY" if settings.llm_provider == "groq" else "OPENAI_API_KEY"
        raise RuntimeError(f"{key_name} is not configured.")


def call_llm(
    query: str,
    system_prompt: str,
    settings: Settings,
    temperature: float = 0.2,
    max_tokens: int = 512,
) -> str:
    """Blocking LLM call — returns the full response as a string."""
    _check_llm_ready(settings)
    try:
        client = create_llm_client(settings)
    except TypeError as exc:
        if "proxies" in str(exc):
            raise RuntimeError(
                "OpenAI client initialization failed due to an incompatible openai/httpx stack. "
                "Use backend\\venv\\Scripts\\python.exe or reinstall backend requirements."
            ) from exc
        raise

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]
    response = client.chat.completions.create(
        messages=messages,
        model=settings.openai_model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()


def stream_llm(
    query: str,
    system_prompt: str,
    settings: Settings,
    temperature: float = 0.2,
    max_tokens: int = 512,
) -> Generator[str, None, None]:
    """Streaming LLM call — yields text chunks as they arrive from the API.

    Usage::

        for chunk in stream_llm(query, prompt, settings):
            print(chunk, end="", flush=True)
    """
    _check_llm_ready(settings)
    try:
        client = create_llm_client(settings)
    except TypeError as exc:
        if "proxies" in str(exc):
            raise RuntimeError(
                "OpenAI client initialization failed due to an incompatible openai/httpx stack."
            ) from exc
        raise

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]
    with client.chat.completions.stream(
        messages=messages,
        model=settings.openai_model,
        max_tokens=max_tokens,
        temperature=temperature,
    ) as stream:
        for text_chunk in stream.text_stream:
            if text_chunk:
                yield text_chunk
