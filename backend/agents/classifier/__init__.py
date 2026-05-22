"""
classifier/__init__.py
Public API for the classifier package.

All external code should import from here, not from submodules directly:
    from agents.classifier import classify_intent, pre_screen_query
"""
from __future__ import annotations

from langsmith import traceable

from core.config import Settings, logger
from core.state import ClassificationOutput, Domain

from .keywords import (
    MAX_QUERY_LENGTH,
    MEDICAL_KEYWORDS, LEGAL_KEYWORDS,
    MEDICAL_PRIORITY_TERMS, LEGAL_PRIORITY_TERMS,
    MEDICAL_WEIGHTED_TERMS, LEGAL_WEIGHTED_TERMS,
    MEDICAL_URGENCY_TERMS, LEGAL_HIGH_RISK_TERMS,
    HIGH_RISK_KEYWORDS, MEDIUM_RISK_KEYWORDS,
    LEGAL_REMEDY_TERMS, LEGAL_PRACTICAL_STEP_TERMS,
    URGENT_INTENT_TERMS, AMBIGUOUS_CROSS_DOMAIN_TERMS,
    MEDICAL_HINTS, LEGAL_HINTS,
    SELF_HARM_KEYWORDS, ILLEGAL_KEYWORDS,
)
from .scorer import (
    correct_typos, contains_any, score_matches,
    weighted_score, matched_terms, is_vague_query, sigmoid_confidence,
)
from .pre_screen import pre_screen_query
from .llm_fallback import llm_classify


