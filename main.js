document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const files = document.getElementById('pdf-files').files;
    if (!files.length) return;
    
    // GitHub Pages static demo
    document.getElementById('results').innerHTML = `
        <div class="demo-message">
            <h3>GitHub Pages Demo Mode</h3>
            <p>This is a static demo hosted on GitHub Pages.</p>
            <p>Full functionality requires the backend server which handles PDF processing.</p>
            <p>File upload simulation complete for ${files.length} file(s).</p>
        </div>
    `;
});

document.getElementById('query-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const query = document.getElementById('query').value;
    
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
}); 