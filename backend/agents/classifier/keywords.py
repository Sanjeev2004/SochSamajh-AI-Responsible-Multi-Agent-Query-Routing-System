"""
classifier/keywords.py
All keyword frozensets, weighted dictionaries, and typo correction maps
used by the classification pipeline.
"""
from __future__ import annotations

MAX_QUERY_LENGTH = 2000  # prevent pathological long inputs

# ── Safety boundaries ──────────────────────────────────────────────────────────

SELF_HARM_KEYWORDS = frozenset([
    "kill myself", "suicide", "end my life", "ending everything",
    "do not want to live anymore", "don't want to live anymore",
    "self harm", "self-harm", "hurt myself", "hurt myself tonight",
    "want to die", "overdose", "kill myself tonight",
    "fastest way to kill myself", "sleeping pills would end my life",
    # Hindi / Hinglish variants
    "khud ko nuksan", "khud ko nuksan pahuncha",
    "mar jana chahta", "marna chahta hoon",
    "jeena nahi chahta", "zindagi khatam karna chahta",
])

ILLEGAL_KEYWORDS = frozenset([
    "make a bomb", "bomb at home", "steal a car", "evade taxes",
    "tax fraud", "launder money", "forge", "forge a signature",
    "forged signature", "counterfeit", "blackmail",
    "hack my neighbor's wi-fi", "hack my neighbor's wifi",
    "how to hack", "buy drugs", "break into a locked phone",
    "destroy evidence",
])

# ── Domain hint sets ───────────────────────────────────────────────────────────

MEDICAL_HINTS = frozenset([
    "symptom", "symptoms", "diagnose", "side effects", "pain", "fever",
    "treatment", "medicine", "doctor", "medical", "hospital", "clinic",
    "health", "mental health", "anxiety", "anxious", "stress", "stressed",
    "burnout", "overwhelmed", "care",
])

LEGAL_HINTS = frozenset([
    "contract", "lawsuit", "liability", "legal", "attorney", "court",
    "jurisdiction", "lawyer", "rights", "complaint", "consumer",
    "notice", "police", "bail",
])

VAGUE_QUERY_TERMS = frozenset([
    "help me with my issue", "i have a problem and need advice",
    "can you tell me what to do", "i need urgent guidance",
    "please help me figure this out", "what should be my next step",
    "i am confused and need direction", "can you explain my situation",
    "i do not know where to start",
    "mujhe samajh nahi aa raha kya karun", "kya karun",
    "guide karo", "need advice",
])

# ── Primary keyword sets ───────────────────────────────────────────────────────

MEDICAL_KEYWORDS = frozenset([
    "symptom", "symptoms", "diabetes", "pain", "fever", "treatment",
    "disease", "health", "doctor", "medicine", "medical", "hospital",
    "clinic", "healthcare", "medical care", "sick", "hurt", "tummy",
    "stomach", "abdomen", "nausea", "vomit", "hypertension", "hba1c",
    "stroke", "dengue", "pregnancy", "vaccine", "vaccines", "bleeding",
    "migraine", "asthma", "thyroid", "anemia", "acid reflux", "vitamin d",
    "pcos", "panic attack", "panic", "depression", "anxiety", "anxious",
    "stress", "stressed", "burnout", "overwhelmed", "mental health",
    "emotional exhaustion", "seizure", "snake bite", "burn injury",
    "dehydration", "heat stroke", "rabies", "tb", "tuberculosis",
    "food poisoning", "blood sugar", "head injury", "cut", "poison",
    "cleaner", "child", "bukhar", "gala dard", "chest tightness",
    "numbness", "drooping", "tightness", "shortness of breath",
    "emergency room",
    # Hinglish
    "dard ho raha hai", "tabiyat theek nahi", "ul\u00adti aa rahi",
    "chakkar aa rahe", "naak band", "khansi",
])

