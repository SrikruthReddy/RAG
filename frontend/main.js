document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const files = document.getElementById('pdf-files').files;
    if (!files.length) return;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('pdfs', files[i]);
    }
    
    // Try Replit backend first, then fallback to local
    const backends = [
        'https://rag-backend.yourusername.repl.co',  // Update with your actual Replit URL
        'http://localhost:8000'
    ];
    
    let uploaded = false;
    for (const backendUrl of backends) {
        try {
            const res = await fetch(`${backendUrl}/upload`, {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById('results').innerText = data.message || 'Upload complete.';
                uploaded = true;
                break;
            }
        } catch (err) {
            console.log(`Failed to upload to ${backendUrl}:`, err);
        }
    }
    
    if (!uploaded) {
        document.getElementById('results').innerText = 'Failed to upload files. Backend server may be unavailable.';
    }
});

document.getElementById('query-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const query = document.getElementById('query').value;
    
    // Try Replit backend first, then fallback to local
    const backends = [
        'https://rag-backend.yourusername.repl.co',  // Update with your actual Replit URL
        'http://localhost:8000'
    ];
    
    let queried = false;
    for (const backendUrl of backends) {
        try {
            const res = await fetch(`${backendUrl}/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById('results').innerText = data.answer || 'No answer found.';
                queried = true;
                break;
            }
        } catch (err) {
            console.log(`Failed to query ${backendUrl}:`, err);
        }
    }
    
    if (!queried) {
        document.getElementById('results').innerText = 'Failed to execute query. Backend server may be unavailable.';
    }
}); 