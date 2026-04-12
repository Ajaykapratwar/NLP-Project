// State
let groqKey = localStorage.getItem('groqKey') || '';
let tavilyKey = localStorage.getItem('tavilyKey') || '';

// DOM Elements
const settingsModal = document.getElementById('settingsModal');
const groqKeyInput = document.getElementById('groqKey');
const tavilyKeyInput = document.getElementById('tavilyKey');
const saveKeysBtn = document.getElementById('saveKeysBtn');
const openSettings = document.getElementById('openSettings');

const tabs = document.querySelectorAll('.nav-links li[data-tab]');
const views = document.querySelectorAll('.view-section');

const chatHistory = document.getElementById('chatHistory');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const fileUploadInput = document.getElementById('fileUploadInput');
const urlInput = document.getElementById('urlInput');
const addUrlBtn = document.getElementById('addUrlBtn');

const csvInput = document.getElementById('csvInput');
const uploadCsvBtn = document.getElementById('uploadCsvBtn');
const csvStatus = document.getElementById('csvStatus');
const sqlQueryInput = document.getElementById('sqlQueryInput');
const askSqlBtn = document.getElementById('askSqlBtn');
const sqlTableContainer = document.getElementById('sqlTableContainer');
const sqlGeneratedCode = document.getElementById('sqlGeneratedCode');

const toast = document.getElementById('toast');

// Init
function checkKeys() {
    if (!groqKey || !tavilyKey) {
        settingsModal.classList.add('active');
    }
}
checkKeys();

// Settings
openSettings.addEventListener('click', () => {
    groqKeyInput.value = groqKey;
    tavilyKeyInput.value = tavilyKey;
    settingsModal.classList.add('active');
});

saveKeysBtn.addEventListener('click', () => {
    groqKey = groqKeyInput.value.trim();
    tavilyKey = tavilyKeyInput.value.trim();
    if(groqKey && tavilyKey) {
        localStorage.setItem('groqKey', groqKey);
        localStorage.setItem('tavilyKey', tavilyKey);
        settingsModal.classList.remove('active');
        showToast("Keys saved locally!");
    } else {
        alert("Please provide both keys.");
    }
});

// Routing
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        const target = tab.getAttribute('data-tab');
        views.forEach(v => v.style.display = 'none');
        document.getElementById(`${target}View`).style.display = 'flex';
    });
});

// Utils
function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => { toast.classList.remove('show'); }, 3000);
}

function getHeaders() {
    return {
        'X-Groq-Api-Key': groqKey,
        'X-Tavily-Api-Key': tavilyKey
    };
}

function appendMessage(role, content, sources=null) {
    const el = document.createElement('div');
    el.className = `message ${role}`;
    
    let avatarHTML = role === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
    
    let sourceHTML = '';
    if (sources && sources.length > 0) {
        sourceHTML = `<hr style="margin: 10px 0; border-color: rgba(255,255,255,0.1)">
                      <div style="font-size: 0.8rem; color: #94a3b8;">
                        <strong>Sources:</strong><br>
                        ${sources.map(s => `- ${s.source}`).join('<br>')}
                      </div>`;
    }

    el.innerHTML = `
        <div class="avatar">${avatarHTML}</div>
        <div class="msg-content">
            ${marked.parse(content)}
            ${sourceHTML}
        </div>
    `;
    
    chatHistory.appendChild(el);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Ensure marked.js is loaded dynamically or handled since we didn't add the tag.
// Actually, I'll just do basic text for now to avoid external script dependencies if marked fails.
const marked = {
    parse: text => `<p>${text.replace(/\n/g, '<br>')}</p>`
};

// RAG Uploads
fileUploadInput.addEventListener('change', async (e) => {
    if(!e.target.files.length) return;
    const formData = new FormData();
    for (const f of e.target.files) formData.append("files", f);
    
    showToast("Uploading documents...");
    try {
        const res = await fetch("/api/upload_files", { method: "POST", body: formData });
        const data = await res.json();
        showToast(data.message);
    } catch (err) {
        showToast("Upload failed.");
    }
});

addUrlBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if(!url) return;
    
    showToast("Processing URL...");
    try {
        const res = await fetch("/api/upload_urls", { 
            method: "POST", 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({urls: url})
        });
        const data = await res.json();
        showToast(data.message);
        urlInput.value = '';
    } catch (err) {
        showToast("URL processing failed.");
    }
});

