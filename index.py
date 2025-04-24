import os
import tempfile
from typing import List, Union
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import google.generativeai as genai
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase and Gemini
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY]):
    raise ValueError("Missing required environment variables. Please check your environment variables.")

genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Constants
GEMINI_LLM_MODEL = "gemini-2.5-flash-preview-04-17"
GEMINI_EMBED_MODEL = "models/text-embedding-004"

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def to_pgvector(vec: List[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

def parse_embedding(emb: Union[str, List[float]]) -> List[float]:
    """
    Ensure embedding is a list of floats, parsing if it's a string.
    """
    if isinstance(emb, list):
        return emb
    if isinstance(emb, str):
        # strip brackets and split
        try:
            vals = emb.strip('[]').split(',')
            return [float(x) for x in vals if x]
        except Exception:
            print(f"Failed to parse embedding string: {emb[:100]}")
    return []

def search_supabase(query: str, k: int = 5) -> List[dict]:
    # 1) Try RPC
    q_vec = embed(query, "retrieval_query")
    q_vec_str = to_pgvector(q_vec)

    try:
        resp = supabase.rpc("match_documents", {
            "query_embedding": q_vec_str,
            "match_count": k
        }).execute()
        rows = resp.data or []
        if rows:
            return rows
    except Exception as e:
        print(f"RPC call failed, falling back: {e}")

    # 2) Fallback: manual cosine similarity
    docs = supabase.table("documents") \
        .select("id, filename, content, embedding") \
        .execute() \
        .data or []

    results = []
    for d in docs:
        emb_list = parse_embedding(d.get("embedding"))
        if len(emb_list) != len(q_vec):
            continue
        dot = sum(a*b for a,b in zip(q_vec, emb_list))
        norm_q = sum(a*a for a in q_vec) ** 0.5
        norm_emb = sum(b*b for b in emb_list) ** 0.5
        sim = dot / (norm_q * norm_emb) if norm_q and norm_emb else 0.0
        results.append({
            "id": d.get("id"),
            "filename": d.get("filename"),
            "content": d.get("content"),
            "similarity": sim
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:k]

def generate_answer(query: str) -> str:
    matches = search_supabase(query)
    if not matches:
        return "I couldn't find any relevant documents."

    context = "\n---\n".join(m["content"][:1800] for m in matches)
    prompt = f"""You are an assistant. Use the following documents to answer the question.

{context}

Question: {query}
Answer:"""

    llm = genai.GenerativeModel(GEMINI_LLM_MODEL)
    result = llm.generate_content(prompt)
    return result.text.strip()

# Routes
@app.get("/")
async def root():
    return {
        "message": "RAG API is running. Available endpoints: /upload, /query, /clear",
        "status": "ok"
    }

@app.post("/upload")
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

@app.post("/query")
async def query_api(request: Request):
    """Query the RAG system with a natural language question."""
    try:
        data = await request.json()
        query = data.get("query")
        
        if not query:
            return JSONResponse(status_code=400, content={"error": "Query is required."})

        answer = generate_answer(query)
        return {"answer": answer}
    
    except Exception as e:
        print(f"Unhandled error while answering query: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/clear")
async def clear_database():
    """Clear all documents from the database by using a query to fetch all IDs first."""
    try:
        # First, get all document IDs
        result = supabase.table("documents").select("id").execute()
        
        if not result.data:
            return {
                "message": "Database is already empty.",
                "status": "success",
                "count": 0
            }
        
        # Get the list of IDs
        ids = [item['id'] for item in result.data]
        
        # Delete the documents using IN operator
        delete_result = supabase.table("documents").delete().in_("id", ids).execute()
        
        deleted_count = len(ids)
        
        return {
            "message": f"Database cleared successfully. {deleted_count} documents removed.",
            "status": "success",
            "count": deleted_count
        }
    except Exception as e:
        print(f"Error clearing database: {e}")
        return JSONResponse(
            status_code=500, 
            content={"error": f"Failed to clear database: {str(e)}"}
        ) 