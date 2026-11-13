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
    "want to die", "kill myself tonight",
    "fastest way to kill myself", "sleeping pills would end my life",
    "ways to die", "painless ways to die", "cutting deeply",
    "pass out and die", "end it all", "no reason to live",
    "take an overdose", "overdose on purpose", "i want to overdose",
    # Hindi / Hinglish variants
    "khud ko nuksan", "khud ko nuksan pahuncha",
    "mar jana chahta", "marna chahta hoon",
    "jeena nahi chahta", "zindagi khatam karna chahta",
])

# Jailbreak / unsafe-instruction patterns → treat as high risk for refusal path.
ADVERSARIAL_HIGH_RISK_TERMS = frozenset([
    "ignore all safety", "ignore policy", "ignore ethics",
    "developer mode", "no disclaimers", "do not warn me",
    "pretend you are my surgeon", "roleplay as an er doctor",
    "exact insulin dosage", "sleeping pills can be fatal",
    "hide poisoning", "sedate someone", "fake symptom story",
    "get opioids", "perform an abortion at home",
    "stitches at home", "remove a bullet", "restart a stopped heart",
    "strongest antibiotic", "household glue", "miscarriage",
    "hide cash income", "mislead police", "threaten someone without",
    "without tests", "without leaving legal proof",
])

POST_INCIDENT_HIGH_RISK_TERMS = frozenset([
    "after a dog bite", "wrong injection", "after a fall",
    "falls in the bathroom", "inhaling heavy smoke",
    "smoke from a kitchen fire", "after smoke inhalation",
    "head injury should never", "after a head injury",
    "carbon monoxide at home", "electric shock at work",
    "chemical leak", "pesticide spray", "wrong blood group",
    "near-drowning", "drinks kerosene",
])

