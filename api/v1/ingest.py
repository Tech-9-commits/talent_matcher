from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.parser import DocumentParser
from app.services.store import CandidateStore

router = APIRouter()

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Uploads a PDF/DOCX resume, parses text, and indexes it into local storage."""
    try:
        contents = await file.read()
        parsed_text = DocumentParser.extract_text(contents, file.filename)
        
        # Save to storage
        saved_record = CandidateStore.save_candidate(file.filename, parsed_text)
        
        return {
            "candidate_id": saved_record["candidate_id"],
            "filename": file.filename,
            "status": "successfully_parsed_and_stored",
            "extracted_length": len(parsed_text),
            "preview": parsed_text[:200] + "..."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))