from __future__ import annotations

from openai import OpenAI
from core.config import Settings
from core.state import AgentResponse

def call_llm(
    query: str, 
    system_prompt: str, 
    settings: Settings, 
    temperature: float = 0.2, 
    max_tokens: int = 512
) -> str:
    """Shared helper to call OpenAI LLM."""
    client = OpenAI(api_key=settings.openai_api_key)
    
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
