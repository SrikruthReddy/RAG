import os
import re
import base64
import json
import psycopg2
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
genai.configure(api_key=GEMINI_API_KEY)

# Extract connection details from Supabase service key (if available)
def get_connection_details():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
        return None
    
    # Try to parse the host from the URL
    host_match = re.match(r'https://([^\.]+)\.supabase\.co', SUPABASE_URL)
    if not host_match:
        print(f"ERROR: Could not parse host from Supabase URL: {SUPABASE_URL}")
        return None
    
    project_id = host_match.group(1)
    host = f"db.{project_id}.supabase.co"
    
    # Try to extract password from service key
    try:
        # The service key is in the format: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByb2plY3QtaWQiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjgzMDQyMTAxLCJleHAiOjE5OTg2MTgxMDF9.SECRET_PART
        jwt_parts = SUPABASE_SERVICE_KEY.split('.')
        if len(jwt_parts) < 2:
            print("ERROR: Invalid service key format")
            return None
        
        # Get the payload part of the JWT
        payload = jwt_parts[1]
        # Add padding if needed
        padding = '=' * (4 - len(payload) % 4)
        payload = payload + padding
        
        decoded_payload = base64.b64decode(payload)
        payload_data = json.loads(decoded_payload)
        
        # Check if password info is in the claims
        password = payload_data.get('password', 'postgres')  # Default to 'postgres' if not found
        
        return {
            'host': host,
            'port': '5432',
            'user': 'postgres',  # Supabase uses postgres as the default user
            'password': SUPABASE_SERVICE_KEY,  # Use the full service key as password for now
            'database': 'postgres'  # Supabase uses postgres as the default database name
        }
    except Exception as e:
        print(f"ERROR: Failed to extract connection details: {e}")
        return None

# Manual connection details - use if automatic extraction fails
def get_manual_connection_details():
    return {
        'host': os.getenv('SUPABASE_HOST', ''),
        'port': os.getenv('SUPABASE_PORT', '5432'),
        'user': os.getenv('SUPABASE_USER', 'postgres'),
        'password': os.getenv('SUPABASE_PASSWORD', ''),
        'database': os.getenv('SUPABASE_DATABASE', 'postgres')
    }

GEMINI_EMBED_MODEL = "models/text-embedding-004"

def create_match_documents_function():
    """Create the match_documents function in Supabase if it doesn't exist"""
    conn_details = get_connection_details() or get_manual_connection_details()
    
    if not conn_details or not conn_details['host'] or not conn_details['password']:
        print("ERROR: Could not determine database connection details. Please check your .env file.")
        return
    
    print(f"Connecting to database at {conn_details['host']}...")
    
    try:
        conn = psycopg2.connect(
            host=conn_details['host'],
            port=conn_details['port'],
            database=conn_details['database'],
            user=conn_details['user'],
            password=conn_details['password']
        )
        
        # First check if pgvector extension is installed
        cursor = conn.cursor()
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        if not cursor.fetchone():
            print("pgvector extension not found, installing...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
            print("pgvector extension installed")
        else:
            print("pgvector extension is already installed")
        
        # Create the match_documents function
        cursor.execute("""
        CREATE OR REPLACE FUNCTION match_documents(
            query_embedding TEXT,
            match_count INT DEFAULT 5
        ) RETURNS TABLE (
            id BIGINT,
            filename TEXT,
            content TEXT,
            similarity REAL
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                d.id,
                d.filename,
                d.content,
                1 - (d.embedding <=> query_embedding::vector) AS similarity
            FROM
                documents d
            WHERE d.embedding IS NOT NULL
            ORDER BY
                d.embedding <=> query_embedding::vector
            LIMIT match_count;
        END;
        $$;
        """)
        conn.commit()
        print("Successfully created match_documents function")
        
        # Verify documents table has vector column
        cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'documents'
        """)
        columns = cursor.fetchall()
        print("Table schema for 'documents':")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
        
        # Check a sample document
        cursor.execute("SELECT id, filename, embedding FROM documents LIMIT 1")
        doc = cursor.fetchone()
        if doc:
            print(f"\nSample document: ID={doc[0]}, filename={doc[1]}")
            embedding = doc[2]
            if embedding:
                if isinstance(embedding, list):
                    print(f"Embedding is a list with {len(embedding)} dimensions")
                else:
                    print(f"Embedding is of type {type(embedding)}")
            else:
                print("No embedding found for this document")
        else:
            print("No documents found in the table")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def test_vector_search(query):
    """Test vector search with direct SQL"""
    conn_details = get_connection_details() or get_manual_connection_details()
    
    if not conn_details or not conn_details['host'] or not conn_details['password']:
        print("ERROR: Could not determine database connection details. Please check your .env file.")
        return
    
    try:
        # Get embedding from Gemini
        embedding_response = genai.embed_content(
            model=GEMINI_EMBED_MODEL,
            content=query,
            task_type="retrieval_query"
        )
        embedding = embedding_response['embedding']
        print(f"Generated embedding with {len(embedding)} dimensions")
        
        # Format vector for Postgres
        vector_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        # Connect to database
        conn = psycopg2.connect(
            host=conn_details['host'],
            port=conn_details['port'],
            database=conn_details['database'],
            user=conn_details['user'],
            password=conn_details['password']
        )
        
        cursor = conn.cursor()
        
        # Test with direct SQL query
        print("\nTesting vector search with direct SQL...")
        cursor.execute(f"""
        SELECT id, filename, 1 - (embedding <=> '{vector_str}'::vector) AS similarity
        FROM documents
        WHERE embedding IS NOT NULL 
        ORDER BY embedding <=> '{vector_str}'::vector
        LIMIT 5
        """)
        
        results = cursor.fetchall()
        print(f"Found {len(results)} results:")
        for row in results:
            print(f"  ID: {row[0]}, Filename: {row[1]}, Similarity: {row[2]}")
        
        # Test with the match_documents function
        print("\nTesting vector search with match_documents function...")
        cursor.execute(f"""
        SELECT * FROM match_documents('{vector_str}', 5)
        """)
        
        results = cursor.fetchall()
        print(f"Found {len(results)} results:")
        for row in results:
            print(f"  ID: {row[0]}, Filename: {row[1]}, Similarity: {row[3]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    # First create/update the match_documents function
    create_match_documents_function()
    
    # Then test some queries
    print("\n=== Testing vector search ===")
    test_vector_search("What is the radius of Mercury?")
    test_vector_search("Tell me about Mercury's orbit")
    test_vector_search("Mercury temperature") 