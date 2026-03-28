from __future__ import annotations

import re
from typing import Iterable

from langsmith import traceable

from core.config import Settings, logger
from core.state import ClassificationOutput

# from agents.router_semantic import semantic_router  # Temporarily disabled

SELF_HARM_KEYWORDS = frozenset([
    "kill myself",
    "suicide",
    "end my life",
    "ending everything",
    "do not want to live anymore",
    "don't want to live anymore",
    "self harm",
    "self-harm",
    "hurt myself",
    "hurt myself tonight",
    "want to die",
    "overdose",
    "kill myself tonight",
    "fastest way to kill myself",
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
    "forge a signature",
    "forged signature",
    "counterfeit",
    "blackmail",
    "hack my neighbor's wi-fi",
    "hack my neighbor's wifi",
    "how to hack",
    "buy drugs",
    "break into a locked phone",
    "destroy evidence",
])

MEDICAL_HINTS = frozenset([
    "symptom",
    "symptoms",
    "diagnose",
    "side effects",
    "pain",
    "fever",
    "treatment",
    "medicine",
    "doctor",
    "medical",
    "hospital",
    "clinic",
    "health",
    "care",
])

LEGAL_HINTS = frozenset([
    "contract",
    "lawsuit",
    "liability",
    "legal",
    "attorney",
    "court",
    "jurisdiction",
    "lawyer",
    "rights",
    "complaint",
    "consumer",
    "notice",
    "police",
    "bail",
])

VAGUE_QUERY_TERMS = frozenset([
    "help me with my issue",
    "i have a problem and need advice",
    "can you tell me what to do",
    "i need urgent guidance",
    "please help me figure this out",
    "what should be my next step",
    "i am confused and need direction",
    "can you explain my situation",
    "i do not know where to start",
    "mujhe samajh nahi aa raha kya karun",
    "kya karun",
    "guide karo",
    "need advice",
])

MEDICAL_KEYWORDS = frozenset([
    "symptom",
    "symptoms",
    "diabetes",
    "pain",
    "fever",
    "treatment",
    "disease",
    "health",
    "doctor",
    "medicine",
    "medical",
    "hospital",
    "clinic",
    "healthcare",
    "medical care",
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
    "migraine",
    "asthma",
    "thyroid",
    "anemia",
    "acid reflux",
    "vitamin d",
    "pcos",
    "panic attack",
    "depression",
    "seizure",
    "snake bite",
    "burn injury",
    "dehydration",
    "heat stroke",
    "rabies",
    "tb",
    "tuberculosis",
    "food poisoning",
    "blood sugar",
    "head injury",
    "cut",
    "poison",
    "cleaner",
    "child",
    "bukhar",
    "gala dard",
    "chest tightness",
    "numbness",
    "drooping",
    "tightness",
    "shortness of breath",
    "emergency room",
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
    "tenant",
    "rent",
    "agreement",
    "legal notice",
    "employment law",
    "domestic violence",
    "evidence",
    "consent",
    "negligence",
    "medical certificate",
    "bail",
    "consumer",
    "complaint",
    "legal heir",
    "succession",
    "rti",
    "challan",
    "cybercrime",
    "arrest",
    "harassment",
    "injunction",
    "mediation",
    "police notice",
    "maintenance",
    "wrongful termination",
    "termination",
    "small claims",
    "dispute",
    "disputes",
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
    "bail",
    "rent",
    "consumer",
    "rti",
    "cybercrime",
    "arrest",
    "harassment",
    "maintenance",
    "wrongful termination",
    "termination",
    "small claims",
    "dispute",
])

LEGAL_REMEDY_TERMS = frozenset([
    "compensation",
    "medical negligence",
    "malpractice",
    "consumer court",
    "legal complaint",
    "legal notice",
    "step by step",
    "what can i do",
    "what should i do now",
    "documents needed",
    "where to file",
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
    "migraine",
    "asthma",
    "thyroid",
    "anemia",
    "acid reflux",
    "pcos",
    "depression",
    "panic",
    "dehydration",
    "heat stroke",
    "rabies",
    "tuberculosis",
    "gala dard",
    "shortness of breath",
    "numbness",
    "drooping",
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
    "bail": 5,
    "rent agreement": 5,
    "consumer": 4,
    "rti": 4,
    "legal heir": 5,
    "succession": 5,
    "cybercrime": 4,
    "challan": 4,
    "arrest": 5,
    "injunction": 4,
    "mediation": 4,
    "harassment": 4,
    "police notice": 5,
    "maintenance": 4,
    "wrongful termination": 6,
    "small claims": 5,
    "dispute": 3,
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
    "migraine": 4,
    "asthma": 4,
    "thyroid": 4,
    "anemia": 4,
    "acid reflux": 4,
    "pcos": 5,
    "depression": 4,
    "panic": 3,
    "seizure": 5,
    "snake bite": 5,
    "burn injury": 5,
    "dehydration": 4,
    "rabies": 5,
    "tuberculosis": 4,
    "shortness of breath": 5,
    "chest tightness": 4,
    "numbness": 4,
    "drooping": 5,
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
    "stroke symptoms",
    "heart attack",
    "face is drooping",
    "arm numbness",
    "severe headache",
    "cannot speak clearly",
    "deep cut",
    "a lot of bleeding",
    "drank floor cleaner",
    "poison",
    "domestic violence",
    "police picked up",
    "dog bite",
    "turning blue",
    "not waking up",
    "seizure",
    "snake bite",
    "burn injury",
    "black stool",
    "chemical splash",
    "stalked",
    "kidnap",
    "threatening",
    "threatened",
    "assault",
    "suspicious death",
])

