from app.services.vectorizer import VectorService
from app.services.vector_db import get_qdrant_client, COLLECTION_NAME
from app.services.evaluator import EvaluatorService
from app.schemas.search import SearchQuery, CandidateMatch, SearchResponse

class SearchEngine:
    @staticmethod
    def search_candidates(query: SearchQuery) -> SearchResponse:
        client = get_qdrant_client()
        
        # 1. Vector Search
        query_vector = VectorService.generate_embedding(query.job_description)
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=query.top_k
        )
        
        matches = []
        
        # 2. Re-rank top results using LLM Evaluator
        for result in response.points:
            payload = result.payload or {}
            raw_text = payload.get("raw_text", "")
            
            # Run AI Evaluation
            ai_eval = EvaluatorService.evaluate_candidate(
                job_description=query.job_description,
                candidate_text=raw_text
            )
            
            matches.append(
                CandidateMatch(
                    candidate_id=str(result.id),
                    vector_score=round(float(result.score), 4),
                    ai_fit_score=ai_eval.get("fit_score", 0),
                    candidate_name=payload.get("candidate_name"),
                    email=payload.get("email"),
                    skills=payload.get("skills", []),
                    strengths=ai_eval.get("strengths", []),
                    gaps=ai_eval.get("gaps", []),
                    executive_summary=ai_eval.get("executive_summary")
                )
            )
            
        # Sort matches by AI Fit Score (descending)
        matches.sort(key=lambda x: x.ai_fit_score, reverse=True)
            
        return SearchResponse(
            matches=matches,
            total_found=len(matches)
        )