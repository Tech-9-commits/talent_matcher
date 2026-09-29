import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

COLLECTION_NAME = "erpnext_candidates"
VECTOR_DIM = 768

_client = None

def get_qdrant_client() -> QdrantClient:
    """Initializes Qdrant client based on Frappe Settings or in-memory fallback."""
    global _client
    if _client is not None:
        return _client

    qdrant_url = None
    qdrant_api_key = None
    
    # Try reading Frappe configuration if available
    try:
        import frappe
        if frappe.db:
            qdrant_url = frappe.db.get_single_value("Talent Matcher Settings", "qdrant_url")
            qdrant_api_key = frappe.db.get_single_value("Talent Matcher Settings", "qdrant_api_key")
    except Exception:
        pass

    if qdrant_url:
        _client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        # Defaults to in-memory mode for development/testing
        _client = QdrantClient(location=":memory:")
        
    return _client

def init_vector_db():
    """Initializes the Qdrant collection if it does not already exist."""
    client = get_qdrant_client()
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE)
        )

def store_candidate(vector: List[float], payload: Dict[str, Any], point_id: Optional[str] = None) -> str:
    """Stores candidate embedding vector and payload metadata into Qdrant."""
    client = get_qdrant_client()
    init_vector_db()
    
    # Use deterministic or supplied point_id, or generate a uuid
    candidate_id = point_id or str(uuid.uuid4())
    
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