LEGAL_KEYWORDS = frozenset([
    "contract", "lawsuit", "law", "legal", "attorney", "court",
    "liability", "jurisdiction", "rights", "copyright", "employer",
    "salary", "fir", "divorce", "deposit", "landlord", "tenant", "rent",
    "agreement", "legal notice", "employment law", "domestic violence",
    "evidence", "consent", "negligence", "medical certificate", "bail",
    "consumer", "complaint", "legal heir", "succession", "rti",
    "challan", "cybercrime", "arrest", "harassment", "injunction",
    "mediation", "police notice", "maintenance", "wrongful termination",
    "termination", "small claims", "dispute", "disputes",
    # Hinglish
    "naukri se nikala", "kiraaya", "kiraya", "mujhe dhoka diya",
])

# ── Priority and weighted scoring ──────────────────────────────────────────────

LEGAL_PRIORITY_TERMS = frozenset([
    "sue", "lawyer", "attorney", "rights", "court", "legal", "illegal",
    "liability", "compensation", "contract", "landlord", "tenant",
    "divorce", "custody", "police", "fir", "complaint", "malpractice",
    "employer", "salary", "copyright", "deposit", "notice", "violence",
    "evidence", "employment", "certificate", "consent", "negligence",
    "bail", "rent", "consumer", "rti", "cybercrime", "arrest",
    "harassment", "maintenance", "wrongful termination", "termination",
    "small claims", "dispute",
])

LEGAL_REMEDY_TERMS = frozenset([
    "compensation", "medical negligence", "malpractice", "consumer court",
    "legal complaint", "legal notice", "step by step",
    "what can i do", "what should i do now",
    "documents needed", "where to file",
])

MEDICAL_PRIORITY_TERMS = frozenset([
    "diagnosis", "diagnose", "symptoms", "treatment", "medicine",
    "doctor", "hospital", "disease", "fever", "pain", "breathing",
    "vomit", "stroke", "blood pressure", "hypertension", "hba1c",
    "dengue", "pregnancy", "vaccine", "bleeding", "poison", "cleaner",
    "bukhar", "migraine", "asthma", "thyroid", "anemia", "acid reflux",
    "pcos", "depression", "panic", "panic attack", "anxiety", "anxious",
    "stress", "stressed", "burnout", "overwhelmed", "mental health",
    "dehydration", "heat stroke", "rabies", "tuberculosis", "gala dard",
    "shortness of breath", "numbness", "drooping",
])

LEGAL_WEIGHTED_TERMS: dict[str, int] = {
    "sue": 6, "lawyer": 5, "attorney": 5, "malpractice": 5,
    "rights": 3, "court": 3, "landlord": 3, "tenant": 3,
    "contract": 3, "divorce": 3, "custody": 3, "compensation": 4,
    "copyright": 4, "employer": 3, "salary": 4, "fir": 5,
    "deposit": 3, "notice": 3, "domestic violence": 5,
    "employment law": 5, "evidence": 3, "consent": 3,
    "negligence": 4, "medical certificate": 4, "bail": 5,
    "rent agreement": 5, "consumer": 4, "rti": 4,
    "legal heir": 5, "succession": 5, "cybercrime": 4,
    "challan": 4, "arrest": 5, "injunction": 4, "mediation": 4,
    "harassment": 4, "police notice": 5, "maintenance": 4,
    "wrongful termination": 6, "small claims": 5, "dispute": 3,
}

