import os
import tempfile
from typing import List
from dotenv import load_dotenv
from fastapi import APIRouter, File, UploadFile, HTTPException
import fitz  # PyMuPDF
import google.generativeai as genai
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase and Gemini
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Constants
GEMINI_EMBED_MODEL = "models/text-embedding-004"

# Create router
router = APIRouter()

# Helper functions
def extract_text_from_pdf(path: str) -> str:
    with fitz.open(path) as doc:
        return "".join(page.get_text() for page in doc)

def embed(text: str, task: str) -> List[float]:
    return genai.embed_content(
        model=GEMINI_EMBED_MODEL,
        content=text,
        task_type=task
    )["embedding"]

@router.post("/upload")
async def upload_pdfs(pdfs: List[UploadFile] = File(...)):
    """Upload and process PDF files, extracting text and creating embeddings."""
    results = []
    
    for pdf in pdfs:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await pdf.read())
            tmp_path = tmp.name

        try:
            text = extract_text_from_pdf(tmp_path)
            vector = embed(text, "retrieval_document")

            payload = {
                "filename": pdf.filename,
                "content": text,
                "embedding": vector  # JSON list → vector column
            }
            
            result = supabase.table("documents").insert(payload).execute()
            
            results.append({
                "filename": pdf.filename,
                "status": "success"
            })

        except Exception as e:
            results.append({
                "filename": pdf.filename,
                "status": "error",
                "error": str(e)
            })
            
        finally:
            os.remove(tmp_path)

    return {"message": "PDFs processed", "results": results} 