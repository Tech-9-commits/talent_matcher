import io
import pypdf
import docx

class DocumentParser:
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        """Extracts clean plain text from PDF and DOCX files."""
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