ILLEGAL_KEYWORDS = frozenset([
    "make a bomb", "bomb at home", "steal a car", "evade taxes",
    "tax fraud", "launder money", "forge", "forge a signature",
    "forged signature", "counterfeit", "blackmail",
    "hack my neighbor's wi-fi", "hack my neighbor's wifi",
    "how to hack", "buy drugs", "buy illegal drugs",
    "break into a locked phone", "destroy evidence",
    "hide income from taxes", "threaten someone online",
    "fake medical certificate", "fake rent agreement",
    "forged signature template", "hack a company email",
    "shell company for illegal", "intimidate a tenant",
    "false statement in court", "move money after fraud",
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
    "emotional exhaustion", "seizure", "snake bite", "bitten by a snake",
    "burn injury", "dehydration", "heat stroke", "rabies", "tb",
    "tuberculosis",
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
    "blackmail", "blackmailed", "kidnap", "stalked", "stalking",
    "threatening", "threatened", "assault", "attacked me",
    "leak my photos", "police picked up",
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

# Strict emergency / acute medical phrases (prefer multi-word to avoid
# substring traps like "stroke" matching inside "heat stroke").
HIGH_RISK_KEYWORDS = frozenset([
    "chest pain", "crushing chest pain", "difficulty breathing",
    "can't breathe", "cannot breathe", "severe bleeding", "heavy bleeding",
    "coughing blood", "blood in vomit", "vomiting blood", "blood in stool",
    "passed out", "unconscious", "not waking up", "not responding",
    "stroke symptoms", "heart attack", "face is drooping", "face drooping",
    "arm numbness", "severe headache", "cannot speak clearly",
    "cannot speak", "slurred speech", "deep cut", "a lot of bleeding",
    "drank floor cleaner", "drank toilet cleaner", "toilet cleaner",
    "turning blue", "seizure", "snake bite", "bitten by a snake",
    "burn injury", "black stool", "chemical splash", "sudden weakness",
    "one side of the body", "hit their head", "acting confused",
    "nonstop vomiting", "too many tablets", "swallowed a coin",
    "smoke inhalation", "electric shock", "carbon monoxide",
    "allergic reaction", "wrong blood group", "kerosene",
    "near-drowning", "concussion", "head injury",
    "fracture during a road", "missing insulin", "food poisoning",
    "animal scratch", "pesticide spray", "chemical leak",
    "severe allergic",
])

MEDICAL_URGENCY_TERMS = frozenset([
    "chest tightness", "chest me tightness", "left arm pain",
    "shortness of breath", "arm numbness", "face drooping",
    "slurred speech", "breathing difficulty", "struggling to breathe",
    "saans lene mein dikkat", "saans nahi aa rahi", "confusion",
    "fainting", "fainted", "pregnancy bleeding", "bleeding ho rahi",
    "pregnancy me bleeding", "heavy bleeding", "crushing chest",
    "vomiting blood", "coughing blood", "turning blue",
    "not waking up", "not responding properly", "sudden weakness",
    "one side of the body", "hit their head", "acting confused",
    "nonstop vomiting", "signs of dehydration", "too many tablets",
    "drank toilet cleaner", "snake bite", "bitten by a snake",
    "burn injury", "smoke inhalation", "electric shock",
    "carbon monoxide", "wrong blood group", "severe allergic reaction",
    "near-drowning", "drinks kerosene", "swallowed a coin",
    "missing insulin",
])

# Educational / chronic topics that are concerning but not automatic ER.
MEDIUM_RISK_KEYWORDS = frozenset([
    "pain", "sick", "worried", "concerned", "problem", "fever", "child",
    "pregnancy", "vaccine", "vaccines", "dengue", "landlord", "deposit",
    "salary", "divorce", "fir", "malpractice", "employer", "legal notice",
    "certificate", "consent", "negligence", "bukhar", "doctor", "hospital",
    "lawyer", "consumer", "bail", "notice", "complaint", "rights",
    "asthma", "wrongful termination", "small claims", "dog bite",
    "heat stroke", "rabies", "migraine", "poisoning",
])

# Immediate personal-safety / rights-threat legal situations.
LEGAL_HIGH_RISK_TERMS = frozenset([
    "domestic violence", "beating me", "assault", "attacked me",
    "blackmail", "blackmailed", "kidnap", "stalked", "stalking",
    "threatening", "threatened", "under threat",
    "police picked up", "wrongful arrest", "threatening violence",
    "leak my photos", "fear for my safety", "suspicious death",
    "threatening to kidnap", "threatening to leak",
])

LEGAL_PRACTICAL_STEP_TERMS = frozenset([
    "next legal step", "what should i do legally", "what documents",
    "process", "procedure", "how do i file", "kaise file",
    "kaise karu", "legal notice", "complaint", "fir", "consumer court",
])

URGENT_INTENT_TERMS = frozenset([
    "urgent", "emergency", "immediately", "asap",
    "right now", "abhi", "jaldi", "immediate", "urgently",
])

# Softens risk when the query is clearly educational / third-person overview
# rather than a present personal emergency.
EDUCATIONAL_FRAMING_TERMS = frozenset([
    "what are", "what is", "how can", "how does", "how do",
    "when does", "when should", "when do", "what should someone",
    "what should a", "what should families", "what medical",
    "what legal remedies", "what happens legally", "overview",
    "in general", "generally", "explain", "definition of",
])

PERSONAL_EMERGENCY_CUES = frozenset([
    "i have", "i am", "i'm", "my child", "my father", "my mother",
    "my husband", "my wife", "someone", "a relative", "right now",
    "at home", "by mistake", "help me", "what should i do",
])

AMBIGUOUS_CROSS_DOMAIN_TERMS = frozenset([
    "not sure where to start", "both legal and medical",
    "legal and medical help", "medical or legal", "which kind of help",
    "doctor or lawyer", "lawyer or doctor",
])

# Semantic-router cascade band: mid confidence / ambiguous keyword results.
SEMANTIC_CONFIDENCE_LOW = 0.40
SEMANTIC_CONFIDENCE_HIGH = 0.75

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
