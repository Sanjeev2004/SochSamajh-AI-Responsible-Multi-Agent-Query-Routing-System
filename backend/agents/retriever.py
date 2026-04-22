from __future__ import annotations

from pathlib import Path
import re

from core.config import logger
from core.state import SourceCitation

CHROMA_PATH = Path(__file__).resolve().parents[1] / "rag" / "chroma_db"
DATA_PATH = Path(__file__).resolve().parents[1] / "rag" / "data"


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(token) > 2}


class Retriever:
    _instance: "Retriever | None" = None

    def __new__(cls) -> "Retriever":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
            cls._instance._init_attempted = False
            cls._instance._fallback_chunks = []
        return cls._instance

    def _load_fallback_chunks(self) -> None:
        if self._fallback_chunks:
            return

        chunks: list[dict[str, str | set[str]]] = []
        for filename in sorted(DATA_PATH.glob("*.txt")):
            domain = "medical" if "medical" in filename.name else "legal"
            try:
                content = filename.read_text(encoding="utf-8")
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to read fallback retrieval file %s: %s", filename, exc)
                continue

            for chunk in [part.strip() for part in content.split("\n\n") if part.strip()]:
                chunks.append(
                    {
                        "domain": domain,
                        "source": filename.name,
                        "text": chunk,
                        "tokens": _tokenize(chunk),
                    }
                )

        self._fallback_chunks = chunks

    def _fallback_relevant_sources(self, query: str, domain: str | None = None, top_k: int = 2) -> list[SourceCitation]:
        self._load_fallback_chunks()
        if not self._fallback_chunks:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[int, int, dict[str, str | set[str]]]] = []
        for chunk in self._fallback_chunks:
            if domain and chunk["domain"] != domain:
                continue
            overlap = len(query_tokens & chunk["tokens"])
            if overlap <= 0:
                continue
            scored.append((overlap, len(str(chunk["text"])), chunk))

        if not scored:
            return []

        scored.sort(key=lambda item: (-item[0], item[1]))
        selected = [item[2] for item in scored[:top_k]]
        sources: list[SourceCitation] = []
        for overlap, _, chunk in scored[:top_k]:
            text = str(chunk["text"])
            first_line = text.splitlines()[0].strip().strip('"')
            sources.append(
                SourceCitation(
                    title=first_line[:90],
                    source=str(chunk["source"]),
                    domain=chunk["domain"],  # type: ignore[arg-type]
                    snippet=text[:280],
                    score=float(overlap),
                )
            )
        return sources

    def _format_context(self, sources: list[SourceCitation]) -> str:
        return "\n\n".join(
            f"Source ({source.source}): {source.snippet}"
            for source in sources
            if source.snippet
        )

    def _initialize(self) -> None:
        if self._init_attempted:
            return

        self._init_attempted = True

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
        except BaseException as exc:  # pragma: no cover
            logger.warning("Retriever initialization failed: %s", exc)

    def get_relevant_context(self, query: str, domain: str | None = None, top_k: int = 2) -> str:
        return self._format_context(self.get_relevant_sources(query=query, domain=domain, top_k=top_k))

    def get_relevant_sources(self, query: str, domain: str | None = None, top_k: int = 2) -> list[SourceCitation]:
        self._initialize()
        if not self._ready:
            return self._fallback_relevant_sources(query=query, domain=domain, top_k=top_k)

        where_filter = {"domain": domain} if domain else None

        try:
            query_embedding = self.model.encode([query]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                where=where_filter,
            )
        except BaseException as exc:  # pragma: no cover
            logger.warning("Retriever query failed: %s", exc)
            return self._fallback_relevant_sources(query=query, domain=domain, top_k=top_k)

        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []
        distances = results.get("distances") or []
        if not documents or not documents[0]:
            return self._fallback_relevant_sources(query=query, domain=domain, top_k=top_k)

        sources: list[SourceCitation] = []
        for index, document in enumerate(documents[0]):
            metadata = metadatas[0][index] if metadatas and metadatas[0] else {}
            source = metadata.get("source", "knowledge_base")
            title = metadata.get("title") or str(source)
            score = None
            if distances and distances[0]:
                score = round(1.0 - float(distances[0][index]), 4)
            sources.append(
                SourceCitation(
                    title=str(title),
                    source=str(source),
                    domain=metadata.get("domain", domain),  # type: ignore[arg-type]
                    snippet=str(document)[:280],
                    score=score,
                )
            )

        return sources


retriever = Retriever()


def retrieve_context(query: str, domain: str | None = None) -> str:
    return retriever.get_relevant_context(query=query, domain=domain)


def retrieve_sources(query: str, domain: str | None = None) -> list[SourceCitation]:
    return retriever.get_relevant_sources(query=query, domain=domain)
