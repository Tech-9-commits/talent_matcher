from typing import List, Dict, Any, Optional
from talent_matcher.services.vectorizer import VectorService
from talent_matcher.services.vector_db import get_qdrant_client, COLLECTION_NAME, init_vector_db
from talent_matcher.services.evaluator import EvaluatorService

class SearchEngine:
    @staticmethod
    def search_candidates(
        job_description: str,
        required_skills: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Searches candidates using vector similarity in Qdrant and re-ranks with EvaluatorService.
        Includes automatic fallback to Frappe Job Applicant database if vector DB is not yet populated.
        """
        matches = []
        client = get_qdrant_client()
        init_vector_db()

        try:
            # 1. Vector Search via Qdrant
            query_vector = VectorService.generate_embedding(job_description)
            response = client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=top_k * 2
            )

            for result in response.points:
                payload = result.payload or {}
                raw_text = payload.get("raw_text", "")
                
                ai_eval = EvaluatorService.evaluate_candidate(
                    job_description=job_description,
                    candidate_text=raw_text,
                    vector_score=round(float(result.score), 4),
                    required_skills=required_skills
                )

                matches.append({
                    "applicant_id": payload.get("applicant_id") or str(result.id),
                    "candidate_name": payload.get("candidate_name", "Unknown Candidate"),
                    "email": payload.get("email"),
                    "phone": payload.get("phone"),
                    "vector_score": round(float(result.score), 4),
                    "ai_fit_score": ai_eval["fit_score"],
                    "skills": ai_eval["skills"],
                    "matched_skills": ai_eval["matched_skills"],
                    "missing_skills": ai_eval["missing_skills"],
                    "strengths": ai_eval["strengths"],
                    "gaps": ai_eval["gaps"],
                    "executive_summary": ai_eval["executive_summary"]
                })

        except Exception as e:
            # If Qdrant query encounters an issue, fallback to Frappe DB search
            pass

        # If vector search yielded no points, fallback to direct Frappe DB applicants
        if not matches:
            matches = SearchEngine._fallback_frappe_search(job_description, required_skills, top_k)

        # Sort matches by AI Fit Score descending
        matches.sort(key=lambda x: (x.get("ai_fit_score", 0), x.get("vector_score", 0)), reverse=True)
        return matches[:top_k]

    @staticmethod
    def _fallback_frappe_search(
        job_description: str,
        required_skills: Optional[List[str]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Fallback to matching against Job Applicant records directly in Frappe database."""
        try:
            import frappe
            applicants = frappe.get_all(
                "Job Applicant",
                fields=["name", "applicant_name", "email_id", "phone_number", "notes", "status"]
            )
            if not applicants:
                return []

            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            corpus = [job_description]
            app_texts = []
            for app in applicants:
                # Use notes or custom resume text field
                txt = f"{app.applicant_name or ''} {app.notes or ''}"
                app_texts.append(txt)
                corpus.append(txt)

            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(corpus)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

            matches = []
            for app, sim in zip(applicants, similarities):
                cand_text = f"{app.applicant_name} {app.notes or ''}"
                ai_eval = EvaluatorService.evaluate_candidate(
                    job_description=job_description,
                    candidate_text=cand_text,
                    vector_score=round(float(sim), 4),
                    required_skills=required_skills
                )
                matches.append({
                    "applicant_id": app.name,
                    "candidate_name": app.applicant_name,
                    "email": app.email_id,
                    "phone": app.phone_number,
                    "vector_score": round(float(sim), 4),
                    "ai_fit_score": ai_eval["fit_score"],
                    "skills": ai_eval["skills"],
                    "matched_skills": ai_eval["matched_skills"],
                    "missing_skills": ai_eval["missing_skills"],
                    "strengths": ai_eval["strengths"],
                    "gaps": ai_eval["gaps"],
                    "executive_summary": ai_eval["executive_summary"]
                })
            return matches
        except Exception:
            return []
