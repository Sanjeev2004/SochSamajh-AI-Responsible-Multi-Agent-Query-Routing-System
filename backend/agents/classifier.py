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
    "sleeping pills would end my life",
    "khud ko nuksan",
    "khud ko nuksan pahuncha",
    "mar jana chahta",
])

ILLEGAL_KEYWORDS = frozenset([
    "make a bomb",
    "bomb at home",
    "steal a car",
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
    "hypertension",
    "hba1c",
    "stroke",
    "dengue",
    "pregnancy",
    "vaccine",
    "vaccines",
    "bleeding",
    "cut",
    "poison",
    "cleaner",
    "child",
    "bukhar",
    "gala dard",
])

LEGAL_KEYWORDS = frozenset([
    "contract",
    "lawsuit",
    "law",
    "legal",
    "attorney",
    "court",
    "liability",
    "jurisdiction",
    "rights",
    "copyright",
    "employer",
    "salary",
    "fir",
    "divorce",
    "deposit",
    "landlord",
    "legal notice",
    "employment law",
    "domestic violence",
    "evidence",
    "consent",
    "negligence",
    "medical certificate",
])

LEGAL_PRIORITY_TERMS = frozenset([
    "sue",
    "lawyer",
    "attorney",
    "rights",
    "court",
    "legal",
    "illegal",
    "liability",
    "compensation",
    "contract",
    "landlord",
    "tenant",
    "divorce",
    "custody",
    "police",
    "fir",
    "complaint",
    "malpractice",
    "employer",
    "salary",
    "copyright",
    "deposit",
    "notice",
    "violence",
    "evidence",
    "employment",
    "certificate",
    "consent",
    "negligence",
])

MEDICAL_PRIORITY_TERMS = frozenset([
    "diagnosis",
    "diagnose",
    "symptoms",
    "treatment",
    "medicine",
    "doctor",
    "hospital",
    "disease",
    "fever",
    "pain",
    "breathing",
    "vomit",
    "stroke",
    "blood pressure",
    "hypertension",
    "dengue",
    "hba1c",
    "pregnancy",
    "vaccine",
    "bleeding",
    "poison",
    "cleaner",
    "bukhar",
])

LEGAL_WEIGHTED_TERMS = {
    "sue": 6,
    "lawyer": 5,
    "attorney": 5,
    "malpractice": 5,
    "rights": 3,
    "court": 3,
    "landlord": 3,
    "tenant": 3,
    "contract": 3,
    "divorce": 3,
    "custody": 3,
    "compensation": 4,
    "copyright": 4,
    "employer": 3,
    "salary": 4,
    "fir": 5,
    "deposit": 3,
    "notice": 3,
    "domestic violence": 5,
    "employment law": 5,
    "evidence": 3,
    "consent": 3,
    "negligence": 4,
    "medical certificate": 4,
}

MEDICAL_WEIGHTED_TERMS = {
    "diagnosis": 4,
    "diagnose": 4,
    "symptoms": 3,
    "fever": 3,
    "treatment": 2,
    "medicine": 2,
    "doctor": 1,
    "pain": 1,
    "vomit": 2,
    "breathing": 2,
    "hypertension": 4,
    "hba1c": 5,
    "dengue": 4,
    "pregnancy": 4,
    "vaccine": 3,
    "vaccines": 3,
    "bleeding": 4,
    "cleaner": 4,
    "poison": 4,
    "bukhar": 4,
    "gala dard": 4,
}

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
    "face is drooping",
    "cannot speak clearly",
    "deep cut",
    "a lot of bleeding",
    "drank floor cleaner",
    "poison",
    "domestic violence",
    "police picked up",
    "dog bite",
])

MEDIUM_RISK_KEYWORDS = frozenset([
    "pain",
    "sick",
    "worried",
    "concerned",
    "problem",
    "fever",
    "child",
    "pregnancy",
    "vaccine",
    "vaccines",
    "dengue",
    "landlord",
    "deposit",
    "salary",
    "divorce",
    "fir",
    "malpractice",
    "employer",
    "legal notice",
    "certificate",
    "consent",
    "negligence",
    "bukhar",
])


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


def _score_matches(text: str, phrases: Iterable[str]) -> int:
    text_lower = text.lower()
    return sum(1 for phrase in phrases if phrase in text_lower)


def _weighted_score(text: str, weighted_phrases: dict[str, int]) -> int:
    text_lower = text.lower()
    return sum(weight for phrase, weight in weighted_phrases.items() if phrase in text_lower)


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
            domain="general",
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

    # Detect domain using weighted heuristic scores rather than first-match wins.
    medical_score = _score_matches(query_lower, MEDICAL_KEYWORDS)
    legal_score = _score_matches(query_lower, LEGAL_KEYWORDS)
    medical_priority_score = _score_matches(query_lower, MEDICAL_PRIORITY_TERMS)
    legal_priority_score = _score_matches(query_lower, LEGAL_PRIORITY_TERMS)
    medical_weighted_score = _weighted_score(query_lower, MEDICAL_WEIGHTED_TERMS)
    legal_weighted_score = _weighted_score(query_lower, LEGAL_WEIGHTED_TERMS)

    has_medical = medical_score > 0
    has_legal = legal_score > 0

    domain = None
    reasoning = "Keyword-based classification"

    if legal_weighted_score > medical_weighted_score:
        domain = "legal"
        reasoning = f"Weighted legal intent heuristic (legal={legal_weighted_score}, medical={medical_weighted_score})"
    elif medical_weighted_score > legal_weighted_score:
        domain = "medical"
        reasoning = f"Weighted medical intent heuristic (medical={medical_weighted_score}, legal={legal_weighted_score})"
    elif legal_priority_score > medical_priority_score:
        domain = "legal"
        reasoning = f"Priority legal heuristic (legal={legal_priority_score}, medical={medical_priority_score})"
    elif medical_priority_score > legal_priority_score:
        domain = "medical"
        reasoning = f"Priority medical heuristic (medical={medical_priority_score}, legal={legal_priority_score})"
    elif legal_score > medical_score:
        domain = "legal"
        reasoning = f"Weighted legal keyword match (legal={legal_score}, medical={medical_score})"
    elif medical_score > legal_score:
        domain = "medical"
        reasoning = f"Weighted medical keyword match (medical={medical_score}, legal={legal_score})"
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
    if domain in {"medical", "legal"} and not has_high_risk and not has_medium_risk:
        has_medium_risk = True

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
