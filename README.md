# RAG (Retrieval-Augmented Generation)

A PDF search application that uses RAG (Retrieval-Augmented Generation) technology to enable semantic search through uploaded PDF documents.

## Demo

A static demo is available at: https://srikruthreddy.github.io/RAG/

The frontend automatically checks if the backend is available. When available, it will use the deployed backend service to provide full functionality.

## Features

- Upload multiple PDF documents
- Query the content of PDFs with natural language
- Get relevant answers extracted from your documents
- Semantic search powered by embeddings
- Backend deployment on Render with Supabase for vector storage

## Deployment

This application has two components:

1. **Frontend**: Static site hosted on GitHub Pages
2. **Backend**: Python FastAPI application deployed on Render

### Backend Deployment (Render)

The backend is configured to be deployed on Render using the `render.yaml` file. To deploy your own instance:

1. Fork this repository
2. Create a Render account at https://render.com
3. Connect your GitHub account to Render
4. Create a new "Blueprint" instance pointing to your forked repo
5. Set the following environment variables:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_KEY`: Your Supabase service key
   - `GEMINI_API_KEY`: Your Google Gemini API key

### Supabase Configuration

The backend uses Supabase for vector storage. You'll need to:

1. Create a Supabase account and project
2. Create a table named `documents` with the following columns:
   - `id`: UUID, primary key
   - `filename`: Text
   - `content`: Text
   - `embedding`: Vector(768)
3. Create a stored procedure for vector similarity search:
   ```sql
   CREATE OR REPLACE FUNCTION match_documents(
     query_embedding vector(768),
     match_count int DEFAULT 5
   ) RETURNS TABLE (
     id UUID,
     filename TEXT,
     content TEXT,
     similarity FLOAT
   )
   LANGUAGE plpgsql
   AS $$
   BEGIN
     RETURN QUERY
     SELECT
       documents.id,
       documents.filename,
       documents.content,
       1 - (documents.embedding <=> query_embedding) as similarity
     FROM documents
     ORDER BY similarity DESC
     LIMIT match_count;
   END;
   $$;
   ```

## Project Structure

- `frontend/`: HTML, CSS, and JavaScript for the user interface
- `backend/`: Python code for the RAG pipeline
- `render.yaml`: Configuration for Render deployment

## Local Setup

### Prerequisites

- Python 3.8+
- Node.js (optional, for development)

### Backend Setup

1. Clone the repository:
   ```
   git clone https://github.com/SrikruthReddy/RAG.git
   cd RAG
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. Create a `.env` file in the backend directory with your API keys:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_key
   GEMINI_API_KEY=your_gemini_key
   ```

4. Start the backend server:
   ```
   cd backend
   uvicorn main:app --reload
   ```

   The server will start at http://localhost:8000

### Frontend Setup

For local development, simply open the `frontend/index.html` file in your browser or use a local development server.

## How It Works

1. Upload your PDF files
2. The backend processes and indexes the content using embedding models
3. Query the system with natural language questions
4. The RAG system retrieves relevant context and generates accurate answers

## License

MIT 