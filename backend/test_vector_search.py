import os
from supabase import create_client, Client
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
SUPABASE_URL = os.getenv('SUPABASE_URL', 'YOUR_SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'YOUR_SUPABASE_SERVICE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

GEMINI_EMBED_MODEL = "models/text-embedding-004"

def get_documents():
    """Get all documents from the database"""
    response = supabase.table('documents').select('id', 'filename').execute()
    return response.data

def get_embedding(text):
    """Get embedding for text"""
    embedding_response = genai.embed_content(
        model=GEMINI_EMBED_MODEL,
        content=text,
        task_type="retrieval_query"
    )
    return embedding_response['embedding']

def try_direct_vector_search(query, top_k=5):
    """Try vector search using direct SQL"""
    print(f"\nSearching for: {query}")
    query_embedding = get_embedding(query)
    print(f"Generated embedding with length: {len(query_embedding)}")
    
    # Format vector for SQL
    vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    try:
        # Try method 1: Using ::vector cast with rpc
        sql = """
        SELECT id, filename, 
               1 - (embedding <=> $1::vector) as similarity 
        FROM documents 
        ORDER BY similarity DESC
        LIMIT $2
        """
        result1 = supabase.rpc('exec_sql', {
            'sql_query': sql,
            'params': [vector_str, top_k]
        }).execute()
        print("\nMethod 1 (::vector cast with rpc):")
        print(f"Found {len(result1.data) if result1.data else 0} results")
        if result1.data:
            for doc in result1.data:
                print(f"  {doc['filename']} (similarity: {doc.get('similarity', 'N/A')})")
    except Exception as e:
        print(f"Method 1 failed: {e}")

    try:
        # Try method 2: Using RPC function
        result2 = supabase.rpc('match_documents', {
            'query_embedding': vector_str,
            'match_count': top_k
        }).execute()
        print("\nMethod 2 (match_documents RPC):")
        print(f"Found {len(result2.data) if result2.data else 0} results")
        if result2.data:
            for doc in result2.data:
                print(f"  {doc.get('filename', 'Unknown')} (similarity: {doc.get('similarity', 'N/A')})")
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    try:
        # Try method 3: Using a custom SQL query via the rpc
        sql = f"""
        WITH query_embedding AS (
            SELECT '{vector_str}'::vector AS vec
        )
        SELECT id, filename, 
               1 - (embedding <=> query_embedding.vec) as similarity 
        FROM documents, query_embedding 
        WHERE embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT {top_k}
        """
        result3 = supabase.postgrest.rpc("execute_sql", { "query": sql }).execute()
        print("\nMethod 3 (custom SQL via RPC):")
        print(f"Found {len(result3.data) if result3.data else 0} results")
        if result3.data:
            for row in result3.data:
                print(row)
    except Exception as e:
        print(f"Method 3 failed: {e}")
        
    # Test if the match_documents function actually exists
    try:
        result = supabase.table("supabase_functions") \
                .select("schema_name, function_name") \
                .ilike("function_name", "match%") \
                .execute()
        print("\nFunctions with 'match' in name:")
        print(result.data)
    except Exception as e:
        print(f"Function lookup failed: {e}")

if __name__ == "__main__":
    print("Documents in database:")
    docs = get_documents()
    for doc in docs:
        print(f"  {doc['id']}: {doc['filename']}")
    
    try_direct_vector_search("What is the radius of Mercury?")
    try_direct_vector_search("Tell me about Mercury's orbit")
    try_direct_vector_search("Mercury temperature") 