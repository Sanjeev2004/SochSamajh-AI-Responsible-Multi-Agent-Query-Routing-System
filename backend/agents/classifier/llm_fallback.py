"""
classifier/llm_fallback.py
LLM-based semantic classification used as a cascade fallback
when heuristic confidence is below the threshold.
"""
from __future__ import annotations

from core.config import Settings, logger
from core.state import ClassificationOutput, Domain, RiskLevel

# Lazy-initialised chain — avoids heavy imports at module load time.
_llm_chain = None


def _get_llm_chain(settings: Settings):
    global _llm_chain
    if _llm_chain is None:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import PromptTemplate
            from langchain_core.output_parsers import JsonOutputParser
            from pydantic import BaseModel, Field as PydanticField
        except ModuleNotFoundError:
            logger.warning("langchain_openai unavailable; using direct OpenAI fallback for classification")

            class _DirectChain:
                def invoke(self, payload: dict[str, str]) -> dict[str, object]:
                    from openai import OpenAI

                    client = OpenAI(
                        api_key=settings.openai_api_key,
                        base_url=settings.openai_base_url,
                        timeout=settings.openai_timeout_seconds,
                        max_retries=settings.openai_max_retries,
                    )
                    response = client.chat.completions.create(
                        model=settings.openai_model or "gpt-4o",
                        temperature=0.0,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert intent router for an AI assistant. "
                                    "Classify the user query into medical, legal, or general, "
                                    "and return JSON with domain, risk_level, reasoning, and confidence."
                                ),
                            },
                            {"role": "user", "content": payload["query"]},
                        ],
                    )
                    content = response.choices[0].message.content or "{}"
                    import json

                    return json.loads(content)

            _llm_chain = _DirectChain()
            return _llm_chain

        class LLMClassificationOutput(BaseModel):
            domain: Domain = PydanticField(description="One of: 'medical', 'legal', 'general'")
            risk_level: RiskLevel = PydanticField(description="One of: 'low', 'medium', 'high'")
            reasoning: str = PydanticField(description="Brief reasoning")
            confidence: float = PydanticField(description="Confidence between 0 and 1")

        llm = ChatOpenAI(
            model=settings.openai_model or "gpt-4o",
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.0,
            max_retries=1,
        )
        parser = JsonOutputParser(pydantic_object=LLMClassificationOutput)
        prompt = PromptTemplate(
            template=(
                "You are an expert intent router for an AI assistant.\n"
                "Classify the following user query into one of three domains: "
                "'medical', 'legal', or 'general'.\n"
                "Also assess the risk_level ('low', 'medium', 'high') based on "
                "urgency or potential harm.\n\n"
                'Query: "{query}"\n\n'
                "Respond with JSON only, matching this schema:\n"
                "{format_instructions}\n"
            ),
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        _llm_chain = prompt | llm | parser
    return _llm_chain


def llm_classify(
    query: str,
    settings: Settings,
    base_result: ClassificationOutput,
) -> ClassificationOutput:
    """Attempt to improve classification using an LLM.

    Falls back to `base_result` silently on any error, preserving hard safety
    flags set by the heuristic pre-screen.
    """
    if not settings.enable_llm or not settings.openai_api_key:
        return base_result

    try:
        chain = _get_llm_chain(settings)
        res = chain.invoke({"query": query})

        return ClassificationOutput(
            domain=res["domain"],
            risk_level=res["risk_level"],
            needs_disclaimer=res["domain"] in [Domain.MEDICAL, Domain.LEGAL],
            # Safety flags are always taken from the pre-screen, never overridden
            self_harm=base_result.self_harm,
            illegal_request=base_result.illegal_request,
            reasoning=f"LLM Fallback: {res['reasoning']}",
            confidence=res["confidence"],
            triggered_terms=base_result.triggered_terms,
            alternative_domains={
                "medical": 1.0 if res["domain"] in (Domain.MEDICAL, "medical") else 0.0,
                "legal": 1.0 if res["domain"] in (Domain.LEGAL, "legal") else 0.0,
                "general": 1.0 if res["domain"] in (Domain.GENERAL, "general") else 0.0,
                "unknown": 1.0 if res["domain"] in (Domain.UNKNOWN, "unknown") else 0.0,
            },
            explanation=(
                f"Heuristic confidence was low ({base_result.confidence:.2f}), "
                "so semantic LLM routing was used."
            ),
        )
    except Exception as exc:
        logger.warning("LLM fallback classification failed: %s", exc)
        return base_result
