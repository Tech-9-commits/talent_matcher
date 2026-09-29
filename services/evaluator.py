import re
from typing import List, Dict

# Standard technical taxonomy filter
COMMON_TECH_SKILLS = {
    "python", "fastapi", "postgresql", "aws", "docker", "rag", "database", 
    "systems", "scalable", "api", "gateways", "react", "node", "java", 
    "cloud", "sql", "git", "linux", "rest", "graphql", "redis", "mongodb"
}

class EvaluatorService:
    @classmethod
    def extract_candidate_skills(cls, text: str) -> List[str]:
        """Extracts recognizable technical skills directly from candidate resume text."""
        tokens = set(re.findall(r'\b[a-zA-Z0-9\+#\.]+\b', text.lower()))
        matched_skills = tokens.intersection(COMMON_TECH_SKILLS)
        return sorted(list(matched_skills))

    @classmethod
    def evaluate_candidate(cls, job_description: str, candidate_text: str, vector_score: float, required_skills: List[str] = None) -> Dict:
        cand_text_lower = candidate_text.lower()
        
        # Build evaluation target skill list
        target_skills = [s.lower() for s in (required_skills or [])]
        if not target_skills:
            # Fallback: extract technical skills from job description text
            jd_tokens = set(re.findall(r'\b[a-zA-Z0-9\+#\.]+\b', job_description.lower()))
            target_skills = list(jd_tokens.intersection(COMMON_TECH_SKILLS))

        candidate_found_skills = cls.extract_candidate_skills(candidate_text)

        # Calculate matches and gaps based on real technical terms
        matched = [skill for skill in target_skills if skill in cand_text_lower or skill in candidate_found_skills]
        missing = [skill for skill in target_skills if skill not in matched]

        # Calculate a realistic fit score
        if target_skills:
            skill_match_ratio = len(matched) / len(target_skills)
        else:
            skill_match_ratio = 0.5

        raw_fit = int((skill_match_ratio * 70) + (vector_score * 30))
        fit_score = max(10, min(99, raw_fit))

        # Format clean, human-readable strengths & gaps
        strengths_str = f"Matches key skills: {', '.join([s.title() for s in matched])}" if matched else "Matches general domain context"
        gaps_str = f"Missing required skills: {', '.join([s.title() for s in missing])}" if missing else "No major skill gaps identified"

        matched_summary = ', '.join([s.title() for s in matched[:3]]) if matched else "General backend criteria"
        summary = f"Candidate aligns on {matched_summary} with an overall similarity fit of {fit_score}%."

        return {
            "fit_score": fit_score,
            "skills": candidate_found_skills,
            "strengths": [strengths_str],
            "gaps": [gaps_str],
            "executive_summary": summary
        }