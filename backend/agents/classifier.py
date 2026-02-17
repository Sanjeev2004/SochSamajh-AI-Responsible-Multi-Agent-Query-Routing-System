from __future__ import annotations

from typing import Iterable
from langsmith import traceable

from core.config import Settings, logger
from core.state import ClassificationOutput
# from agents.router_semantic import semantic_router  # Temporarily disabled

SELF_HARM_KEYWORDS = frozenset([
    "kill myself",
    "suicide",
    "end my life",
    "self harm",
    "self-harm",
    "hurt myself",
    "want to die",
    "overdose",
])

ILLEGAL_KEYWORDS = frozenset([
    "evade taxes",
    "tax fraud",
    "launder money",
    "forge",
    "counterfeit",
    "blackmail",
    "how to hack",
    "buy drugs",
])

MEDICAL_HINTS = frozenset(["symptom", "diagnose", "side effects", "pain", "fever", "treatment", "medicine"])
LEGAL_HINTS = frozenset(["contract", "lawsuit", "liability", "legal", "attorney", "court", "jurisdiction"])

MEDICAL_KEYWORDS = frozenset([
    "symptom",
    "diabetes",
    "pain",
    "fever",
    "treatment",
    "disease",
    "health",
    "doctor",
    "medicine",
    "sick",
    "hurt",
    "tummy",
    "stomach",
    "abdomen",
    "nausea",
    "vomit",
])

LEGAL_KEYWORDS = frozenset(["contract", "lawsuit", "law", "legal", "attorney", "court", "liability", "jurisdiction", "rights"])

HIGH_RISK_KEYWORDS = frozenset([
    "chest pain",
    "difficulty breathing",
    "can't breathe",
    "cannot breathe",
    "severe bleeding",
    "coughing blood",
    "blood in vomit",
    "blood in stool",
    "passed out",
    "unconscious",
    "stroke",
    "heart attack",
])

MEDIUM_RISK_KEYWORDS = frozenset(["pain", "sick", "worried", "concerned", "problem"])


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    """Check if text contains any of the given phrases (case-insensitive).
    
    Args:
        text: The text to search in
        phrases: Iterable of phrases to check for
        
    Returns:
        bool: True if any phrase is found in text
    """
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in phrases)


@traceable(name="pre_screen")
def pre_screen_query(query: str) -> ClassificationOutput | None:
    """Detect self-harm and illegal intent before processing.
    
    This is the first-stage safety check. If a query contains indicators
    of self-harm or illegal intent, it returns immediately with a high-risk
    classification, preventing the query from entering the standard pipeline.
    
    Args:
        query: The user's query string
        
    Returns:
        ClassificationOutput with safety flags if harmful intent detected,
        None otherwise
        
    Notes:
        - Uses keyword-based pattern matching for reliability
        - Intentionally conservative (prefer false positives to false negatives)
        - Decorated with @traceable for LangSmith observability
    """
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
    """Classify query intent across multiple dimensions.
    
    Analyzes the query to extract:
      1. Domain (medical/legal/general/unknown)
      2. Risk level (low/medium/high)
      3. Need for disclaimers
      4. Self-harm and illegal intent indicators
      
    Uses a hybrid approach:
    1. Fast keyword matching (high precision)
    2. Semantic embedding search (fallback for high recall)
    
    Args:
        query: The user's query string
        settings: Application settings
        
    Returns:
        ClassificationOutput with comprehensive classification results
    """
    # Simple keyword-based classification for reliability
    query_lower = query.lower()

    # Detect domain
    has_medical = any(kw in query_lower for kw in MEDICAL_KEYWORDS)
    has_legal = any(kw in query_lower for kw in LEGAL_KEYWORDS)

    domain = None
    reasoning = "Keyword-based classification"

    if has_medical:
        domain = "medical"
    elif has_legal:
        domain = "legal"
    elif len(query.strip()) < 10:
        domain = "unknown"
        
    # Hybrid Fallback: Use Semantic Router if keyword match is weak
    if not domain or domain == "unknown" or (not has_medical and not has_legal):
        logger.info("Keyword match inconclusive. Semantic routing temporarily disabled.")
        # semantic_domain = semantic_router.predict(query)  # Temporarily disabled
        # if semantic_domain:
        #     domain = semantic_domain
        #     reasoning = f"Semantic routing (embedding similarity). Initial keyword result was inconclusive."
        # elif not domain:
        if not domain:
             domain = "general"

    # Default to general if still nothing
    if not domain:
        domain = "general"

    # Detect risk level
    has_high_risk = any(kw in query_lower for kw in HIGH_RISK_KEYWORDS)
    has_medium_risk = any(kw in query_lower for kw in MEDIUM_RISK_KEYWORDS)

    if has_high_risk:
        risk_level = "high"
    elif has_medium_risk:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Needs disclaimer
    needs_disclaimer = domain in ["medical", "legal"]

    result = ClassificationOutput(
        domain=domain,
        risk_level=risk_level,
        needs_disclaimer=needs_disclaimer,
        self_harm=_contains_any(query, SELF_HARM_KEYWORDS),
        illegal_request=_contains_any(query, ILLEGAL_KEYWORDS),
        reasoning=f"{reasoning}: domain={domain}, risk={risk_level}",
    )

    if result.domain == "general" and _contains_any(query, MEDICAL_HINTS | LEGAL_HINTS):
        logger.warning("Possible misclassification: heuristic suggests medical/legal")

    return result
