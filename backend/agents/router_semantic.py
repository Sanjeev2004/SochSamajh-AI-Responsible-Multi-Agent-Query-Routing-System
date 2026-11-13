"""
Semantic domain router using sentence embeddings over domain anchor phrases.

The SentenceTransformer model is lazy-loaded so importing this module (or the
classifier) does not pull a heavy model into memory — important for CI with
ENABLE_LLM=false and offline environments.
"""
from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger("semantic_router")

DOMAIN_ANCHORS: dict[str, list[str]] = {
    "medical": [
        "What are the symptoms of flu?",
        "I have a headache and fever.",
        "Is this medication safe?",
        "diagnose my condition",
        "treatment for diabetes",
        "doctor appointment",
        "medical advice",
        "my stomach hurts",
        # India / Hinglish medical anchors
        "dengue ke symptoms kya hain",
        "mujhe bukhar aur body pain hai",
        "dog bite ke baad rabies vaccine chahiye kya",
        "chest pain aur saans phool rahi hai",
        "pregnancy me bleeding ho rahi hai",
        "migraine ka treatment kya hai",
        "diabetes me blood sugar control kaise kare",
        "heat stroke ke signs kya hote hain",
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
        # India / Hinglish legal anchors
        "FIR kaise file kare police station me",
        "security deposit wapas nahi mil raha landlord se",
        "consumer court me complaint kaise kare",
        "IPC section kya hota hai educational overview",
        "rent agreement aur tenancy rights India",
        "police complaint register nahi kar rahe",
        "naukri se nikala wrongful termination",
        "domestic violence ke legal remedies",
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
        "aaj ka mausam kaisa hai",
        "mujhe ek recipe batao",
    ],
}


class SemanticRouter:
    """Lazy singleton semantic router. Safe when the model is unavailable."""

    _instance: "SemanticRouter | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "SemanticRouter":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._initialized = False
                inst._load_attempted = False
                inst.model = None
                inst.anchor_embeddings = {}
                cls._instance = inst
        return cls._instance

    def _semantic_enabled(self) -> bool:
        """Read ENABLE_SEMANTIC_ROUTER without importing Settings (keeps this module light)."""
        import os

        raw = os.getenv("ENABLE_SEMANTIC_ROUTER", os.getenv("enable_semantic_router", "false"))
        return str(raw).strip().lower() in {"1", "true", "t", "yes", "y", "on"}

    def _ensure_model(self) -> bool:
        """Load SentenceTransformer on first use. Returns True if ready.

        No-ops when ENABLE_SEMANTIC_ROUTER is false so production free-tier
        never attempts a multi-hundred-MB model load.
        """
        if self._initialized and self.model is not None:
            return True
        if self._load_attempted:
            return self.model is not None

        with self._lock:
            if self._load_attempted:
                return self.model is not None

            if not self._semantic_enabled():
                self._load_attempted = True
                self.model = None
                logger.info("Semantic router disabled (ENABLE_SEMANTIC_ROUTER=false); skipping model load")
                return False

            self._load_attempted = True

            try:
                import numpy as np  # noqa: F401
                from sentence_transformers import SentenceTransformer
                from sklearn.metrics.pairwise import cosine_similarity  # noqa: F401
            except Exception as exc:
                logger.warning("Semantic router dependencies unavailable: %s", exc)
                self.model = None
                return False

            try:
                logger.info("Lazy-loading Semantic Router model...")
                # Local cache only by default so CI/offline stays fast and silent.
                # Set SOCH_SEMANTIC_ALLOW_DOWNLOAD=1 to permit a one-time download.
                import os

                allow_download = os.getenv("SOCH_SEMANTIC_ALLOW_DOWNLOAD", "").lower() in {
                    "1", "true", "yes", "on",
                }
                # sentence-transformers versions differ on local_files_only support.
                try:
                    self.model = SentenceTransformer(
                        "all-MiniLM-L6-v2", local_files_only=True
                    )
                except TypeError:
                    if not allow_download:
                        # Avoid network in CI: probe cache path only.
                        from pathlib import Path

                        cache = Path.home() / ".cache" / "huggingface"
                        if not cache.exists():
                            raise RuntimeError(
                                "Semantic model not cached; skipping load in offline mode"
                            )
                    self.model = SentenceTransformer("all-MiniLM-L6-v2")
                except Exception:
                    if not allow_download:
                        raise
                    self.model = SentenceTransformer("all-MiniLM-L6-v2")

                self.anchor_embeddings = {}
                for domain, anchors in DOMAIN_ANCHORS.items():
                    self.anchor_embeddings[domain] = self.model.encode(anchors)

                self._initialized = True
                logger.info("Semantic Router initialized successfully.")
                return True
            except Exception as exc:
                logger.warning("Failed to initialize Semantic Router: %s", exc)
                self.model = None
                self.anchor_embeddings = {}
                return False

    def _score_domains(self, query: str) -> dict[str, float] | None:
        if not self._ensure_model() or self.model is None:
            return None

        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity

            query_embedding = self.model.encode([query])
            scores: dict[str, float] = {}
            for domain, anchors_emb in self.anchor_embeddings.items():
                similarities = cosine_similarity(query_embedding, anchors_emb)[0]
                top_k = min(3, len(similarities))
                top_scores = np.partition(similarities, -top_k)[-top_k:]
                scores[domain] = float(np.mean(top_scores))
            return scores
        except Exception as exc:
            logger.warning("Semantic router scoring failed: %s", exc)
            return None

    def predict(self, query: str, threshold: float = 0.3) -> str | None:
        result = self.predict_with_scores(query, threshold=threshold)
        if result is None:
            return None
        best_domain, _, _ = result
        return best_domain

    def predict_with_scores(
        self, query: str, threshold: float = 0.3
    ) -> tuple[str | None, float | None, dict[str, float]] | None:
        """Return (best_domain, best_score, all_scores) or None if unavailable."""
        scores = self._score_domains(query)
        if not scores:
            return None

        best_domain = max(scores, key=scores.get)
        best_score = scores[best_domain]
        logger.info(
            "Semantic Routing Scores: %s (Best: %s @ %.3f)",
            scores, best_domain, best_score,
        )
        if best_score >= threshold:
            return best_domain, best_score, scores
        return None, best_score, scores


def get_semantic_router() -> SemanticRouter:
    """Factory used by the classifier — does not force model load."""
    return SemanticRouter()


# Backwards-compatible name: does NOT load the model at import time.
semantic_router = SemanticRouter()
