import re
from typing import Dict, List, Optional, Any

_nlp = None

def get_nlp():
    """Lazy loader for spaCy to prevent boot slowdowns."""
    global _nlp
    if _nlp is None:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if model is not yet downloaded
            import spacy.cli
            spacy.cli.download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

# Common words found in resume headers that are NOT candidate names
EXCLUDED_WORDS = {
    "resume", "curriculum", "vitae", "cv", "profile", "summary", 
    "experience", "education", "contact", "skills", "projects",
    "developer", "engineer", "manager", "lead", "architect", "analyst"
}

# Standard technical taxonomy filter
COMMON_TECH_SKILLS = {
    "python", "fastapi", "django", "flask", "frappe", "erpnext", "react", "vue", 
    "angular", "node.js", "javascript", "typescript", "html", "css", "postgresql", 
    "mysql", "mariadb", "mongodb", "redis", "docker", "kubernetes", "aws", "gcp", 
    "azure", "git", "linux", "rest", "graphql", "pytorch", "tensorflow", "spacy", 
    "scikit-learn", "rag", "qdrant", "vector", "pandas", "numpy"
}

class EntityExtractor:
    @staticmethod
    def extract_clean_name(raw_text: str, doc) -> Optional[str]:
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
                    if not any(w.lower() in EXCLUDED_WORDS for word in words):
                        return cleaned_ent

        return None

    @staticmethod
    def parse_resume(raw_text: str) -> Dict[str, Any]:
        """Extracts structured contact information and skills from raw resume text."""
        nlp = get_nlp()
        doc = nlp(raw_text)
        
        # Extract Contact Information
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
        phone_match = re.search(r"\(?\+?\d{1,3}\)?[-.\s]?\d{3}[-.\s]?\d{4,6}", raw_text)
        
        email = email_match.group(0) if email_match else None
        phone = phone_match.group(0) if phone_match else None

        # Extract Candidate Name using heuristic pipeline
        candidate_name = EntityExtractor.extract_clean_name(raw_text, doc)

        # Extract Skills
        tokens = {token.text.lower() for token in doc if not token.is_stop}
        # Also check regex words for hyphenated/dotted skills like node.js, scikit-learn
        raw_words = set(re.findall(r'[a-zA-Z0-9\+#\.]+', raw_text.lower()))
        combined_tokens = tokens.union(raw_words)
        
        extracted_skills = sorted(list(COMMON_TECH_SKILLS.intersection(combined_tokens)))

        return {
            "candidate_name": candidate_name,
            "email": email,
            "phone": phone,
            "skills": extracted_skills,
            "raw_text": raw_text
        }
