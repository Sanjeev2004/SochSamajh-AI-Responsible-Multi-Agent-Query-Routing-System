import chromadb
from sentence_transformers import SentenceTransformer

# Re-use config
CHROMA_PATH = "backend/rag/chroma_db"

class Retriever:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Retriever, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
        
    def __init__(self):
        if self.initialized:
            return
            
        # Initialize client and model once
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(name="knowledge_base")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.initialized = True
        
    def get_relevant_context(self, query: str, domain: str = None, top_k: int = 2) -> str:
        """
        Retrieve relevant context for a query.
        """
        # Embed query
        query_emb = self.model.encode([query]).tolist()
        
        # Query Chroma
        # We can filter by domain if needed (metadata filter)
        where_filter = {"domain": domain} if domain else None
        
        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=top_k,
            where=where_filter
        )
        
        # Format results
        context_parts = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                source = results['metadatas'][0][i]['source']
                context_parts.append(f"Source ({source}): {doc}")
                
        return "\n\n".join(context_parts)

# Singleton - Temporarily disabled due to sentence-transformers error
# retriever = Retriever()

def retrieve_context(query: str, domain: str = None) -> str:
    # Temporarily disabled - return empty context
    return ""