@traceable(name="intent_risk_classifier")
def classify_intent(query: str, settings: Settings) -> ClassificationOutput:
    """Classify a user query into a domain and risk level.

    Pipeline:
      1. Pre-screen for hard safety boundaries (self-harm / illegal).
      2. Keyword & weighted heuristics to determine domain + risk.
      3. If confidence < threshold or domain is unknown, cascade to LLM.
    """
    raw_query = query

    # Guard against extremely long inputs
    if len(query) > MAX_QUERY_LENGTH:
        logger.warning("Query truncated from %d to %d chars", len(query), MAX_QUERY_LENGTH)
        query = query[:MAX_QUERY_LENGTH]

    # Lightweight typo correction to improve keyword recall
    query = correct_typos(query)
    query_lower = query.lower()
    word_count = len(query_lower.split())

    # Step 1: Pre-screen (reuse result to avoid double-work)
    pre_screen_result = pre_screen_query(raw_query)
    if pre_screen_result is not None:
        logger.info(
            "PRE-SCREEN HIT | domain=%s | risk=%s | terms=%s",
            pre_screen_result.domain,
            pre_screen_result.risk_level,
            pre_screen_result.triggered_terms,
        )
        return pre_screen_result

    # Step 2: Keyword and heuristic feature extraction
    medical_score = score_matches(query_lower, MEDICAL_KEYWORDS)
    legal_score = score_matches(query_lower, LEGAL_KEYWORDS)
    medical_priority_score = score_matches(query_lower, MEDICAL_PRIORITY_TERMS)
    legal_priority_score = score_matches(query_lower, LEGAL_PRIORITY_TERMS)
    medical_weighted = weighted_score(query_lower, MEDICAL_WEIGHTED_TERMS)
    legal_weighted = weighted_score(query_lower, LEGAL_WEIGHTED_TERMS)
    urgent_intent = contains_any(query_lower, URGENT_INTENT_TERMS)
    has_legal_remedy_intent = contains_any(query_lower, LEGAL_REMEDY_TERMS)

    if contains_any(query_lower, LEGAL_PRACTICAL_STEP_TERMS):
        legal_weighted += 2

    has_medical = medical_score > 0 or medical_priority_score > 0 or medical_weighted > 0
    has_legal = legal_score > 0 or legal_priority_score > 0 or legal_weighted > 0
    is_vague = is_vague_query(query_lower)
    has_cross_domain = contains_any(query_lower, AMBIGUOUS_CROSS_DOMAIN_TERMS)

    # Step 3: Domain decision logic (cascading priority)
    domain: Domain | None = None
    reasoning = "Keyword-based classification"

    if has_cross_domain and has_medical and has_legal:
        domain = "unknown"
        reasoning = "Explicitly mixed medical/legal query requesting routing help"

    if has_legal and has_legal_remedy_intent and legal_weighted >= medical_weighted:
        domain = "legal"
        reasoning = "Legal remedy terms indicate practical legal intent"

    if domain is None and has_medical and has_legal:
        w_gap = abs(medical_weighted - legal_weighted)
        p_gap = abs(medical_priority_score - legal_priority_score)
        if w_gap <= 2 and p_gap <= 1:
            domain = "unknown"
            reasoning = (
                f"Ambiguous cross-domain query (weighted_gap={w_gap}, priority_gap={p_gap})"
            )

    if domain is None and legal_weighted > medical_weighted:
        domain = "legal"
        reasoning = f"Weighted legal intent (legal={legal_weighted}, medical={medical_weighted})"
    elif domain is None and medical_weighted > legal_weighted:
        domain = "medical"
        reasoning = f"Weighted medical intent (medical={medical_weighted}, legal={legal_weighted})"
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

    if not domain:
        domain = "general"

    # Step 4: Risk level determination
    has_high_risk = contains_any(query_lower, HIGH_RISK_KEYWORDS)
    medical_urgent = contains_any(query_lower, MEDICAL_URGENCY_TERMS)
    legal_high_risk = contains_any(query_lower, LEGAL_HIGH_RISK_TERMS)
    has_medium_risk = contains_any(query_lower, MEDIUM_RISK_KEYWORDS)

    if medical_urgent and domain in {"medical", "unknown"}:
        has_high_risk = True
    if legal_high_risk and domain in {"legal", "unknown"}:
        has_high_risk = True
    if urgent_intent and (has_medical or has_legal) and not has_high_risk:
        has_medium_risk = True
    if urgent_intent and domain == "medical" and medical_weighted >= 3:
        has_high_risk = True
    if domain == "unknown":
        has_medium_risk = urgent_intent

    if has_high_risk:
        risk_level = "high"
    elif has_medium_risk:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Step 5: Collect triggered terms for explainability
    triggered_terms = sorted(
        set(
            matched_terms(query_lower, MEDICAL_KEYWORDS)
            + matched_terms(query_lower, LEGAL_KEYWORDS)
            + matched_terms(query_lower, HIGH_RISK_KEYWORDS)
            + matched_terms(query_lower, MEDIUM_RISK_KEYWORDS)
            + matched_terms(query_lower, MEDICAL_URGENCY_TERMS)
            + matched_terms(query_lower, LEGAL_HIGH_RISK_TERMS)
            + matched_terms(query_lower, LEGAL_PRACTICAL_STEP_TERMS)
        ),
        key=lambda p: (-len(p), p),
    )[:10]

    # Step 6: Confidence estimation via normalised domain scores
    domain_scores = {
        "medical": float(medical_weighted + medical_priority_score + medical_score),
        "legal": float(legal_weighted + legal_priority_score + legal_score),
        "general": 1.0 if not has_medical and not has_legal and not is_vague else 0.0,
        "unknown": 2.0 if domain == "unknown" or is_vague or has_cross_domain else 0.0,
    }

    max_score = max(domain_scores.values()) if domain_scores else 0.0
    if max_score > 0:
        normalized_scores = {k: round(v / max_score, 3) for k, v in domain_scores.items()}
    else:
        normalized_scores = {"general": 1.0, "medical": 0.0, "legal": 0.0, "unknown": 0.0}

    sorted_vals = sorted(normalized_scores.values(), reverse=True)
    score_gap = sorted_vals[0] - sorted_vals[1] if len(sorted_vals) > 1 else sorted_vals[0]

    if domain == "unknown":
        confidence = 0.45 if triggered_terms else 0.35
    elif max_score == 0:
        confidence = 0.55
    else:
        confidence = sigmoid_confidence(score_gap, base=0.58)

    if has_high_risk:
        confidence = max(confidence, 0.82)

    # Step 7: Build human-readable explanation
    explanation_parts = [reasoning]
    if triggered_terms:
        explanation_parts.append("Matched terms: " + ", ".join(triggered_terms[:6]))
    if domain == "unknown":
        explanation_parts.append(
            "The router avoided over-confident routing and asks clarification instead."
        )
    if domain in {"medical", "legal"}:
        explanation_parts.append(f"The strongest evidence points to the {domain} route.")

    result = ClassificationOutput(
        domain=domain,
        risk_level=risk_level,
        needs_disclaimer=domain in ["medical", "legal"],
        self_harm=contains_any(raw_query, SELF_HARM_KEYWORDS),
        illegal_request=contains_any(raw_query, ILLEGAL_KEYWORDS),
        reasoning=f"{reasoning}: domain={domain}, risk={risk_level}",
        confidence=round(confidence, 2),
        triggered_terms=triggered_terms,
        alternative_domains=normalized_scores,
        explanation=" ".join(explanation_parts),
    )

    if result.domain == "general" and contains_any(query, MEDICAL_HINTS | LEGAL_HINTS):
        logger.warning("Possible misclassification: heuristic suggests medical/legal")

    # Step 8: LLM cascade — escalate uncertain results to semantic router
    if result.domain == Domain.UNKNOWN or result.confidence < settings.llm_fallback_confidence_threshold:
        logger.info(
            "Cascading to LLM semantic router (confidence=%.2f, domain=%s)",
            result.confidence, result.domain,
        )
        llm_result = llm_classify(raw_query, settings, result)
        # Always preserve hard safety flags from the pre-screen
        if result.self_harm or result.illegal_request:
            llm_result.self_harm = result.self_harm
            llm_result.illegal_request = result.illegal_request
        logger.info(
            "LLM override applied: domain=%s conf=%.2f",
            llm_result.domain, llm_result.confidence,
        )
        result = llm_result

    logger.info(
        "CLASSIFICATION | len=%d words=%d | domain=%s | risk=%s | conf=%.2f | terms=%s",
        len(raw_query), word_count,
        result.domain, result.risk_level,
        result.confidence, result.triggered_terms[:3],
    )

    return result


__all__ = ["classify_intent", "pre_screen_query"]
