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

// File upload handler
document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const files = document.getElementById('pdf-files').files;
    if (!files.length) return;
    
    document.getElementById('results').innerText = 'Uploading files...';
    
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('pdfs', files[i]);
    }
    
    try {
        const res = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) {
            throw new Error(`Server responded with status: ${res.status}`);
        }
        
        const data = await res.json();
        document.getElementById('results').innerText = data.message || 'Upload complete.';
    } catch (error) {
        console.error('Upload error:', error);
        document.getElementById('results').innerText = `Error: ${error.message}`;
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
        document.getElementById('results').innerText = data.message || 'Database cleared successfully.';
    } catch (error) {
        console.error('Clear database error:', error);
        document.getElementById('results').innerText = `Error: ${error.message}`;
    }
});

// Query handler
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
        document.getElementById('results').innerText = data.answer || 'No answer found.';
    } catch (error) {
        console.error('Query error:', error);
        document.getElementById('results').innerText = `Error: ${error.message}`;
    }
}); 