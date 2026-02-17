import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid

# Configuration
CHROMA_PATH = "backend/rag/chroma_db"
DATA_PATH = "backend/rag/data"

def ingest_data():
    print(f"Initializing ChromaDB at {CHROMA_PATH}...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Using the same model as the semantic router for consistency
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2') 
    
    # Create or get collection
    collection = client.get_or_create_collection(name="knowledge_base")
    
    # Read files
    documents = []
    metadatas = []
    ids = []
    
    print("Reading data files...")
    for filename in os.listdir(DATA_PATH):
        if filename.endswith(".txt"):
            domain = "medical" if "medical" in filename else "legal"
            with open(os.path.join(DATA_PATH, filename), "r") as f:
                content = f.read()
                # Simple chunking by paragraph (double newline)
                chunks = [c.strip() for c in content.split('\n\n') if c.strip()]
                
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({"source": filename, "domain": domain})
                    ids.append(f"{filename}_{i}")
    
    if not documents:
        print("No data found to ingest!")
        return

    print(f"Ingesting {len(documents)} chunks...")
    
    # Embed and add to Chroma
    # Note: Chroma uses a default embedding model if none provided, 
    # but we'll use ours explicitly or let Chroma handle it if we passed raw text.
    # For simplicity here, we let Chroma use its default valid model (often all-MiniLM-L6-v2 compatible)
    # OR we pre-embed. Let's let Chroma do it to keep this script simple, 
    # assuming we rely on its default EF or we pass embeddings.
    # Actually, to be safe and consistent with our SemanticRouter, let's pre-embed.
    
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
