from __future__ import annotations

from openai import OpenAI
from core.config import Settings


def call_llm(
    query: str, 
    system_prompt: str, 
    settings: Settings, 
    temperature: float = 0.2, 
    max_tokens: int = 512
) -> str:
    """Shared helper to call OpenAI LLM."""
    if not settings.enable_llm:
        raise RuntimeError("LLM calls are disabled. Set ENABLE_LLM=true to use the OpenAI API.")

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
    except TypeError as exc:
        if "proxies" in str(exc):
            raise RuntimeError(
                "OpenAI client initialization failed because this Python environment has an incompatible "
                "openai/httpx stack. Use backend\\venv\\Scripts\\python.exe or reinstall backend requirements."
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
