document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const files = document.getElementById('pdf-files').files;
    if (!files.length) return;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('pdfs', files[i]);
    }
    const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData
    });
    const data = await res.json();
    document.getElementById('results').innerText = data.message || 'Upload complete.';
});

document.getElementById('query-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const query = document.getElementById('query').value;
    const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    });
    const data = await res.json();
    document.getElementById('results').innerText = data.answer || 'No answer found.';
}); 