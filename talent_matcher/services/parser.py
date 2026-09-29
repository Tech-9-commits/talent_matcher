import io
import os
import pypdf
import docx

class DocumentParser:
    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
        """Extracts clean plain text from PDF and DOCX bytes."""
        text = ""
        filename_lower = filename.lower()
        
        if filename_lower.endswith(".pdf"):
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
        elif filename_lower.endswith(".docx"):
            doc = docx.Document(io.BytesIO(file_bytes))
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text += paragraph.text + "\n"
                    
        else:
            raise ValueError("Unsupported file format. Please upload a .pdf or .docx file.")
            
        return text.strip()

    @staticmethod
    def extract_text_from_file_path(file_path: str) -> str:
        """Extracts text given a local absolute file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at path: {file_path}")
            
        with open(file_path, "rb") as f:
            content = f.read()
        return DocumentParser.extract_text_from_bytes(content, os.path.basename(file_path))
