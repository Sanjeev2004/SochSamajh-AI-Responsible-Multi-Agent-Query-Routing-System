from __future__ import annotations
from langsmith import traceable
from core.state import AgentResponse, ClassificationOutput
from core.config import Settings

settings = Settings.load()

@traceable(name="safety_critic")
def run_critic(response: AgentResponse, classification: ClassificationOutput, query: str) -> AgentResponse:
    """
    Criticizes the response for safety and policy adherence.
    If the response violates safety rules, it modifies the response.
    """
    # Rule 1: Medical Agent must allow "diagnosis" language
    # If the user asked for a diagnosis, the agent should have refused or clarified.
    # We check if the response contains "I diagnosis" or similar (bad) vs "consult a doctor" (good).
    
    # Simple keyword heuristic for the critic (in a full paper, this would be an LLM)
    content_lower = response.content.lower()
    
    # If medical, ensure disclaimer language is present in content OR disclaimer list
    if classification.domain == "medical":
        has_advice_warning = "consult" in content_lower or "doctor" in content_lower or "medical professional" in content_lower
        if not has_advice_warning and not response.disclaimers:
            # Inject a safety note if the agent forgot
            response.safety_notes.append("CRITIC WARNING: Response did not explicitly advise consulting a doctor.")
            
    # If legal, ensure "lawyer" or "attorney" is mentioned if it's high risk
    if classification.domain == "legal" and classification.risk_level == "high":
        has_legal_warning = "attorney" in content_lower or "lawyer" in content_lower or "counsel" in content_lower
        if not has_legal_warning:
             response.safety_notes.append("CRITIC WARNING: High-risk legal query response missing attorney referral.")

    return response
