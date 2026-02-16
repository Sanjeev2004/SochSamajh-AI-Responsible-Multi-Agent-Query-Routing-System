from __future__ import annotations

from langsmith import traceable
from openai import OpenAI

from core.config import Settings
from core.state import AgentResponse, ClassificationOutput

MEDICAL_DISCLAIMER = "This is general educational information and not medical advice. Please consult a qualified healthcare professional."

COMMON_MEDICAL_INFO = {
    "diabetes": "Common symptoms of diabetes include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, blurred vision, slow-healing sores, and frequent infections. Type 1 diabetes symptoms often develop quickly, while Type 2 symptoms develop more gradually. If you experience these symptoms, consult a healthcare provider for proper diagnosis and blood sugar testing.",
    "fever": "Fever is a temporary increase in body temperature, often due to illness. Normal body temperature is around 98.6 F (37 C). Common causes include infections (viral or bacterial), heat exhaustion, certain medications, and inflammatory conditions. Seek medical attention if fever exceeds 103 F (39.4 C), lasts more than 3 days, or is accompanied by severe symptoms.",
    "headache": "Headaches can be tension-type (most common), migraines, cluster headaches, or secondary to other conditions. Common triggers include stress, dehydration, poor posture, eye strain, and lack of sleep. Most headaches are not serious, but seek immediate medical care for sudden severe headaches, headaches with fever or stiff neck, or headaches after head injury.",
    "pain": "Pain is the body's warning signal. Acute pain comes on suddenly and is usually sharp; chronic pain persists over time. Management depends on the cause and may include rest, ice/heat, over-the-counter pain relievers, physical therapy, or prescription medications. Always consult a healthcare provider for persistent or severe pain.",
}


@traceable(name="medical_agent")
def run_medical_agent(query: str, classification: ClassificationOutput, settings: Settings) -> AgentResponse:
    try:
        client = OpenAI(api_key=settings.openai_api_key)

        messages = [
            {
                "role": "system",
                "content": "You are a medical information assistant. Provide educational, high-level information only. Do NOT diagnose, prescribe, or provide dosages. Encourage professional medical help when appropriate. Be concise and clear.",
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
            disclaimers=[MEDICAL_DISCLAIMER],
            safety_notes=[],
        )
    except Exception:
        query_lower = query.lower()
        for topic, info in COMMON_MEDICAL_INFO.items():
            if topic in query_lower:
                return AgentResponse(
                    content=info,
                    disclaimers=[MEDICAL_DISCLAIMER],
                    safety_notes=[],
                )

        fallback = (
            "I can provide general educational information about medical topics. For specific health concerns, "
            "including symptoms, diagnosis, or treatment, please consult with a qualified healthcare professional "
            "who can evaluate your individual situation. Every person's health needs are unique and require "
            "personalized medical assessment."
        )
        return AgentResponse(
            content=fallback,
            disclaimers=[MEDICAL_DISCLAIMER],
            safety_notes=[],
        )
