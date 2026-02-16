from __future__ import annotations

from langsmith import traceable
from openai import OpenAI

from core.config import Settings
from core.state import AgentResponse, ClassificationOutput

LEGAL_DISCLAIMER = (
    "This is general legal information, not legal advice. Laws vary by jurisdiction; consult a licensed attorney."
)

COMMON_LEGAL_INFO = {
    "contract": "A contract is a legally binding agreement between two or more parties. To be valid, it typically requires: (1) an offer, (2) acceptance, (3) consideration (something of value exchanged), (4) mutual intent to be bound, and (5) legal capacity of parties. Contracts can be written, oral, or implied. Written contracts are generally easier to enforce. Laws governing contracts vary by jurisdiction.",
    "liability": "Liability refers to legal responsibility for one's actions or omissions. Common types include: (1) Criminal liability - responsibility for crimes, (2) Civil liability - responsibility for damages in civil matters, (3) Strict liability - responsibility regardless of fault (e.g., defective products), (4) Vicarious liability - responsibility for others' actions (e.g., employer for employee). The specifics depend on jurisdiction and circumstances.",
    "lawsuit": "A lawsuit is a legal action brought in court to enforce a right or seek a remedy. The process typically involves: filing a complaint, serving the defendant, discovery (evidence exchange), pre-trial motions, trial (if not settled), and potential appeals. Civil lawsuits seek monetary damages or specific performance; criminal cases are prosecuted by the government. Legal procedures vary by jurisdiction.",
    "lease": "A lease is a contract granting use of property for a specified period in exchange for payment. Key elements include: parties' names, property description, lease term, rent amount and due date, security deposit, maintenance responsibilities, and termination conditions. Tenant and landlord rights vary significantly by jurisdiction. Review local laws or consult an attorney for specific situations.",
}


@traceable(name="legal_agent")
def run_legal_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    try:
        client = OpenAI(api_key=settings.openai_api_key)

        messages = [
            {
                "role": "system",
                "content": "You are a legal information assistant. Provide general, high-level information only. Do NOT provide definitive legal advice. Note that laws vary by jurisdiction. Be concise and clear.",
            },
            {"role": "user", "content": query},
        ]

        response = client.chat.completions.create(
            messages=messages,
            model=settings.openai_model,
            max_tokens=512,
            temperature=0.2,
        )

        return AgentResponse(
            content=(response.choices[0].message.content or "").strip(),
            disclaimers=[LEGAL_DISCLAIMER],
            safety_notes=[],
        )
    except Exception:
        query_lower = query.lower()
        for topic, info in COMMON_LEGAL_INFO.items():
            if topic in query_lower:
                return AgentResponse(
                    content=info,
                    disclaimers=[LEGAL_DISCLAIMER],
                    safety_notes=[],
                )

        fallback = (
            "I can provide general legal information and concepts. However, laws vary significantly by jurisdiction "
            "and your specific circumstances matter. For advice applicable to your situation, please consult with "
            "a licensed attorney in your area who can review the specific details of your case and provide guidance "
            "based on applicable local laws."
        )
        return AgentResponse(
            content=fallback,
            disclaimers=[LEGAL_DISCLAIMER],
            safety_notes=[],
        )
