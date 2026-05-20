from __future__ import annotations

import math
import re
from typing import Iterable

from langsmith import traceable

from core.config import Settings, logger
from core.state import ClassificationOutput, Domain, RiskLevel


# -------------------- CONFIG / CONSTANTS --------------------

MAX_QUERY_LENGTH = 2000  # prevent pathological long inputs


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
    # Hindi / Hinglish variants
    "khud ko nuksan",
    "khud ko nuksan pahuncha",
    "mar jana chahta",
    "marna chahta hoon",
    "jeena nahi chahta",
    "zindagi khatam karna chahta",
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
    "mental health",
    "anxiety",
    "anxious",
    "stress",
    "stressed",
    "burnout",
    "overwhelmed",
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
    "panic",
    "depression",
    "anxiety",
    "anxious",
    "stress",
    "stressed",
    "burnout",
    "overwhelmed",
    "mental health",
    "emotional exhaustion",
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
    # extra Hinglish
    "dard ho raha hai",
    "tabiyat theek nahi",
    "ul­ti aa rahi",
    "chakkar aa rahe",
    "naak band",
    "khansi",
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
    # common Hinglish context
    "naukri se nikala",
    "kiraaya",
    "kiraya",
    "mujhe dhoka diya",
])

# Future: if you add a financial agent, you already have signals:
FINANCIAL_KEYWORDS = frozenset([
    "loan",
    "emi",
    "credit card",
    "bank fraud",
    "upi fraud",
    "insurance claim",
    "mutual fund",
    "tax return",
    "itr",
    "investment",
    "stock market",
    "demat",
    "sebi",
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
    "hba1c",
    "dengue",
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
    "panic attack",
    "anxiety",
    "anxious",
    "stress",
    "stressed",
    "burnout",
    "overwhelmed",
    "mental health",
    "dehydration",
    "heat stroke",
    "rabies",
    "tuberculosis",
    "gala dard",
    "shortness of breath",
    "numbness",
    "drooping",
])

