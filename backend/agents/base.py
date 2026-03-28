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
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )
    
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
