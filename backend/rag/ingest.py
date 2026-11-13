"""Rebuild the local Chroma knowledge base from backend/rag/data/*.txt.

Usage (from repo root or backend/):
    cd backend
    python -m rag.ingest

Requires sentence-transformers for vector embeddings. If the model cannot be
loaded, ingestion aborts with a clear error — runtime retrieval still has a
keyword/BM25-like fallback in agents/retriever.py when ENABLE_RETRIEVER=true.
"""
from __future__ import annotations

from pathlib import Path
import uuid

RAG_DIR = Path(__file__).resolve().parent
CHROMA_PATH = RAG_DIR / "chroma_db"
DATA_PATH = RAG_DIR / "data"


def _chunk_file(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    return [c.strip() for c in content.split("\n\n") if c.strip()]


def ingest_data() -> None:
    print(f"Initializing ChromaDB at {CHROMA_PATH}...")
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except Exception as exc:
        raise SystemExit(
            f"Ingest dependencies missing ({exc}). "
            "Install backend/requirements.txt, then retry."
        ) from exc

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    try:
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as exc:
        raise SystemExit(
            f"Could not load embedding model: {exc}. "
            "Runtime retrieval can still use keyword fallback."
        ) from exc

    # Recreate collection for a clean rebuild after corpus updates.
    try:
        client.delete_collection("knowledge_base")
    except Exception:
        pass
    collection = client.get_or_create_collection(name="knowledge_base")

    documents: list[str] = []
    metadatas: list[dict[str, str]] = []
    ids: list[str] = []

    print("Reading data files...")
    for filename in sorted(DATA_PATH.iterdir()):
        if filename.suffix != ".txt":
            continue
        domain = "medical" if "medical" in filename.name else "legal"
        chunks = _chunk_file(filename)
        for i, chunk in enumerate(chunks):
            title = chunk.splitlines()[0].strip().strip('"')[:120]
            documents.append(chunk)
            metadatas.append(
                {
                    "source": filename.name,
                    "domain": domain,
                    "title": title,
                }
            )
            ids.append(f"{filename.stem}_{i}_{uuid.uuid4().hex[:8]}")

    if not documents:
        print("No data found to ingest!")
        return

    print(f"Ingesting {len(documents)} chunks...")
    embeddings = embedding_model.encode(documents).tolist()
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )
    print(f"Ingestion complete! Wrote {len(documents)} chunks to {CHROMA_PATH}")


if __name__ == "__main__":
    ingest_data()
