from __future__ import annotations

import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logger = logging.getLogger("semantic_router")

# Define anchor queries to represent each domain
# In a full research implementation, these would be centroids of a larger dataset.
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
            # Load a lightweight model optimized for semantic search
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Pre-compute anchor embeddings
            self.anchor_embeddings = {}
            for domain, anchors in DOMAIN_ANCHORS.items():
                self.anchor_embeddings[domain] = self.model.encode(anchors)
                
            self.initialized = True
            logger.info("Semantic Router initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Semantic Router: {e}")
            self.model = None

    def predict(self, query: str, threshold: float = 0.3) -> str | None:
        """
        Predict the domain of a query using semantic similarity.
        
        Args:
            query: User query string
            threshold: Minimum similarity score to accept a prediction
            
        Returns:
            Predicted domain ('medical', 'legal', 'general') or None if low confidence
        """
        if not self.model:
            return None

        # Encode the query
        query_embedding = self.model.encode([query])

        # meaningful similarity score for each domain (average of top 3 matches)
        scores = {}
        for domain, anchors_emb in self.anchor_embeddings.items():
            # Calculate similarity between query and all domain anchors
            similarities = cosine_similarity(query_embedding, anchors_emb)[0]
            # Take the mean of the top 3 most similar anchors to be robust
            top_k = min(3, len(similarities))
            top_scores = np.partition(similarities, -top_k)[-top_k:]
            scores[domain] = np.mean(top_scores)

        # Find best domain
        best_domain = max(scores, key=scores.get)
        best_score = scores[best_domain]

        logger.info(f"Semantic Routing Scores: {scores} (Best: {best_domain} @ {best_score:.3f})")

        if best_score >= threshold:
            return best_domain
        
        return None

# Global instance
semantic_router = SemanticRouter()
