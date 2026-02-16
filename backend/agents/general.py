from __future__ import annotations

from langsmith import traceable
from openai import OpenAI

from core.config import Settings
from core.state import AgentResponse, ClassificationOutput

COMMON_GENERAL_INFO = {
    "bread": "To bake basic bread: Mix 3 cups flour, 2 tsp yeast, 1 tbsp sugar, 1 tsp salt with 1 cup warm water and 2 tbsp oil. Knead for 10 minutes, let rise 1 hour until doubled. Shape, let rise 30 minutes. Bake at 375 F (190 C) for 25-30 minutes until golden brown. Enjoy fresh!",
    "pasta": "To cook pasta: Boil 4-6 quarts of salted water per pound of pasta. Add pasta and stir occasionally. Cook for 8-12 minutes (check package) until al dente (firm to bite). Drain (save some pasta water for sauce). Toss with your favorite sauce and serve immediately.",
    "coffee": "For great coffee: Use fresh, quality beans ground just before brewing. Standard ratio is 1-2 tablespoons of grounds per 6 oz water. Water temperature should be 195-205 F (90-96 C). Brew time: 4-5 minutes for drip, 2-4 minutes for French press. Clean your equipment regularly.",
}


@traceable(name="general_agent")
def run_general_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    try:
        client = OpenAI(api_key=settings.openai_api_key)

        messages = [
            {
                "role": "system",
                "content": "You are a helpful general assistant. Answer clearly and safely. If user asks for medical or legal advice, keep it general and encourage professional help.",
            },
            {"role": "user", "content": query},
        ]

        response = client.chat.completions.create(
            messages=messages,
            model=settings.openai_model,
            max_tokens=512,
            temperature=0.3,
        )

        return AgentResponse(content=(response.choices[0].message.content or "").strip(), disclaimers=[], safety_notes=[])
    except Exception:
        query_lower = query.lower()
        for topic, info in COMMON_GENERAL_INFO.items():
            if topic in query_lower:
                return AgentResponse(content=info, disclaimers=[], safety_notes=[])

        fallback = (
            "I'm here to help with general information and questions. Could you provide more details about "
            "what you'd like to know? I can assist with various topics including cooking, technology, "
            "general knowledge, and more."
        )
        return AgentResponse(content=fallback, disclaimers=[], safety_notes=[])
