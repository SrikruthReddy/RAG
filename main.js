// Backend API URL - will be replaced with deployed backend URL
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8000' 
    : 'https://rag-backend.onrender.com';

// Check if the backend is available
let backendAvailable = false;

// Try to connect to the backend
async function checkBackend() {
    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: 'test' }),
            // Short timeout to avoid long wait if backend is down
            signal: AbortSignal.timeout(3000)
        });
        backendAvailable = response.ok;
        console.log(`Backend is ${backendAvailable ? 'available' : 'unavailable'}`);
    } catch (error) {
        console.log('Backend check failed:', error);
        backendAvailable = false;
    }
}

// Check backend availability when page loads
checkBackend();

// Handle file upload
document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const files = document.getElementById('pdf-files').files;
    if (!files.length) return;
    
    // If backend is available, use it
    if (backendAvailable) {
        document.getElementById('results').innerHTML = `<div>Uploading ${files.length} file(s)...</div>`;
        
        try {
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('pdfs', files[i]);
            }
            
            const res = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                body: formData
            });
            
            if (res.ok) {
                const data = await res.json();
                document.getElementById('results').innerHTML = `
                    <div>
                        <h3>Upload Successful</h3>
                        <p>${data.message || 'Upload complete.'}</p>
                    </div>
                `;
            } else {
                throw new Error(`Server responded with ${res.status}`);
            }
        } catch (error) {
            console.error('Upload failed:', error);
            document.getElementById('results').innerHTML = `
                <div class="error-message">
                    <h3>Upload Failed</h3>
                    <p>Error: ${error.message}</p>
                    <p>The backend server might be unavailable.</p>
                </div>
            `;
        }
    } else {
        // GitHub Pages static demo
        document.getElementById('results').innerHTML = `
            <div class="demo-message">
                <h3>GitHub Pages Demo Mode</h3>
                <p>This is a static demo hosted on GitHub Pages.</p>
                <p>Full functionality requires the backend server which handles PDF processing.</p>
                <p>File upload simulation complete for ${files.length} file(s).</p>
            </div>
        `;
    }
});

// Handle query submission
document.getElementById('query-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const query = document.getElementById('query').value;
    
    // If backend is available, use it
    if (backendAvailable) {
        document.getElementById('results').innerHTML = `<div>Processing query...</div>`;
        
        try {
            const res = await fetch(`${API_URL}/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            
            if (res.ok) {
                const data = await res.json();
                document.getElementById('results').innerHTML = `
                    <div>
                        <h3>Query Results</h3>
                        <p class="query-text">Query: "${query}"</p>
                        <div class="answer">${data.answer || 'No answer found.'}</div>
                    </div>
                `;
            } else {
                throw new Error(`Server responded with ${res.status}`);
            }
        } catch (error) {
            console.error('Query failed:', error);
            document.getElementById('results').innerHTML = `
                <div class="error-message">
                    <h3>Query Failed</h3>
                    <p>Error: ${error.message}</p>
                    <p>The backend server might be unavailable.</p>
                </div>
            `;
        }
    } else {
        // GitHub Pages static demo
        document.getElementById('results').innerHTML = `
            <div class="demo-message">
                <h3>GitHub Pages Demo Mode</h3>
                <p>This is a static demo hosted on GitHub Pages.</p>
                <p>Query: "${query}"</p>
                <p>In the full version, this would return relevant information from your uploaded PDFs using RAG technology.</p>
                <p>To use the complete functionality:</p>
                <ol>
                    <li>Clone the repository: <code>git clone https://github.com/SrikruthReddy/RAG.git</code></li>
                    <li>Set up the backend server following instructions in the README</li>
                    <li>Run the application locally</li>
                </ol>
            </div>
        `;
    }
}); 