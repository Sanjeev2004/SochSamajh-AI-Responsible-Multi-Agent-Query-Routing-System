from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid

RAG_DIR = Path(__file__).resolve().parent
CHROMA_PATH = RAG_DIR / "chroma_db"
DATA_PATH = RAG_DIR / "data"

def ingest_data():
    print(f"Initializing ChromaDB at {CHROMA_PATH}...")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2') 
    
    collection = client.get_or_create_collection(name="knowledge_base")
    
    documents = []
    metadatas = []
    ids = []
    
    print("Reading data files...")
    for filename in DATA_PATH.iterdir():
        if filename.suffix == ".txt":
            domain = "medical" if "medical" in filename.name else "legal"
            with filename.open("r", encoding="utf-8") as f:
                content = f.read()
                chunks = [c.strip() for c in content.split('\n\n') if c.strip()]
                
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({"source": filename.name, "domain": domain})
                    ids.append(f"{filename.name}_{i}")
    
    if not documents:
        print("No data found to ingest!")
        return

    print(f"Ingesting {len(documents)} chunks...")
    
    
    embeddings = embedding_model.encode(documents).tolist()
    
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_data()
