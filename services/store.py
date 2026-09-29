import json
import os
import uuid
import re
from typing import List, Dict

DATA_FILE = "candidates.json"

class CandidateStore:
    @classmethod
    def load_all(cls) -> List[Dict]:
        if not os.path.exists(DATA_FILE):
            return []
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    @classmethod
    def extract_name_from_text(cls, text: str, fallback_filename: str) -> str:
        """Extracts the candidate's actual name from top lines of text or falls back to filename."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:5]:
            clean_line = re.sub(r'[^a-zA-Z\s]', '', line).strip()
            words = clean_line.split()
            if 1 <= len(words) <= 4 and len(clean_line) < 40:
                if not any(header in clean_line.lower() for header in ["curriculum", "vitae", "resume", "page", "contact"]):
                    return clean_line.title()
        
        return fallback_filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()

    @classmethod
    def save_candidate(cls, filename: str, text: str) -> Dict:
        candidates = cls.load_all()
        
        candidate_name = cls.extract_name_from_text(text, filename)
        
        # Check if candidate already exists in database (De-duplication)
        for existing in candidates:
            if existing.get("candidate_name", "").lower() == candidate_name.lower():
                existing["resume_text"] = text  # Update text
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(candidates, f, indent=2)
                return existing

        candidate_id = str(uuid.uuid4())
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = email_match.group(0) if email_match else f"{candidate_id[:8]}@example.com"

        new_candidate = {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "email": email,
            "resume_text": text
        }
        
        candidates.append(new_candidate)
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2)
            
        return new_candidate