LEGAL_WEIGHTED_TERMS: dict[str, int] = {
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

MEDICAL_WEIGHTED_TERMS: dict[str, int] = {
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
    "panic attack": 4,
    "anxiety": 4,
    "anxious": 4,
    "stress": 3,
    "stressed": 3,
    "burnout": 3,
    "overwhelmed": 3,
    "mental health": 4,
    "emotional exhaustion": 4,
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

# Simple typo correction map to improve recall
TYPO_CORRECTIONS: dict[str, str] = {
    "symtoms": "symptoms",
    "symtpoms": "symptoms",
    "lawer": "lawyer",
    "attourney": "attorney",
    "docter": "doctor",
    "hospitl": "hospital",
    "emergancy": "emergency",
    "divorc": "divorce",
    "vaccin": "vaccine",
}

NEGATION_PREFIXES = (
    "not ",
    "don't ",
    "doesn't ",
    "no ",
    "never ",
    "without ",
    "avoid ",
    "stop ",
    "stopped ",
)


# -------------------- HELPER FUNCTIONS --------------------


def _correct_typos(text: str) -> str:
    """Very lightweight token-level typo correction."""
    words = text.split()
    corrected = [TYPO_CORRECTIONS.get(w.lower(), w) for w in words]
    return " ".join(corrected)


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    text_lower = text.lower()
    return any(_phrase_in_text(text_lower, phrase) for phrase in phrases)


def _score_matches(text: str, phrases: Iterable[str]) -> int:
    text_lower = text.lower()
    return sum(
        1 for phrase in phrases 
        if _phrase_in_text(text_lower, phrase) 
        and not _is_negated(text_lower, phrase)
    )


def _is_negated(text_lower: str, phrase: str) -> bool:
    """Check if a phrase appears in the scope of a negation word."""
    idx = text_lower.find(phrase)
    if idx == -1:
        return False
    window = text_lower[max(0, idx - 20) : idx]
    return any(neg in window for neg in NEGATION_PREFIXES)


def _weighted_score(text: str, weighted_phrases: dict[str, int]) -> int:
    text_lower = text.lower()
    total = 0
    for phrase, weight in weighted_phrases.items():
        if _phrase_in_text(text_lower, phrase) and not _is_negated(text_lower, phrase):
            total += weight
    return total


def _matched_terms(text: str, phrases: Iterable[str], limit: int = 8) -> list[str]:
    text_lower = text.lower()
    matches = [phrase for phrase in phrases if _phrase_in_text(text_lower, phrase)]
    return sorted(matches, key=lambda phrase: (-len(phrase), phrase))[:limit]


def _phrase_in_text(text: str, phrase: str) -> bool:
    escaped_phrase = re.escape(phrase.lower()).replace(r"\ ", r"\s+")
    pattern = rf"(?<!\w){escaped_phrase}(?!\w)"
    return re.search(pattern, text) is not None


def _is_vague_query(text: str) -> bool:
    text_lower = text.lower().strip()
    normalized_text = re.sub(r"[^a-z0-9\s]", "", text_lower)

    if text_lower in VAGUE_QUERY_TERMS or normalized_text in VAGUE_QUERY_TERMS:
        return True

    generic_terms = ("help", "problem", "issue", "guidance", "situation", "advice", "kya karun", "guide")
    word_count = len(normalized_text.split())

    if word_count <= 6 and any(term in normalized_text for term in generic_terms):
        return True

    if word_count <= 12 and any(term in normalized_text for term in ("next step", "urgent guidance", "figure this out")):
        return True

    return False


def _sigmoid_confidence(score_gap: float, base: float = 0.6) -> float:
    """Map score gap [0, ∞) to confidence [base, 0.95] using a smooth curve."""
    # smaller gaps → close to base; larger gaps → asymptotically approach 0.95
    return base + (0.95 - base) * (1 - math.exp(-score_gap * 0.4))


# -------------------- PRE-SCREEN --------------------

_llm_chain = None

def _get_llm_chain(settings: Settings):
    global _llm_chain
    if _llm_chain is None:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import JsonOutputParser
        from pydantic import BaseModel, Field
        
        class LLMClassificationOutput(BaseModel):
            domain: Domain = Field(description="One of: 'medical', 'legal', 'general'")
            risk_level: RiskLevel = Field(description="One of: 'low', 'medium', 'high'")
            reasoning: str = Field(description="Brief reasoning")
            confidence: float = Field(description="Confidence between 0 and 1")
            
        llm = ChatOpenAI(
            model=settings.openai_model or "gpt-4o",
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.0,
            max_retries=1
        )
        parser = JsonOutputParser(pydantic_object=LLMClassificationOutput)
        prompt = PromptTemplate(
            template=(
                "You are an expert intent router for an AI assistant.\n"
                "Classify the following user query into one of three domains: 'medical', 'legal', or 'general'.\n"
                "Also assess the risk_level ('low', 'medium', 'high') based on urgency or potential harm.\n\n"
                "Query: \"{query}\"\n\n"
                "Respond with JSON only, matching this schema:\n"
                "{format_instructions}\n"
            ),
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        _llm_chain = prompt | llm | parser
    return _llm_chain

def _llm_classify(query: str, settings: Settings, base_result: ClassificationOutput) -> ClassificationOutput:
    if not settings.enable_llm or not settings.openai_api_key:
        return base_result
        
    try:
        chain = _get_llm_chain(settings)
        res = chain.invoke({"query": query})
        
        return ClassificationOutput(
            domain=res["domain"],
            risk_level=res["risk_level"],
            needs_disclaimer=res["domain"] in [Domain.MEDICAL, Domain.LEGAL],
            self_harm=base_result.self_harm,
            illegal_request=base_result.illegal_request,
            reasoning=f"LLM Fallback: {res['reasoning']}",
            confidence=res["confidence"],
            triggered_terms=base_result.triggered_terms,
            alternative_domains=base_result.alternative_domains,
            explanation=f"Heuristic confidence was low ({base_result.confidence}), so semantic LLM routing was used."
        )
    except Exception as e:
        logger.warning("LLM fallback classification failed: %s", e)
        return base_result


@traceable(name="pre_screen")
def pre_screen_query(query: str) -> ClassificationOutput | None:
    # For safety, use the raw query (no truncation/typo-correction)
    if _contains_any(query, SELF_HARM_KEYWORDS):
        triggers = _matched_terms(query, SELF_HARM_KEYWORDS)
        return ClassificationOutput(
            domain="general",
            risk_level="high",
            needs_disclaimer=True,
            self_harm=True,
            illegal_request=False,
            reasoning="Pre-screen detected self-harm intent.",
            confidence=0.98,
            triggered_terms=triggers,
            alternative_domains={"general": 0.98, "medical": 0.1, "legal": 0.05},
            explanation=(
                "The pre-screen matched self-harm language, so the normal router "
                "was bypassed for a safety response."
            ),
        )

    if _contains_any(query, ILLEGAL_KEYWORDS):
        triggers = _matched_terms(query, ILLEGAL_KEYWORDS)
        return ClassificationOutput(
            domain="legal",
            risk_level="high",
            needs_disclaimer=True,
            self_harm=False,
            illegal_request=True,
            reasoning="Pre-screen detected illegal intent.",
            confidence=0.96,
            triggered_terms=triggers,
            alternative_domains={"legal": 0.96, "general": 0.2, "medical": 0.05},
            explanation=(
                "The pre-screen matched illegal-intent language, so the system refused "
                "unsafe help and offered lawful alternatives."
            ),
        )

    return None


# -------------------- MAIN CLASSIFIER --------------------


@traceable(name="intent_risk_classifier")
def classify_intent(query: str, settings: Settings) -> ClassificationOutput:
    raw_query = query

    # Guard against extremely long inputs
    if len(query) > MAX_QUERY_LENGTH:
        logger.warning("Query truncated from %d to %d chars", len(query), MAX_QUERY_LENGTH)
        query = query[:MAX_QUERY_LENGTH]

    # Lightweight typo correction to improve keyword recall
    query = _correct_typos(query)
    query_lower = query.lower()
    word_count = len(query_lower.split())

    # Pre-screen once and reuse
    pre_screen_result = pre_screen_query(raw_query)
    if pre_screen_result is not None:
        logger.info(
            "PRE-SCREEN HIT | domain=%s | risk=%s | terms=%s",
            pre_screen_result.domain,
            pre_screen_result.risk_level,
            pre_screen_result.triggered_terms,
        )
        return pre_screen_result

    # --- Keyword and heuristic features ---

    medical_score = _score_matches(query_lower, MEDICAL_KEYWORDS)
    legal_score = _score_matches(query_lower, LEGAL_KEYWORDS)
    medical_priority_score = _score_matches(query_lower, MEDICAL_PRIORITY_TERMS)
    legal_priority_score = _score_matches(query_lower, LEGAL_PRIORITY_TERMS)
    medical_weighted_score = _weighted_score(query_lower, MEDICAL_WEIGHTED_TERMS)
    legal_weighted_score = _weighted_score(query_lower, LEGAL_WEIGHTED_TERMS)
    urgent_intent = _contains_any(query_lower, URGENT_INTENT_TERMS)
    has_legal_remedy_intent = _contains_any(query_lower, LEGAL_REMEDY_TERMS)
    has_financial = _contains_any(query_lower, FINANCIAL_KEYWORDS)

    if _contains_any(query_lower, LEGAL_PRACTICAL_STEP_TERMS):
        legal_weighted_score += 2

    has_medical = medical_score > 0 or medical_priority_score > 0 or medical_weighted_score > 0
    has_legal = legal_score > 0 or legal_priority_score > 0 or legal_weighted_score > 0
    is_vague = _is_vague_query(query_lower)
    has_cross_domain_ambiguity = _contains_any(query_lower, AMBIGUOUS_CROSS_DOMAIN_TERMS)

    domain: Domain | None = None
    reasoning = "Keyword-based classification"

    # --- Domain decision logic ---

    if has_cross_domain_ambiguity and has_medical and has_legal:
        domain = "unknown"
        reasoning = "Explicitly mixed medical/legal query requesting routing help"

    if has_legal and has_legal_remedy_intent and legal_weighted_score >= medical_weighted_score:
        domain = "legal"
        reasoning = "Legal remedy terms indicate practical legal intent"

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
    elif domain is None and (word_count < 10 or is_vague):
        domain = "unknown"
        reasoning = "Vague or very short query with low domain evidence"

    # If after all heuristics domain is still None, default to general
    if not domain:
        domain = "general"

    has_high_risk = _contains_any(query_lower, HIGH_RISK_KEYWORDS)
    medical_urgent = _contains_any(query_lower, MEDICAL_URGENCY_TERMS)
    legal_high_risk = _contains_any(query_lower, LEGAL_HIGH_RISK_TERMS)
    has_medium_risk = _contains_any(query_lower, MEDIUM_RISK_KEYWORDS)

    triggered_terms = sorted(
        set(
            _matched_terms(query_lower, MEDICAL_KEYWORDS)
            + _matched_terms(query_lower, LEGAL_KEYWORDS)
            + _matched_terms(query_lower, HIGH_RISK_KEYWORDS)
            + _matched_terms(query_lower, MEDIUM_RISK_KEYWORDS)
            + _matched_terms(query_lower, MEDICAL_URGENCY_TERMS)
            + _matched_terms(query_lower, LEGAL_HIGH_RISK_TERMS)
            + _matched_terms(query_lower, LEGAL_PRACTICAL_STEP_TERMS)
        ),
        key=lambda phrase: (-len(phrase), phrase),
    )[:10]

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

    domain_scores = {
        "medical": float(medical_weighted_score + medical_priority_score + medical_score),
        "legal": float(legal_weighted_score + legal_priority_score + legal_score),
        "general": 1.0 if not has_medical and not has_legal and not is_vague else 0.0,
        "unknown": 2.0 if domain == "unknown" or is_vague or has_cross_domain_ambiguity else 0.0,
    }

    max_score = max(domain_scores.values()) if domain_scores else 0.0
    if max_score > 0:
        normalized_scores = {key: round(value / max_score, 3) for key, value in domain_scores.items()}
    else:
        normalized_scores = {"general": 1.0, "medical": 0.0, "legal": 0.0, "unknown": 0.0}

    sorted_scores = sorted(normalized_scores.values(), reverse=True)
    score_gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]

    # Base confidence on separation between top-2 domain scores
    if domain == "unknown":
        confidence = 0.45 if triggered_terms else 0.35
    elif max_score == 0:
        confidence = 0.55
    else:
        confidence = _sigmoid_confidence(score_gap, base=0.58)

    if has_high_risk:
        confidence = max(confidence, 0.82)

    explanation_parts = [reasoning]
    if triggered_terms:
        explanation_parts.append("Matched terms: " + ", ".join(triggered_terms[:6]))
    if domain == "unknown":
        explanation_parts.append("The router avoided over-confident routing and asks clarification instead.")
    elif domain in {"medical", "legal"}:
        explanation_parts.append(f"The strongest evidence points to the {domain} route.")
    if has_financial:
        explanation_parts.append("Detected financial-related terms; a financial agent could refine this further in future.")

    explanation = " ".join(explanation_parts)

    result = ClassificationOutput(
        domain=domain,
        risk_level=risk_level,
        needs_disclaimer=needs_disclaimer,
        self_harm=_contains_any(raw_query, SELF_HARM_KEYWORDS),
        illegal_request=_contains_any(raw_query, ILLEGAL_KEYWORDS),
        reasoning=f"{reasoning}: domain={domain}, risk={risk_level}",
        confidence=round(confidence, 2),
        triggered_terms=triggered_terms,
        alternative_domains=normalized_scores,
        explanation=explanation,
    )

    if result.domain == "general" and _contains_any(query, MEDICAL_HINTS | LEGAL_HINTS):
        logger.warning("Possible misclassification: heuristic suggests medical/legal")

    # -------------------- CASCADE ROUTING (RESEARCH-LEVEL) --------------------
    # Use fast heuristics for obvious queries. 
    # If the domain is unknown or confidence is low, cascade to the LLM (Semantic Routing).
    if result.domain == Domain.UNKNOWN or result.confidence < 0.65:
        logger.info("Cascading to LLM semantic router due to low confidence (%.2f) or unknown domain.", result.confidence)
        llm_result = _llm_classify(raw_query, settings, result)
        # Retain hard safety flags triggered in pre-screen
        if result.self_harm or result.illegal_request:
            llm_result.self_harm = result.self_harm
            llm_result.illegal_request = result.illegal_request
        
        logger.info("LLM override applied: domain=%s conf=%.2f", llm_result.domain, llm_result.confidence)
        result = llm_result

    logger.info(
        "CLASSIFICATION | len=%d words=%d | domain=%s | risk=%s | conf=%.2f | terms=%s",
        len(raw_query),
        word_count,
        result.domain,
        result.risk_level,
        result.confidence,
        result.triggered_terms[:3],
    )

    return result