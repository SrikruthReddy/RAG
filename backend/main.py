import os
import tempfile
import logging
from typing import List, Union
from pprint import pformat

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fitz                          # PyMuPDF
import google.generativeai as genai
from supabase import create_client, Client

# ───────────────────────── CONFIG ────────────────────────── #
load_dotenv()

SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
GEMINI_API_KEY       = os.environ["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
# Debug requests - uncomment if needed after fixing structure
# import httpx
# def log_request(r: httpx.Request):
#     print("→", r.method, r.url, r.content)
# supabase.postgrest.client.http._client.event_xhooks["request"] = [log_request]

GEMINI_LLM_MODEL   = "gemini-2.5-flash-preview-04-17"
GEMINI_EMBED_MODEL = "models/text-embedding-004"
EMBED_DIM          = 768   # must match your vector column & RPC cast

# integrate with Uvicorn's logger
log = logging.getLogger("uvicorn.error")

# ──────────────────────  FASTAPI setup  ───────────────────── #
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────  Helper functions  ──────────────────── #
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

# ─────────────────────  Ingestion endpoint  ───────────────── #
@app.post("/upload")
async def upload_pdfs(pdfs: List[UploadFile] = File(...)):
    for pdf in pdfs:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await pdf.read())
            tmp_path = tmp.name

        try:
            text   = extract_text_from_pdf(tmp_path)
            vector = embed(text, "retrieval_document")

            payload = {
                "filename": pdf.filename,
                "content":  text,
                "embedding": vector   # JSON list → vector column
            }
            log.info("INSERT payload ➜ %s", pformat(payload)[:400])
            resp = supabase.table("documents").insert(payload).execute()
            log.info("INSERT result ➜ %s", resp.data)

        except Exception as e:
            log.exception("Error ingesting %s", pdf.filename)
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            os.remove(tmp_path)

    return {"message": "PDFs uploaded and processed successfully."}

# ─────────────────────  Retrieval helpers  ────────────────── #
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
            log.warning("Failed to parse embedding string: %s", emb[:100])
    return []


def search_supabase(query: str, k: int = 5) -> List[dict]:
    # 1) Try RPC
    q_vec     = embed(query, "retrieval_query")
    q_vec_str = to_pgvector(q_vec)

    log.info("RPC vector literal ➜ %s…", q_vec_str[:100])
    try:
        resp = supabase.rpc("match_documents", {
            "query_embedding": q_vec_str,
            "match_count":     k
        }).execute()
        rows = resp.data or []
        if rows:
            log.info("RPC returned %d rows", len(rows))
            return rows
        log.warning("RPC returned 0 rows, falling back to manual similarity")
    except Exception as e:
        log.error("RPC call failed, falling back: %s", e)

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
        dot      = sum(a*b for a,b in zip(q_vec, emb_list))
        norm_q   = sum(a*a for a in q_vec) ** 0.5
        norm_emb = sum(b*b for b in emb_list) ** 0.5
        sim = dot / (norm_q * norm_emb) if norm_q and norm_emb else 0.0
        results.append({
            "id": d.get("id"),
            "filename": d.get("filename"),
            "content": d.get("content"),
            "similarity": sim
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    log.info("Manual fallback found %d rows (returning top %d)", len(results), k)
    return results[:k]


def generate_answer(query: str) -> str:
    matches = search_supabase(query)
    if not matches:
        return "I couldn't find any relevant documents."

    context = "\n---\n".join(m["content"][:1800] for m in matches)
    prompt  = f"""You are an assistant. Use the following documents to answer the question.

{context}

Question: {query}
Answer:"""

    llm    = genai.GenerativeModel(GEMINI_LLM_MODEL)
    result = llm.generate_content(prompt)
    return result.text.strip()

# ───────────────────────  Query endpoint  ─────────────────── #
@app.post("/query")
async def query_api(request: Request):
    data  = await request.json()
    query = data.get("query")
    if not query:
        return JSONResponse(status_code=400, content={"error": "Query is required."})

    try:
        answer = generate_answer(query)
        return {"answer": answer}
    except Exception as e:
        log.exception("Unhandled error while answering query")
        return JSONResponse(status_code=500, content={"error": str(e)})
