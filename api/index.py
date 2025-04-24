from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Add parent directory to path so we can import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import routes from backend
from api.upload import router as upload_router
from api.query import router as query_router

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

# Include routers
app.include_router(upload_router)
app.include_router(query_router)

@app.get("/")
async def root():
    return {
        "message": "RAG API is running. Available endpoints: /upload, /query",
        "status": "ok"
    }

# For Vercel serverless deployment
from mangum import Adapter
handler = Adapter(app) 