MEDICAL_URGENCY_TERMS = frozenset([
    "chest tightness",
    "chest me tightness",
    "left arm pain",
    "shortness of breath",
    "arm numbness",
    "face drooping",
    "slurred speech",
    "breathing difficulty",
    "saans lene mein dikkat",
    "saans nahi aa rahi",
    "confusion",
    "fainting",
    "pregnancy bleeding",
    "bleeding ho rahi",
    "pregnancy me bleeding",
    "heavy bleeding",
])

AMBIGUOUS_CROSS_DOMAIN_TERMS = frozenset([
    "not sure where to start",
    "both legal and medical",
    "legal and medical help",
    "medical or legal",
    "which kind of help",
    "doctor or lawyer",
    "lawyer or doctor",
])

LEGAL_HIGH_RISK_TERMS = frozenset([
    "domestic violence",
    "assault",
    "blackmail",
    "kidnap",
    "stalked",
    "threatening",
    "threatened",
    "police picked up",
    "wrongful arrest",
])

LEGAL_PRACTICAL_STEP_TERMS = frozenset([
    "next legal step",
    "what should i do legally",
    "what documents",
    "process",
    "procedure",
    "how do i file",
    "kaise file",
    "kaise karu",
    "legal notice",
    "complaint",
    "fir",
    "consumer court",
])

URGENT_INTENT_TERMS = frozenset([
    "urgent",
    "emergency",
    "immediately",
    "asap",
    "right now",
    "abhi",
    "jaldi",
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
    "doctor",
    "hospital",
    "lawyer",
    "consumer",
    "bail",
    "notice",
    "complaint",
    "rights",
    "asthma",
    "pregnancy",
    "wrongful termination",
    "small claims",
])


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    text_lower = text.lower()
    return any(_phrase_in_text(text_lower, phrase) for phrase in phrases)


def _score_matches(text: str, phrases: Iterable[str]) -> int:
    text_lower = text.lower()
    return sum(1 for phrase in phrases if _phrase_in_text(text_lower, phrase))


def _weighted_score(text: str, weighted_phrases: dict[str, int]) -> int:
    text_lower = text.lower()
    return sum(weight for phrase, weight in weighted_phrases.items() if _phrase_in_text(text_lower, phrase))


def _phrase_in_text(text: str, phrase: str) -> bool:
    escaped_phrase = re.escape(phrase.lower()).replace(r"\ ", r"\s+")
    pattern = rf"(?<!\w){escaped_phrase}(?!\w)"
    return re.search(pattern, text) is not None


def _is_vague_query(text: str) -> bool:
    text_lower = text.lower().strip()
    normalized_text = re.sub(r"[^a-z0-9\s]", "", text_lower)
    if text_lower in VAGUE_QUERY_TERMS:
        return True
    if normalized_text in VAGUE_QUERY_TERMS:
        return True

    generic_terms = ("help", "problem", "issue", "guidance", "situation", "advice", "kya karun", "guide")
    word_count = len(normalized_text.split())
    if word_count <= 6 and any(term in normalized_text for term in generic_terms):
        return True

    # Slightly longer but still non-specific prompts should be routed as unknown.
    if word_count <= 12 and any(term in normalized_text for term in ("next step", "urgent guidance", "figure this out")):
        return True

    return False


