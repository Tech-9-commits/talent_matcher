import re
import spacy
from app.schemas.resume import ParsedResume

nlp = spacy.load("en_core_web_sm")

# Common words found in resume headers that are NOT candidate names
EXCLUDED_WORDS = {
    "resume", "curriculum", "vitae", "cv", "profile", "summary", 
    "experience", "education", "contact", "skills", "projects",
    "developer", "engineer", "manager", "lead", "architect", "analyst"
}

class EntityExtractor:
    @staticmethod
    def extract_clean_name(raw_text: str, doc) -> str | None:
        """Extracts candidate name using header positioning and entity filtering."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        # 1. First Pass: Check the top 5 lines of the resume (where names typically live)
        for line in lines[:5]:
            # Skip lines containing emails, URLs, or phone numbers
            if re.search(r"[\w\.-]+@[\w\.-]+\.\w+|\d{10}|http|github|linkedin", line, re.IGNORECASE):
                continue
                
            # Clean up punctuation and special characters
            cleaned_line = re.sub(r"[^a-zA-Z\s]", "", line).strip()
            words = cleaned_line.split()
            
            # Candidate names are typically 2 to 4 words long
            if 2 <= len(words) <= 4:
                # Ensure none of the words are common header section titles
                if not any(word.lower() in EXCLUDED_WORDS for word in words):
                    # Check if words are Title Cased (e.g., "John Doe")
                    if all(w[0].isupper() for w in words if w):
                        return cleaned_line

        # 2. Fallback: Search spaCy PERSON entities with strict validation
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                cleaned_ent = re.sub(r"[^a-zA-Z\s]", "", ent.text).strip()
                words = cleaned_ent.split()
                if 2 <= len(words) <= 3:
                    if not any(w.lower() in EXCLUDED_WORDS for w in words):
                        return cleaned_ent

        return None

    @staticmethod
    def parse_resume(raw_text: str) -> ParsedResume:
        doc = nlp(raw_text)
        
        # Extract Contact Information
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
        phone_match = re.search(r"\(?\+?\d{1,3}\)?[-.\s]?\d{3}[-.\s]?\d{4,6}", raw_text)
        
        email = email_match.group(0) if email_match else None
        phone = phone_match.group(0) if phone_match else None

        # Extract Candidate Name using heuristic pipeline
        candidate_name = EntityExtractor.extract_clean_name(raw_text, doc)

        # Extract Skills
        common_skills_db = {
            "python", "fastapi", "django", "react", "node.js", "postgresql", 
            "docker", "kubernetes", "aws", "pytorch", "tensorflow", "spacy", "scikit-learn"
        }
        tokens = {token.text.lower() for token in doc if not token.is_stop}
        extracted_skills = list(common_skills_db.intersection(tokens))

        return ParsedResume(
            candidate_name=candidate_name,
            email=email,
            phone=phone,
            skills=extracted_skills,
            raw_text=raw_text
        )