from typing import List, Dict, Any

_embedding_model = None

def get_embedding_model():
    """Lazy load SentenceTransformer model."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    return _embedding_model

class VectorService:
    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        """Generates a dense vector representation of the text (768 dimensions)."""
        model = get_embedding_model()
        vector = model.encode(text, show_progress_bar=False)
        return vector.tolist()

    @staticmethod
    def prepare_payload(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Converts candidate data into metadata payload for Qdrant."""
        return {
            "applicant_id": candidate_data.get("applicant_id") or candidate_data.get("name"),
            "candidate_name": candidate_data.get("candidate_name") or candidate_data.get("applicant_name"),
            "email": candidate_data.get("email") or candidate_data.get("email_id"),
            "phone": candidate_data.get("phone") or candidate_data.get("phone_number"),
            "skills": [s.lower() for s in candidate_data.get("skills", [])],
            "raw_text": candidate_data.get("raw_text", "")
        }