MEDICAL_WEIGHTED_TERMS: dict[str, int] = {
    "diagnosis": 4, "diagnose": 4, "symptoms": 3, "fever": 3,
    "treatment": 2, "medicine": 2, "doctor": 1, "pain": 1,
    "vomit": 2, "breathing": 2, "hypertension": 4, "hba1c": 5,
    "dengue": 4, "pregnancy": 4, "vaccine": 3, "vaccines": 3,
    "bleeding": 4, "cleaner": 4, "poison": 4, "bukhar": 4,
    "gala dard": 4, "migraine": 4, "asthma": 4, "thyroid": 4,
    "anemia": 4, "acid reflux": 4, "pcos": 5, "depression": 4,
    "panic": 3, "panic attack": 4, "anxiety": 4, "anxious": 4,
    "stress": 3, "stressed": 3, "burnout": 3, "overwhelmed": 3,
    "mental health": 4, "emotional exhaustion": 4, "seizure": 5,
    "snake bite": 5, "burn injury": 5, "dehydration": 4,
    "rabies": 5, "tuberculosis": 4, "shortness of breath": 5,
    "chest tightness": 4, "numbness": 4, "drooping": 5,
}

# ── Risk signals ───────────────────────────────────────────────────────────────

HIGH_RISK_KEYWORDS = frozenset([
    "chest pain", "difficulty breathing", "can't breathe",
    "cannot breathe", "severe bleeding", "coughing blood",
    "blood in vomit", "blood in stool", "passed out", "unconscious",
    "stroke", "stroke symptoms", "heart attack", "face is drooping",
    "arm numbness", "severe headache", "cannot speak clearly",
    "deep cut", "a lot of bleeding", "drank floor cleaner", "poison",
    "domestic violence", "police picked up", "dog bite", "turning blue",
    "not waking up", "seizure", "snake bite", "burn injury",
    "black stool", "chemical splash", "stalked", "kidnap",
    "threatening", "threatened", "assault", "suspicious death",
])

MEDICAL_URGENCY_TERMS = frozenset([
    "chest tightness", "chest me tightness", "left arm pain",
    "shortness of breath", "arm numbness", "face drooping",
    "slurred speech", "breathing difficulty",
    "saans lene mein dikkat", "saans nahi aa rahi", "confusion",
    "fainting", "pregnancy bleeding", "bleeding ho rahi",
    "pregnancy me bleeding", "heavy bleeding",
])

MEDIUM_RISK_KEYWORDS = frozenset([
    "pain", "sick", "worried", "concerned", "problem", "fever", "child",
    "pregnancy", "vaccine", "vaccines", "dengue", "landlord", "deposit",
    "salary", "divorce", "fir", "malpractice", "employer", "legal notice",
    "certificate", "consent", "negligence", "bukhar", "doctor", "hospital",
    "lawyer", "consumer", "bail", "notice", "complaint", "rights",
    "asthma", "wrongful termination", "small claims",
])

LEGAL_HIGH_RISK_TERMS = frozenset([
    "domestic violence", "assault", "blackmail", "kidnap", "stalked",
    "threatening", "threatened", "police picked up", "wrongful arrest",
])

LEGAL_PRACTICAL_STEP_TERMS = frozenset([
    "next legal step", "what should i do legally", "what documents",
    "process", "procedure", "how do i file", "kaise file",
    "kaise karu", "legal notice", "complaint", "fir", "consumer court",
])

URGENT_INTENT_TERMS = frozenset([
    "urgent", "emergency", "immediately", "asap",
    "right now", "abhi", "jaldi",
])

AMBIGUOUS_CROSS_DOMAIN_TERMS = frozenset([
    "not sure where to start", "both legal and medical",
    "legal and medical help", "medical or legal", "which kind of help",
    "doctor or lawyer", "lawyer or doctor",
])

# ── Typo corrections ───────────────────────────────────────────────────────────

TYPO_CORRECTIONS: dict[str, str] = {
    "symtoms": "symptoms", "symtpoms": "symptoms", "lawer": "lawyer",
    "attourney": "attorney", "docter": "doctor", "hospitl": "hospital",
    "emergancy": "emergency", "divorc": "divorce", "vaccin": "vaccine",
}

NEGATION_PREFIXES = (
    "not ", "don't ", "doesn't ", "no ", "never ",
    "without ", "avoid ", "stop ", "stopped ",
)