@traceable(name="pre_screen")
def pre_screen_query(query: str) -> ClassificationOutput | None:
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
    query_lower = query.lower()

    medical_score = _score_matches(query_lower, MEDICAL_KEYWORDS)
    legal_score = _score_matches(query_lower, LEGAL_KEYWORDS)
    medical_priority_score = _score_matches(query_lower, MEDICAL_PRIORITY_TERMS)
    legal_priority_score = _score_matches(query_lower, LEGAL_PRIORITY_TERMS)
    medical_weighted_score = _weighted_score(query_lower, MEDICAL_WEIGHTED_TERMS)
    legal_weighted_score = _weighted_score(query_lower, LEGAL_WEIGHTED_TERMS)
    urgent_intent = _contains_any(query_lower, URGENT_INTENT_TERMS)
    has_legal_remedy_intent = _contains_any(query_lower, LEGAL_REMEDY_TERMS)

    if _contains_any(query_lower, LEGAL_PRACTICAL_STEP_TERMS):
        legal_weighted_score += 2

    has_medical = medical_score > 0 or medical_priority_score > 0 or medical_weighted_score > 0
    has_legal = legal_score > 0 or legal_priority_score > 0 or legal_weighted_score > 0
    is_vague = _is_vague_query(query_lower)
    has_cross_domain_ambiguity = _contains_any(query_lower, AMBIGUOUS_CROSS_DOMAIN_TERMS)

    domain = None
    reasoning = "Keyword-based classification"

    if has_cross_domain_ambiguity and has_medical and has_legal:
        domain = "unknown"
        reasoning = "Explicitly mixed medical/legal query requesting routing help"

    if has_legal and has_legal_remedy_intent and legal_weighted_score >= medical_weighted_score:
        domain = "legal"
        reasoning = "Legal remedy terms indicate practical legal intent"

    # Ambiguous mixed-domain prompts should not be over-confidently routed.
    if domain is None and has_medical and has_legal:
        weighted_gap = abs(medical_weighted_score - legal_weighted_score)
        priority_gap = abs(medical_priority_score - legal_priority_score)
        if weighted_gap <= 2 and priority_gap <= 1:
            domain = "unknown"
            reasoning = (
                "Ambiguous cross-domain query with similar medical/legal evidence "
                f"(weighted_gap={weighted_gap}, priority_gap={priority_gap})"
            )

    if domain is None and legal_weighted_score > medical_weighted_score:
        domain = "legal"
        reasoning = f"Weighted legal intent heuristic (legal={legal_weighted_score}, medical={medical_weighted_score})"
    elif domain is None and medical_weighted_score > legal_weighted_score:
        domain = "medical"
        reasoning = f"Weighted medical intent heuristic (medical={medical_weighted_score}, legal={legal_weighted_score})"
    elif domain is None and legal_priority_score > medical_priority_score:
        domain = "legal"
        reasoning = f"Priority legal heuristic (legal={legal_priority_score}, medical={medical_priority_score})"
    elif domain is None and medical_priority_score > legal_priority_score:
        domain = "medical"
        reasoning = f"Priority medical heuristic (medical={medical_priority_score}, legal={legal_priority_score})"
    elif domain is None and legal_score > medical_score:
        domain = "legal"
        reasoning = f"Legal keyword match (legal={legal_score}, medical={medical_score})"
    elif domain is None and medical_score > legal_score:
        domain = "medical"
        reasoning = f"Medical keyword match (medical={medical_score}, legal={legal_score})"
    elif domain is None and (len(query.strip()) < 10 or is_vague):
        domain = "unknown"

    if domain is None and is_vague and max(medical_weighted_score, legal_weighted_score, medical_score, legal_score) <= 1:
        domain = "unknown"
        reasoning = "Vague query with low-confidence domain evidence"

    if not domain or (domain == "unknown" and not is_vague and (has_medical or has_legal)):
        logger.info("Keyword match inconclusive. Semantic routing temporarily disabled.")
        if not domain:
            domain = "general"

    if not domain:
        domain = "general"

    has_high_risk = _contains_any(query_lower, HIGH_RISK_KEYWORDS)
    medical_urgent = _contains_any(query_lower, MEDICAL_URGENCY_TERMS)
    legal_high_risk = _contains_any(query_lower, LEGAL_HIGH_RISK_TERMS)
    has_medium_risk = _contains_any(query_lower, MEDIUM_RISK_KEYWORDS)

    if medical_urgent and domain in {"medical", "unknown"}:
        has_high_risk = True
    if legal_high_risk and domain in {"legal", "unknown"}:
        has_high_risk = True
    if urgent_intent and (has_medical or has_legal) and not has_high_risk:
        has_medium_risk = True

    if urgent_intent and domain == "medical" and medical_weighted_score >= 3:
        has_high_risk = True

    if domain == "unknown":
        has_medium_risk = urgent_intent

    if has_high_risk:
        risk_level = "high"
    elif has_medium_risk:
        risk_level = "medium"
    else:
        risk_level = "low"

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
