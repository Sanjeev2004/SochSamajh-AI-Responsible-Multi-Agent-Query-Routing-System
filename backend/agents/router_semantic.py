from __future__ import annotations

import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("semantic_router")

DOMAIN_ANCHORS = {
    "medical": [
        "What are the symptoms of flu?",
        "I have a headache and fever.",
        "Is this medication safe?",
        "diagnose my condition",
        "treatment for diabetes",
        "doctor appointment",
        "medical advice",
        "my stomach hurts",
    ],
    "legal": [
        "How do I draft a contract?",
        "Is this legal in my state?",
        "sue my landlord",
        "court procedures",
        "intellectual property rights",
        "lawyer consultation",
        "legal liability",
        "breach of agreement",
    ],
    "general": [
        "How do I bake a cake?",
        "What is the capital of France?",
        "write a python script",
        "tell me a joke",
        "weather forecast",
        "how to change a tire",
        "general knowledge",
        "greeting hello",
    ]
}

class SemanticRouter:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SemanticRouter, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        logger.info("Initializing Semantic Router (loading model)...")
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            self.anchor_embeddings = {}
            for domain, anchors in DOMAIN_ANCHORS.items():
                self.anchor_embeddings[domain] = self.model.encode(anchors)
                
            self.initialized = True
            logger.info("Semantic Router initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Semantic Router: {e}")
            self.model = None

    def predict(self, query: str, threshold: float = 0.3) -> str | None:
        if not self.model:
            return None

        query_embedding = self.model.encode([query])

        scores = {}
        for domain, anchors_emb in self.anchor_embeddings.items():
            similarities = cosine_similarity(query_embedding, anchors_emb)[0]
            top_k = min(3, len(similarities))
            top_scores = np.partition(similarities, -top_k)[-top_k:]
            scores[domain] = np.mean(top_scores)

        best_domain = max(scores, key=scores.get)
        best_score = scores[best_domain]

        logger.info(f"Semantic Routing Scores: {scores} (Best: {best_domain} @ {best_score:.3f})")

        if best_score >= threshold:
            return best_domain
        
        return None

semantic_router = SemanticRouter()
