from __future__ import annotations

from typing import Iterable
from huggingface_hub import InferenceClient
from langsmith import traceable
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from core.config import Settings, logger
from core.state import ClassificationOutput

SELF_HARM_KEYWORDS = [
    "kill myself",
    "suicide",
    "end my life",
    "self harm",
    "self-harm",
    "hurt myself",
    "want to die",
    "overdose",
]

ILLEGAL_KEYWORDS = [
    "evade taxes",
    "tax fraud",
    "launder money",
    "forge",
    "counterfeit",
    "blackmail",
    "how to hack",
    "buy drugs",
]

MEDICAL_HINTS = ["symptom", "diagnose", "side effects", "pain", "fever", "treatment", "medicine"]
LEGAL_HINTS = ["contract", "lawsuit", "liability", "legal", "attorney", "court", "jurisdiction"]


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in phrases)


@traceable(name="pre_screen")
def pre_screen_query(query: str) -> ClassificationOutput | None:
    if _contains_any(query, SELF_HARM_KEYWORDS):
        return ClassificationOutput(
            domain="medical",
            risk_level="high",
            needs_disclaimer=True,
            self_harm=True,
            illegal_request=False,
            reasoning="Pre-screen detected self-harm intent.",
        )

    if _contains_any(query, ILLEGAL_KEYWORDS):
        return ClassificationOutput(
            domain="legal",
            risk_level="high",
            needs_disclaimer=True,
            self_harm=False,
            illegal_request=True,
            reasoning="Pre-screen detected illegal intent.",
        )

    return None


@traceable(name="intent_risk_classifier")
def classify_intent(query: str, settings: Settings) -> ClassificationOutput:
    # Simple keyword-based classification for reliability
    query_lower = query.lower()
    
    # Detect domain
    medical_keywords = ["symptom", "diabetes", "pain", "fever", "treatment", "disease", "health", "doctor", "medicine", "sick"]
    legal_keywords = ["contract", "lawsuit", "law", "legal", "attorney", "court", "liability", "jurisdiction", "rights"]
    
    has_medical = any(kw in query_lower for kw in medical_keywords)
    has_legal = any(kw in query_lower for kw in legal_keywords)
    
    if has_medical:
        domain = "medical"
    elif has_legal:
        domain = "legal"
    elif len(query.strip()) < 10:
        domain = "unknown"
    else:
        domain = "general"
    
    # Detect risk level
    high_risk_keywords = ["kill", "die", "suicide", "hurt", "harm", "emergency", "urgent", "severe", "chest pain", "blood"]
    medium_risk_keywords = ["pain", "sick", "worried", "concerned", "problem"]
    
    has_high_risk = any(kw in query_lower for kw in high_risk_keywords)
    has_medium_risk = any(kw in query_lower for kw in medium_risk_keywords)
    
    if has_high_risk:
        risk_level = "high"
    elif has_medium_risk:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Needs disclaimer
    needs_disclaimer = domain in ["medical", "legal"]
    
    return ClassificationOutput(
        domain=domain,
        risk_level=risk_level,
        needs_disclaimer=needs_disclaimer,
        self_harm=_contains_any(query, SELF_HARM_KEYWORDS),
        illegal_request=_contains_any(query, ILLEGAL_KEYWORDS),
        reasoning=f"Keyword-based classification: domain={domain}, risk={risk_level}",
    )

    if result.domain == "general" and _contains_any(query, MEDICAL_HINTS + LEGAL_HINTS):
        logger.warning("Possible misclassification: heuristic suggests medical/legal")

    return result
