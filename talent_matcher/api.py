import os
import json
import frappe
from frappe import _
from talent_matcher.services.parser import DocumentParser
from talent_matcher.services.extractor import EntityExtractor
from talent_matcher.services.evaluator import EvaluatorService
from talent_matcher.services.vectorizer import VectorService
from talent_matcher.services.vector_db import store_candidate
from talent_matcher.services.search_engine import SearchEngine

def _get_applicant_file_path(doc) -> tuple[str, str]:
    """Finds the local file path and filename of an attached resume for a Job Applicant."""
    file_url = getattr(doc, "resume_attachment", None)
    
    # If not on standard field, look in attached Files
    if not file_url:
        attached_files = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Job Applicant", "attached_to_name": doc.name},
            fields=["file_url", "file_name"],
            order_by="creation desc",
            limit=1
        )
        if attached_files:
            file_url = attached_files[0].file_url

    if not file_url:
        raise frappe.ValidationError(_("No resume attachment found for applicant {0}").format(doc.name))

    # Resolve local file system path in Frappe
    if file_url.startswith("/private/files/"):
        abs_path = frappe.get_site_path("private", "files", os.path.basename(file_url))
    elif file_url.startswith("/files/"):
        abs_path = frappe.get_site_path("public", "files", os.path.basename(file_url))
    else:
        abs_path = frappe.get_site_path(file_url.lstrip("/"))

    return abs_path, os.path.basename(file_url)


@frappe.whitelist()
def parse_applicant_resume(applicant_id: str):
    """
    Parses an applicant's resume file, extracts contact info & skills,
    updates the Job Applicant document, and indexes it into Qdrant.
    """
    doc = frappe.get_doc("Job Applicant", applicant_id)
    file_path, filename = _get_applicant_file_path(doc)

    # 1. Parse document text
    raw_text = DocumentParser.extract_text_from_file_path(file_path)

    # 2. Extract entities and skills
    parsed = EntityExtractor.parse_resume(raw_text)

    # 3. Update Job Applicant fields (without overwriting if already set manually)
    if not doc.applicant_name and parsed.get("candidate_name"):
        doc.applicant_name = parsed["candidate_name"]
    if not doc.email_id and parsed.get("email"):
        doc.email_id = parsed["email"]
    if not doc.phone_number and parsed.get("phone"):
        doc.phone_number = parsed["phone"]

    # Append extracted skills and AI summary to notes
    skills_list = parsed.get("skills", [])
    skills_badge = ", ".join(skills_list) if skills_list else "None detected"
    
    notes_addition = f"\n\n--- AI Resume Parsing ---\nExtracted Skills: {skills_badge}"
    if not doc.notes:
        doc.notes = notes_addition
    elif "--- AI Resume Parsing ---" not in doc.notes:
        doc.notes += notes_addition

    doc.flags.ignore_permissions = True
    doc.save()

    # 4. Vectorize & Index in Qdrant Vector DB
    try:
        vector = VectorService.generate_embedding(raw_text)
        payload = VectorService.prepare_payload({
            "applicant_id": doc.name,
            "candidate_name": doc.applicant_name,
            "email": doc.email_id,
            "phone": doc.phone_number,
            "skills": skills_list,
            "raw_text": raw_text
        })
        store_candidate(vector=vector, payload=payload, point_id=None)
    except Exception as e:
        frappe.log_error(f"Error vectorizing applicant {doc.name}: {str(e)}", "Talent Matcher Vector Error")

    return {
        "status": "success",
        "applicant_id": doc.name,
        "applicant_name": doc.applicant_name,
        "email": doc.email_id,
        "phone": doc.phone_number,
        "skills": skills_list,
        "extracted_length": len(raw_text)
    }


def on_job_applicant_created(doc, method=None):
    """
    Hook triggered after a new Job Applicant is inserted.
    Enqueues background resume parsing if resume attachment is present.
    """
    try:
        has_attachment = bool(getattr(doc, "resume_attachment", None))
        if has_attachment:
            frappe.enqueue(
                "talent_matcher.api.parse_applicant_resume",
                queue="long",
                applicant_id=doc.name
            )
    except Exception as e:
        frappe.log_error(f"Error enqueuing resume parse for {doc.name}: {str(e)}", "Talent Matcher Hook Error")


@frappe.whitelist()
def match_candidates_for_job(job_opening_id: str, top_k: int = 5):
    """
    Matches and ranks candidates against a specific Job Opening in ERPNext.
    """
    job = frappe.get_doc("Job Opening", job_opening_id)
    
    job_desc = f"{job.job_title}\n\n{job.description or ''}"
    matches = SearchEngine.search_candidates(
        job_description=job_desc,
        required_skills=None,
        top_k=int(top_k)
    )

    # Optional: Log the search query for auditing
    try:
        log = frappe.get_doc({
            "doctype": "Candidate Match Log",
            "job_opening": job.name,
            "total_matches": len(matches),
            "top_candidate": matches[0]["candidate_name"] if matches else "",
            "top_fit_score": matches[0]["ai_fit_score"] if matches else 0
        })
        log.insert(ignore_permissions=True)
    except Exception:
        pass

    return {
        "job_title": job.job_title,
        "total_found": len(matches),
        "matches": matches
    }


@frappe.whitelist()
def search_candidates_api(job_description: str, required_skills: str = None, top_k: int = 5):
    """
    REST API endpoint equivalent to the internship FastAPI /api/v1/search endpoint.
    Accessible via POST /api/method/talent_matcher.api.search_candidates_api
    """
    skills_list = []
    if required_skills:
        if isinstance(required_skills, str):
            try:
                skills_list = json.loads(required_skills)
            except Exception:
                skills_list = [s.strip() for s in required_skills.split(",") if s.strip()]
        elif isinstance(required_skills, list):
            skills_list = required_skills

    matches = SearchEngine.search_candidates(
        job_description=job_description,
        required_skills=skills_list,
        top_k=int(top_k)
    )
    return {
        "total_found": len(matches),
        "matches": matches
    }
