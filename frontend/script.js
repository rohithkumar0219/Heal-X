// ========== NAVIGATION ==========
const menuItems = document.querySelectorAll('.menu-item');
const pages = document.querySelectorAll('.page');
const pageTitle = document.getElementById('pageTitle');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');
const hamburger = document.getElementById('hamburger');

const titles = { home: 'Home', text: 'Symptom Check', image: 'Image Scan', voice: 'Voice' };

function goTo(id) {
    menuItems.forEach(m => m.classList.toggle('active', m.dataset.page === id));
    pages.forEach(p => p.classList.toggle('active', p.id === `page-${id}`));
    pageTitle.textContent = titles[id] || id;
    closeSidebar();
    if (id === 'home') refreshHome();
}
window.goTo = goTo; // expose for onclick

menuItems.forEach(m => m.addEventListener('click', () => goTo(m.dataset.page)));
hamburger.addEventListener('click', () => { sidebar.classList.add('open'); overlay.classList.add('show'); });
function closeSidebar() { sidebar.classList.remove('open'); overlay.classList.remove('show'); }
overlay.addEventListener('click', closeSidebar);


// ========== HISTORY (localStorage) ==========
function getHistory() { return JSON.parse(localStorage.getItem('healx') || '[]'); }
function addHistory(type, preview) {
    const h = getHistory();
    h.unshift({ type, preview: preview.substring(0, 60), time: new Date().toLocaleString() });
    if (h.length > 10) h.length = 10;
    localStorage.setItem('healx', JSON.stringify(h));
}

function refreshHome() {
    const h = getHistory();
    document.getElementById('statTotal').textContent = h.length;
    document.getElementById('statLast').textContent = h.length ? h[0].time.split(',')[0] : '—';

    const list = document.getElementById('historyList');
    if (!h.length) { list.innerHTML = '<p class="empty-msg">No activity yet. Try a health check!</p>'; return; }
    list.innerHTML = h.map(i => `
        <div class="history-item">
            <span class="history-dot ${i.type}"></span>
            <span class="history-text">${i.preview}</span>
            <span class="history-time">${i.time}</span>
        </div>`).join('');
}
refreshHome();


// ========== SHARED ==========
function showLoading() { document.getElementById('loader').classList.remove('hidden'); }
function hideLoading() { document.getElementById('loader').classList.add('hidden'); }

function renderResult(data, container) {
    container.classList.remove('hidden');
    let html = '';

    // Audio bar
    if (data.audio_url) {
        html += `<div class="audio-bar">
            <button onclick="this.nextElementSibling.paused ? this.nextElementSibling.play() : this.nextElementSibling.pause()">▶</button>
            <audio src="${data.audio_url}"></audio>
            <span>Listen to response</span>
        </div>`;
    }

    // Explanation
    html += `<h3>Analysis</h3><div class="result-text">${data.explanation || data.response || ''}</div>`;

    // Conditions
    if (data.possible_conditions && data.possible_conditions.length) {
        html += '<h3 style="margin-top:20px">Possible Conditions</h3><div>';
        data.possible_conditions.forEach(c => {
            const label = typeof c === 'string' ? c : c.name;
            html += `<span class="condition-chip">${label}</span>`;
        });
        html += '</div>';
    }

    // Precautions
    if (data.precautions && data.precautions.length) {
        html += '<h3 style="margin-top:20px">Precautions</h3>';
        data.precautions.forEach(p => { html += `<div class="precaution-item">${p}</div>`; });
    }

    container.innerHTML = html;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


// ========== TEXT ==========
document.getElementById('txtBtn').addEventListener('click', async () => {
    const q = document.getElementById('txtInput').value.trim();
    if (!q) return;
    showLoading();
    try {
        const res = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: q, include_audio: document.getElementById('txtAudio').checked })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Request failed');
        renderResult(data, document.getElementById('txtResult'));
        addHistory('symptom', q);
    } catch (e) { alert(e.message); }
    finally { hideLoading(); }
});


// ========== IMAGE ==========
const dropZone = document.getElementById('dropZone');
const imgFile = document.getElementById('imgFile');
const imgPreview = document.getElementById('imgPreview');
const imgWrap = document.getElementById('imgPreviewWrap');
const dropPrompt = document.getElementById('dropPrompt');
const imgBtn = document.getElementById('imgBtn');
let chosenFile = null;

dropZone.addEventListener('click', () => imgFile.click());

imgFile.addEventListener('change', e => {
    if (e.target.files[0]) showImgPreview(e.target.files[0]);
});

// Drag & drop
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.borderColor = 'var(--accent)'; });
dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = ''; });
dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.style.borderColor = '';
    if (e.dataTransfer.files[0]) showImgPreview(e.dataTransfer.files[0]);
});

