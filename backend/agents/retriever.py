from __future__ import annotations

import os
from pathlib import Path

from core.config import logger

CHROMA_PATH = Path(__file__).resolve().parents[1] / "rag" / "chroma_db"


class Retriever:
    _instance: "Retriever | None" = None

    def __new__(cls) -> "Retriever":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
            cls._instance._init_attempted = False
        return cls._instance

    def _initialize(self) -> None:
        if self._init_attempted:
            return

        self._init_attempted = True
        if os.getenv("MEDICAL_ROUTER_DISABLE_RETRIEVER", "").lower() in {"1", "true", "yes"}:
            logger.info("Retriever disabled via MEDICAL_ROUTER_DISABLE_RETRIEVER.")
            return

        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except Exception as exc:  # pragma: no cover
            logger.warning("Retriever dependencies unavailable: %s", exc)
            return

        try:
            self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
            self.collection = self.client.get_or_create_collection(name="knowledge_base")
            # Avoid hanging on model downloads in restricted or offline environments.
            self.model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            self._ready = True
        except Exception as exc:  # pragma: no cover
            logger.warning("Retriever initialization failed: %s", exc)

    def get_relevant_context(self, query: str, domain: str | None = None, top_k: int = 2) -> str:
        self._initialize()
        if not self._ready:
            return ""

        where_filter = {"domain": domain} if domain else None

        try:
            query_embedding = self.model.encode([query]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                where=where_filter,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("Retriever query failed: %s", exc)
            return ""

        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []
        if not documents or not documents[0]:
            return ""

        context_parts: list[str] = []
        for index, document in enumerate(documents[0]):
            metadata = metadatas[0][index] if metadatas and metadatas[0] else {}
            source = metadata.get("source", "knowledge_base")
            context_parts.append(f"Source ({source}): {document}")

        return "\n\n".join(context_parts)


retriever = Retriever()


def retrieve_context(query: str, domain: str | None = None) -> str:
    return retriever.get_relevant_context(query=query, domain=domain)
