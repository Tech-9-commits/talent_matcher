from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from app.schemas.resume import ParsedResume

# Load lightweight, highly accurate embedding model
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

class VectorService:
    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        """Generates a dense vector representation of the text."""
        vector = embedding_model.encode(text, show_progress_bar=False)
        return vector.tolist()

    @staticmethod
    def prepare_payload(parsed_resume: ParsedResume) -> Dict[str, Any]:
        """Converts structured resume data into metadata payload for Qdrant."""
        return {
            "candidate_name": parsed_resume.candidate_name,
            "email": parsed_resume.email,
            "phone": parsed_resume.phone,
            "skills": [s.lower() for s in parsed_resume.skills],
            "raw_text": parsed_resume.raw_text
        }