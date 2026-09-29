from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.evaluator import EvaluatorService
from app.services.store import CandidateStore
import shutil
import os

router = APIRouter()

class SearchQuery(BaseModel):
    job_description: str = Field(..., description="Job description or query string")
    required_skills: List[str] = Field(default_factory=list, description="Optional required skills")
    top_k: int = Field(default=3, description="Number of candidates to evaluate with AI")

    @field_validator('job_description', mode='before')
    @classmethod
    def sanitize_control_characters(cls, v: str) -> str:
        if isinstance(v, str):
            return v.replace('\r\n', '\n').replace('\r', '\n').replace('\t', ' ')
        return v

class CandidateMatch(BaseModel):
    candidate_id: str
    vector_score: float
    ai_fit_score: int
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    executive_summary: Optional[str] = None

class SearchResponse(BaseModel):
    matches: List[CandidateMatch]
    total_found: int


def calculate_vector_scores(job_desc: str, candidates: List[dict]) -> List[float]:
    if not candidates:
        return []
        
    corpus = [job_desc] + [cand.get("resume_text", "") for cand in candidates]
    vectorizer = TfidfVectorizer(stop_words="english")
    
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        return [round(float(score), 4) for score in similarities]
    except Exception:
        return [0.5000] * len(candidates)


@router.post("/search", response_model=SearchResponse)
async def search_candidates(query: SearchQuery):
    try:
        all_candidates = CandidateStore.load_all()

        unique_candidates = []
        seen_names = set()
        for cand in all_candidates:
            name = cand.get("candidate_name", "").strip().lower()
            if name not in seen_names:
                seen_names.add(name)
                unique_candidates.append(cand)

        if not unique_candidates:
            return SearchResponse(matches=[], total_found=0)

        vector_scores = calculate_vector_scores(query.job_description, unique_candidates)

        evaluated_matches = []
        for cand, v_score in zip(unique_candidates, vector_scores):
            eval_result = EvaluatorService.evaluate_candidate(
                job_description=query.job_description,
                candidate_text=cand.get("resume_text", ""),
                vector_score=v_score,
                required_skills=query.required_skills
            )
            
            evaluated_matches.append(
                CandidateMatch(
                    candidate_id=cand.get("candidate_id", ""),
                    vector_score=v_score,
                    ai_fit_score=eval_result["fit_score"],
                    candidate_name=cand.get("candidate_name"),
                    email=cand.get("email"),
                    skills=eval_result["skills"],  # Dynamically extracted skills
                    strengths=eval_result["strengths"],
                    gaps=eval_result["gaps"],
                    executive_summary=eval_result["executive_summary"]
                )
            )

        sorted_matches = sorted(
            evaluated_matches, 
            key=lambda match: (match.ai_fit_score, match.vector_score), 
            reverse=True
        )

        top_matches = sorted_matches[:query.top_k]

        return SearchResponse(matches=top_matches, total_found=len(top_matches))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploaded_resumes"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "status": "success",
            "filename": file.filename,
            "message": f"Resume '{file.filename}' uploaded successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))