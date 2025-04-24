# Backend for PDF RAG Search

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_KEY`: Your Supabase service key
   - `OPENAI_API_KEY`: Your OpenAI API key

   You can set these in your shell or in a `.env` file (use a package like `python-dotenv` if you want to load from `.env`).

3. **Supabase Table Setup:**
   - Create the `documents` table and index in your Supabase SQL editor:
     ```sql
     create table documents (
       id bigserial primary key,
       filename text,
       content text,
       embedding vector(1536)
     );
     create index documents_embedding_idx on documents
     using ivfflat (embedding vector_cosine_ops)
     with (lists = 100);
     ```
   - Add the similarity search function:
     ```sql
     create or replace function match_documents(query_embedding vector(1536), match_count int)
     returns table(id bigint, filename text, content text, similarity float)
     language plpgsql as $$
     begin
       return query
       select 
         id,
         filename,
         content,
         1 - (documents.embedding <=> query_embedding) as similarity
       from documents
       order by documents.embedding <=> query_embedding
       limit match_count;
     end;
     $$;
     ```

4. **Run the backend:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Endpoints
- `POST /upload`: Upload one or more PDF files.
- `POST /query`: Query the documents with a question. 