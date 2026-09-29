# Talent Matcher Pro (Frappe & ERPNext App)

**Talent Matcher** is a custom Frappe application that integrates AI-powered resume parsing, NLP skill extraction, and semantic candidate matching directly into **ERPNext HRMS (Human Resource Management System)**.

---

## 🚀 Key Features

1. **Automated Resume Parsing**:
   - Parses `.pdf` and `.docx` resumes using `pypdf` and `python-docx`.
   - Extracts candidate names, emails, phone numbers, and technical skills using `spaCy` NLP and heuristic pipelines.
   - Automatically populates `Job Applicant` fields and notes upon resume upload.

2. **Semantic Vector Search & AI Fit Scoring**:
   - Embeds resumes into dense vectors (768 dimensions) using `sentence-transformers` (`all-mpnet-base-v2`).
   - Indexes and performs lightning-fast cosine similarity lookups in **Qdrant Vector DB** (with automatic fallback to in-memory/TF-IDF if Qdrant is not running).
   - Re-ranks candidates against `Job Opening` descriptions with fit scores (0–99%), matched strengths, and skill gaps.

3. **Seamless Desk Integration**:
   - **Job Applicant**: Custom button `⚡ Parse Resume with AI` to manually trigger extraction and update fields on the fly.
   - **Job Opening**: Custom button `🎯 Match Candidates with AI` that opens an interactive dialog with candidate cards, percentage fit badges, and one-click links to applicant profiles.

4. **REST API Compatible**:
   - Exposes whitelisted endpoints (`/api/method/talent_matcher.api.search_candidates_api` and `/api/method/talent_matcher.api.parse_applicant_resume`) for external web/mobile integrations.

---

## 📁 App Structure

```text
app/
├── pyproject.toml                         # App metadata & dependencies
├── requirements.txt                       # Python dependencies
├── README.md
└── talent_matcher/                        # Python package
    ├── __init__.py                        # Version string
    ├── hooks.py                           # Frappe doc_events & doctype_js hooks
    ├── modules.txt                        # Module definition
    ├── api.py                             # Whitelisted Frappe endpoints & hooks
    ├── services/                          # Core AI & parsing logic
    │   ├── parser.py                      # PDF & DOCX text extraction
    │   ├── extractor.py                   # spaCy entity & skill extraction
    │   ├── evaluator.py                   # AI Fit Score, strengths, and gap calculation
    │   ├── vectorizer.py                  # SentenceTransformer embeddings
    │   ├── vector_db.py                   # Qdrant client & collection management
    │   └── search_engine.py               # Vector search & fallback engine
    ├── talent_matcher/                    # Frappe Module
    │   └── doctype/
    │       ├── talent_matcher_settings/   # Single DocType for configuration
    │       └── candidate_match_log/       # Log DocType for matching history
    └── public/
        └── js/
            ├── job_applicant.js           # UI Button for Job Applicant form
            └── job_opening.js             # UI Matching Dialog for Job Opening form
```

---

## 🛠️ Installation in Frappe Bench

Run the following commands inside your Frappe Bench directory:

### Step 1: Install the App
```bash
# If using local path:
bench get-app /path/to/talent_matcher

# Or if pushed to GitHub:
# bench get-app https://github.com/your-username/talent_matcher.git
```

### Step 2: Install Python Dependencies & spaCy Model
```bash
./env/bin/pip install -r apps/talent_matcher/requirements.txt
./env/bin/python -m spacy download en_core_web_sm
```

### Step 3: Install onto your Site
```bash
bench --site [your-site-name] install-app talent_matcher
bench --site [your-site-name] migrate
```

### Step 4: (Optional) Run Qdrant Vector DB
You can spin up Qdrant locally in Docker:
```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```
*Note: If Qdrant is not configured, the app automatically falls back to in-memory vector storage and ERPNext database matching.*

---

## 📋 How to Use

1. **Resume Ingestion**:
   - In ERPNext, go to **HR > Recruitment > Job Applicant**.
   - Create an applicant and attach a resume (`.pdf` or `.docx`).
   - The background worker will automatically parse the resume and extract contact details and skills into the form, or you can click `⚡ Parse Resume with AI` under the **Talent AI** menu button.

2. **Job Matching**:
   - Go to **HR > Recruitment > Job Opening**.
   - Select an existing job opening (or create one with a detailed description).
   - Click `🎯 Match Candidates with AI` in the top right.
   - Select the number of top candidates and click **Run AI Matching**.
   - Review ranked candidates with fit scores, matching skills, and missing skills.
