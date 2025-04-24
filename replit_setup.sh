#!/bin/bash
# Setup script for Replit deployment

echo "Setting up RAG backend on Replit..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements-replit.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
  echo "Please set your environment variables in Replit's Secrets tab!"
  echo "Required variables: SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY"
fi

echo "Setup complete! You can now run the app." 