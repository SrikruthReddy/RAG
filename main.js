// Get the API URL based on the current environment
const getApiUrl = () => {
    // If running on Vercel, use relative URLs
    if (window.location.hostname.includes('vercel.app')) {
        return '';  // Empty string means use relative URLs (same domain)
    }
    // If running on GitHub Pages
    else if (window.location.hostname.includes('github.io')) {
        return 'https://rag-iota-jade.vercel.app';  // Your actual Vercel deployment URL
    }
    // Local development
    return 'http://localhost:8000';
};

const API_URL = getApiUrl();

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
    
    document.getElementById('results').innerText = 'Uploading files...';
    
    try {
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('pdfs', files[i]);
        }
        
        const res = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) {
            throw new Error(`Server responded with status: ${res.status}`);
        }
        
        const data = await res.json();
        document.getElementById('results').innerHTML = `
            <div>
                <h3>Upload Successful</h3>
                <p>${data.message || 'Upload complete.'}</p>
            </div>
        `;
    } catch (error) {
        console.error('Upload error:', error);
        document.getElementById('results').innerHTML = `
            <div class="error-message">
                <h3>Upload Failed</h3>
                <p>Error: ${error.message}</p>
                <p>The backend server might be unavailable.</p>
            </div>
        `;
    }
});

// Clear database handler
document.getElementById('clear-db').addEventListener('click', async function() {
    if (!confirm('Are you sure you want to clear the database? This will delete all uploaded documents and cannot be undone.')) {
        return;
    }
    
    document.getElementById('results').innerText = 'Clearing database...';
    
    try {
        const res = await fetch(`${API_URL}/clear`, {
            method: 'POST'
        });
        
        if (!res.ok) {
            throw new Error(`Server responded with status: ${res.status}`);
        }
        
        const data = await res.json();
        document.getElementById('results').innerHTML = `
            <div>
                <h3>Database Cleared</h3>
                <p>${data.message || 'Database cleared successfully.'}</p>
            </div>
        `;
    } catch (error) {
        console.error('Clear database error:', error);
        document.getElementById('results').innerHTML = `
            <div class="error-message">
                <h3>Clear Database Failed</h3>
                <p>Error: ${error.message}</p>
                <p>The backend server might be unavailable.</p>
            </div>
        `;
    }
});

// Handle query submission
document.getElementById('query-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const query = document.getElementById('query').value;
    if (!query.trim()) return;
    
    document.getElementById('results').innerText = 'Processing query...';
    
    try {
        const res = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        if (!res.ok) {
            throw new Error(`Server responded with status: ${res.status}`);
        }
        
        const data = await res.json();
        document.getElementById('results').innerHTML = `
            <div>
                <h3>Query Results</h3>
                <p class="query-text">Query: "${query}"</p>
                <div class="answer">${data.answer || 'No answer found.'}</div>
            </div>
        `;
    } catch (error) {
        console.error('Query error:', error);
        document.getElementById('results').innerHTML = `
            <div class="error-message">
                <h3>Query Failed</h3>
                <p>Error: ${error.message}</p>
                <p>The backend server might be unavailable or you may need to wait for it to wake up from sleep mode (free tier limitation).</p>
            </div>
        `;
    }
}); 