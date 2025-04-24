# RAG (Retrieval-Augmented Generation)

A PDF search application that uses RAG (Retrieval-Augmented Generation) technology to enable semantic search through uploaded PDF documents.

## Demo

A static demo is available at: https://srikruthreddy.github.io/RAG/

Note: The GitHub Pages demo is a simplified version that showcases the UI. For full functionality, you need to set up the backend server.

## Features

- Upload multiple PDF documents
- Query the content of PDFs with natural language
- Get relevant answers extracted from your documents
- Semantic search powered by embeddings

## Project Structure

- `frontend/`: HTML, CSS, and JavaScript for the user interface
- `backend/`: Python code for the RAG pipeline

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

3. Start the backend server:
   ```
   cd backend
   python app.py
   ```

   The server will start at http://localhost:8000

### Frontend Setup

For local development, simply open the `index.html` file in your browser or use a local development server.

## How It Works

1. Upload your PDF files
2. The backend processes and indexes the content using embedding models
3. Query the system with natural language questions
4. The RAG system retrieves relevant context and generates accurate answers

## License

MIT 