// Chat Output
sendBtn.addEventListener('click', sendMsg);
chatInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') sendMsg(); });

async function sendMsg() {
    const query = chatInput.value.trim();
    if(!query) return;
    
    appendMessage('user', query);
    chatInput.value = '';
    
    const loadingId = 'loading-' + Date.now();
    const loadingEl = document.createElement('div');
    loadingEl.className = 'message assistant';
    loadingEl.id = loadingId;
    loadingEl.innerHTML = `<div class="avatar"><i class="fa-solid fa-robot"></i></div><div class="msg-content"><i class="fa-solid fa-circle-notch fa-spin"></i> Thinking...</div>`;
    chatHistory.appendChild(loadingEl);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getHeaders()
            },
            body: JSON.stringify({query})
        });
        const data = await res.json();
        document.getElementById(loadingId).remove();
        
        if(res.ok) {
            appendMessage('assistant', data.answer, data.sources);
        } else {
            appendMessage('assistant', `Error: ${data.detail || 'Unknown error'}`);
            if(res.status === 401) settingsModal.classList.add('active');
        }
    } catch(err) {
        document.getElementById(loadingId).remove();
        appendMessage('assistant', "Connection error.");
    }
}

// NLP 2 SQL functionality
document.querySelector('.upload-csv-box').addEventListener('click', () => {
    csvInput.click();
});

csvInput.addEventListener('change', (e) => {
    if(e.target.files.length) {
        csvStatus.innerHTML = `<span style="color: var(--accent)"><i class="fa-solid fa-file-circle-check"></i> ${e.target.files[0].name} selected</span>`;
    }
});

uploadCsvBtn.addEventListener('click', async () => {
    if(!csvInput.files.length) return showToast("Select a CSV file first!");
    const file = csvInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    
    showToast("Loading Data...");
    try {
        const res = await fetch('/api/upload_sql_csv', {
            method: 'POST',
            headers: getHeaders(), // Only needs headers
            body: formData
        });
        const data = await res.json();
        if(res.ok) {
            showToast(data.message);
        } else {
            showToast(data.detail);
        }
    } catch(err) {
        showToast("Error uploading file.");
    }
});

askSqlBtn.addEventListener('click', async () => {
    const q = sqlQueryInput.value.trim();
    if(!q) return;
    
    showToast("Generating query...");
    try {
        const res = await fetch('/api/nl2sql', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getHeaders()
            },
            body: JSON.stringify({query: q})
        });
        const data = await res.json();
        
        if(!res.ok) {
            showToast(data.detail);
            return;
        }
        
        if(data.error) {
            sqlTableContainer.innerHTML = `<div style="color:var(--accent-red); padding: 1rem;">${data.error}</div>`;
            return;
        }
        
        // Show SQL
        sqlGeneratedCode.style.display = 'block';
        sqlGeneratedCode.innerText = data.sql;
        
        // Render Table
        if(data.columns && data.data) {
            let html = '<table><thead><tr>';
            data.columns.forEach(c => html += `<th>${c}</th>`);
            html += '</tr></thead><tbody>';
            data.data.forEach(row => {
                html += '<tr>';
                row.forEach(cell => html += `<td>${cell}</td>`);
                html += '</tr>';
            });
            html += '</tbody></table>';
            sqlTableContainer.innerHTML = html;
        }
        
    } catch (err) {
        showToast("Query failed.");
    }
});
