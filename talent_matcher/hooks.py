app_name = "talent_matcher"
app_title = "Talent Matcher"
app_publisher = "Talent Matcher"
app_description = "AI Resume Parsing & Semantic Candidate Matching for ERPNext HRMS"
app_email = "admin@example.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# DocType JavaScript triggers (Inject custom UI buttons & matching dialogs)
doctype_js = {
    "Job Applicant": "public/js/job_applicant.js",
    "Job Opening": "public/js/job_opening.js"
}

# Document Events (Automated triggers when docs are created/updated)
doc_events = {
    "Job Applicant": {
        "after_insert": "talent_matcher.api.on_job_applicant_created"
    }
}
