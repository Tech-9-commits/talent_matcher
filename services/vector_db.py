import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from typing import List, Dict, Any

COLLECTION_NAME = "candidates"
VECTOR_DIM = 768

_client = None

def get_qdrant_client() -> QdrantClient:
    """Lazy initializer to prevent multiprocessing file-lock errors in Windows/Uvicorn."""
    global _client
    if _client is None:
        # Uses in-memory storage to prevent folder locking issues during reload/multiprocessing
        _client = QdrantClient(location=":memory:")
    return _client

def init_vector_db():
    """Initializes the Qdrant collection if it does not exist."""
    client = get_qdrant_client()
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE)
        )

def store_candidate(vector: List[float], payload: Dict[str, Any]) -> str:
    """Stores candidate embedding vector and payload metadata into Qdrant."""
    client = get_qdrant_client()
    init_vector_db()
    candidate_id = str(uuid.uuid4())
    
    point = PointStruct(
        id=candidate_id,
        vector=vector,
        payload=payload
    )
    
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[point]
    )
    return candidate_id