function showImgPreview(file) {
    chosenFile = file;
    const reader = new FileReader();
    reader.onload = e => { imgPreview.src = e.target.result; };
    reader.readAsDataURL(file);
    imgWrap.classList.remove('hidden');
    dropPrompt.classList.add('hidden');
    imgBtn.disabled = false;
}

document.getElementById('imgRemove').addEventListener('click', e => {
    e.stopPropagation();
    chosenFile = null;
    imgFile.value = '';
    imgWrap.classList.add('hidden');
    dropPrompt.classList.remove('hidden');
    imgBtn.disabled = true;
});

imgBtn.addEventListener('click', async () => {
    if (!chosenFile) return;
    showLoading();
    const fd = new FormData();
    fd.append('image', chosenFile);
    fd.append('query', document.getElementById('imgQuery').value || 'Analyze this medical image');
    try {
        const res = await fetch('/api/analyze-image', { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Request failed');
        renderResult(data, document.getElementById('imgResult'));
        addHistory('image', 'Image analysis');
    } catch (e) { alert(e.message); }
    finally { hideLoading(); }
});


// ========== VOICE ==========
const micBtn = document.getElementById('micBtn');
const micStatus = document.getElementById('micStatus');
const pulseRing = document.getElementById('pulseRing');
const voiceBtn = document.getElementById('voiceBtn');
let recorder, chunks = [], recording = false, audioBlob = null;
let recordingTimer = null, recordingSeconds = 0;
let selectedMimeType = 'audio/webm';

// Negotiate the best supported mimeType/codec
function getSupportedMimeType() {
    const types = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
    ];
    for (const type of types) {
        if (MediaRecorder.isTypeSupported(type)) return type;
    }
    return '';  // let browser pick default
}

function startRecordingTimer() {
    recordingSeconds = 0;
    micStatus.textContent = 'Listening… 0s';
    recordingTimer = setInterval(() => {
        recordingSeconds++;
        micStatus.textContent = `Listening… ${recordingSeconds}s`;
    }, 1000);
}

function stopRecordingTimer() {
    clearInterval(recordingTimer);
    recordingTimer = null;
}

micBtn.addEventListener('click', async () => {
    if (!recording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            selectedMimeType = getSupportedMimeType();
            const options = selectedMimeType ? { mimeType: selectedMimeType } : {};
            recorder = new MediaRecorder(stream, options);
            // Update to actual mimeType chosen by browser
            selectedMimeType = recorder.mimeType || 'audio/webm';
            chunks = [];

            recorder.ondataavailable = e => {
                if (e.data && e.data.size > 0) chunks.push(e.data);
            };

            recorder.onerror = (e) => {
                console.error('MediaRecorder error:', e);
                micStatus.textContent = 'Recording error. Try again.';
                stopRecordingTimer();
                recording = false;
                micBtn.classList.remove('recording');
                pulseRing.classList.remove('active');
                stream.getTracks().forEach(t => t.stop());
            };

            recorder.onstop = () => {
                stopRecordingTimer();
                if (chunks.length === 0) {
                    micStatus.textContent = 'No audio captured. Try again.';
                    voiceBtn.disabled = true;
                    stream.getTracks().forEach(t => t.stop());
                    return;
                }
                audioBlob = new Blob(chunks, { type: selectedMimeType });
                const sizeMB = (audioBlob.size / 1024 / 1024).toFixed(2);
                voiceBtn.disabled = false;
                micStatus.textContent = `Recording ready (${recordingSeconds}s, ${sizeMB}MB). Click Send.`;
                stream.getTracks().forEach(t => t.stop()); // release mic
            };

            // Start standard recording (no timeslice) for better file integrity
            recorder.start();
            console.log(`Recording started with MIME type: ${selectedMimeType}`);
            recording = true;
            micBtn.classList.add('recording');
            pulseRing.classList.add('active');
            startRecordingTimer();
        } catch (err) {
            console.error('Microphone error:', err);
            alert('Microphone access denied or unavailable.');
        }
    } else {
        recorder.stop();
        recording = false;
        micBtn.classList.remove('recording');
        pulseRing.classList.remove('active');
    }
});

voiceBtn.addEventListener('click', async () => {
    if (!audioBlob) return;
    showLoading();
    // Determine file extension from mimeType
    const ext = selectedMimeType.includes('ogg') ? 'ogg' : selectedMimeType.includes('mp4') ? 'mp4' : 'webm';
    const fd = new FormData();
    fd.append('audio', audioBlob, `recording.${ext}`);
    try {
        const res = await fetch('/api/voice-query', { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Request failed');
        renderResult(data, document.getElementById('voiceResult'));
        addHistory('voice', data.metadata?.transcription || 'Voice consultation');
    } catch (e) { alert(e.message); }
    finally { hideLoading(); }
});
