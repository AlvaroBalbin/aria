// ── ARIA Dashboard ────────────────────────────────────────────────────────────

const WS_URL = `ws://${location.hostname}:8000/ws/dashboard`;

let ws = null;
let currentState = 'idle';
let memoryCount = 0;
let ttsEnabled = false;
let pendingQuery = false; // suppress broadcast duplicates during direct queries

// ── Voice recording state ────────────────────────────────────────────────────

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let micStream = null;
let audioContext = null;
let analyser = null;
let recAnimFrame = null;
let recTimerInterval = null;
let recSeconds = 0;

// ── Ambient listening state ──────────────────────────────────────────────────

let ambientRecorder = null;
let ambientStream = null;
let isAmbient = false;
let wasAmbient = false; // resume after conversation

function toggleAmbient() {
  if (isAmbient) stopAmbient();
  else startAmbient();
}

let ambientInterval = null;

async function startAmbient() {
  try {
    ambientStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    isAmbient = true;

    document.getElementById('ambient-btn').classList.add('active');
    document.getElementById('ambient-btn').innerHTML = '<span id="ambient-dot" class="visible"></span>LISTENING';
    document.body.classList.add('ambient-active');
    handleState('idle');

    // Record in 8s windows: start → stop → send → start again
    // Each stop produces a valid standalone webm file
    startAmbientWindow();
    ambientInterval = setInterval(() => {
      if (isAmbient && ambientRecorder && ambientRecorder.state === 'recording') {
        ambientRecorder.stop(); // triggers onstop → send → restart
      }
    }, 8000);
  } catch (e) {
    console.error('Ambient mic denied:', e);
  }
}

function startAmbientWindow() {
  if (!ambientStream || !isAmbient) return;
  const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
    ? 'audio/webm;codecs=opus' : 'audio/webm';
  const chunks = [];
  ambientRecorder = new MediaRecorder(ambientStream, { mimeType });
  ambientRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) chunks.push(e.data);
  };
  ambientRecorder.onstop = () => {
    if (chunks.length > 0 && isAmbient) {
      const blob = new Blob(chunks, { type: mimeType });
      if (blob.size > 2000) sendAmbientChunk(blob);
    }
    // Start next window
    if (isAmbient) startAmbientWindow();
  };
  ambientRecorder.start();
}

function stopAmbient() {
  isAmbient = false;
  if (ambientInterval) { clearInterval(ambientInterval); ambientInterval = null; }
  if (ambientRecorder && ambientRecorder.state !== 'inactive') {
    ambientRecorder.onstop = null; // prevent restart
    ambientRecorder.stop();
  }
  if (ambientStream) { ambientStream.getTracks().forEach(t => t.stop()); ambientStream = null; }
  ambientRecorder = null;

  document.getElementById('ambient-btn').classList.remove('active');
  document.getElementById('ambient-btn').innerHTML = '<span id="ambient-dot"></span>AMBIENT';
  document.body.classList.remove('ambient-active');
  handleState('idle');
}

async function sendAmbientChunk(blob) {
  try {
    const fd = new FormData();
    fd.append('audio', blob, 'ambient.webm');
    await fetch('/ambient', { method: 'POST', body: fd });
  } catch (_) { /* silent */ }
}

// ── Clone recording state ────────────────────────────────────────────────────

let cloneRecorder = null;
let cloneChunks = [];
let isCloneRecording = false;
let cloneTimerInterval = null;
let cloneSeconds = 0;

// ── WebSocket ─────────────────────────────────────────────────────────────────

function connect() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.log('Connected to ARIA backend');
  };

  ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    if (msg.event === 'history')          handleHistory(msg);
    else if (msg.event === 'transcript')  handleTranscript(msg);
    else if (msg.event === 'pendant_state') handleState(msg.state);
  };

  ws.onclose = () => {
    console.log('Disconnected — reconnecting in 2s');
    setTimeout(connect, 2000);
  };
}

function handleHistory({ transcript, memories }) {
  transcript.forEach(addTranscriptEntry);
  if (memories) {
    memoryCount = memories.length;
    document.getElementById('memory-count').textContent = `${memoryCount} memories`;
    renderMemories(memories);
  }
}

function handleTranscript({ speaker, text, ts }) {
  addTranscriptEntry({ speaker, text, ts });
  // Only add ARIA messages to convo panel from broadcasts (pendant/ambient).
  // Direct queries (text chat, voice memo) add to convo panel themselves.
  if (speaker === 'ARIA' && !pendingQuery) {
    addConvoEntry({ speaker, text, ts });
  }
}

function handleState(state) {
  currentState = state;
  const badge = document.getElementById('status-badge');
  // When returning to idle, show AMBIENT in the badge if ambient mode is on
  if (state === 'idle' && isAmbient) {
    badge.textContent = 'AMBIENT';
    badge.className = 'speaking'; // green colour class
    document.body.className = 'ambient-active';
    return;
  }
  badge.textContent = state.toUpperCase();
  badge.className = state;
  document.body.className = state === 'speaking' ? 'speaking'
                           : isAmbient          ? 'ambient-active'
                           : '';
}

// ── DOM helpers ───────────────────────────────────────────────────────────────

function fmtTime(ts) {
  return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function makeEntry({ speaker, text, ts }) {
  const cls = speaker === 'ARIA' ? 'aria' : 'user';
  const div = document.createElement('div');
  div.className = `entry ${cls}`;
  div.innerHTML = `
    <div class="entry-speaker">${speaker}</div>
    <div class="entry-time">${fmtTime(ts)}</div>
    <div class="entry-bubble">${escHtml(text)}</div>
  `;
  return div;
}

function addTranscriptEntry(entry) {
  const panel = document.getElementById('transcript-panel');
  panel.appendChild(makeEntry(entry));
  panel.scrollTop = panel.scrollHeight;
}

function addConvoEntry(entry) {
  const panel = document.getElementById('convo-panel');
  panel.appendChild(makeEntry(entry));
  panel.scrollTop = panel.scrollHeight;
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function switchLeftTab(tabId) {
  document.getElementById('tab-transcript').classList.remove('active');
  document.getElementById('tab-memories').classList.remove('active');
  document.getElementById(`tab-${tabId}`).classList.add('active');

  document.getElementById('transcript-panel').style.display = 'none';
  document.getElementById('memories-panel').style.display = 'none';
  document.getElementById(`${tabId}-panel`).style.display = 'block';

  if (tabId === 'memories') {
    loadMemories();
  }
}

async function loadMemories() {
  try {
    const resp = await fetch('/memories');
    if (!resp.ok) return;
    const memories = await resp.json();
    memoryCount = memories.length;
    document.getElementById('memory-count').textContent = `${memoryCount} memories`;
    renderMemories(memories);
  } catch (e) {
    console.error('Failed to load memories:', e);
  }
}

function renderMemories(memories) {
  const panel = document.getElementById('memories-panel');
  if (!panel) return;
  panel.innerHTML = '';
  if (!memories || memories.length === 0) {
    panel.innerHTML = '<div style="color:#4b5563; font-size:12px; padding:20px;">No memories stored yet. Talk to ARIA!</div>';
    return;
  }
  
  // Sort by timestamp descending
  memories.sort((a, b) => b.ts - a.ts);
  
  memories.forEach(m => {
    const card = document.createElement('div');
    card.className = 'memory-card';
    const dateStr = new Date(m.ts * 1000).toLocaleString();
    card.innerHTML = `
      <div class="memory-key">${escHtml(m.key)}</div>
      <div class="memory-val">${escHtml(m.value)}</div>
      <div class="memory-time">${dateStr}</div>
    `;
    panel.appendChild(card);
  });
}

// ── Mood indicator ───────────────────────────────────────────────────────────

const MOOD_EMOJI = {
  curious: '?', happy: ':)', warm: '~', playful: ';)', thoughtful: '...',
  excited: '!', focused: '>', empathetic: '<3', amused: 'ha',
  reflective: '~', concerned: '..', neutral: '-',
};

function setMood(mood) {
  const el = document.getElementById('mood-indicator');
  if (!mood || mood === 'neutral') {
    el.classList.remove('visible');
    return;
  }
  el.textContent = `${mood}`;
  el.className = `visible ${mood}`;
}

// ── Thinking animation ───────────────────────────────────────────────────────

let thinkingEl = null;

function showThinking() {
  const panel = document.getElementById('convo-panel');
  thinkingEl = document.createElement('div');
  thinkingEl.className = 'entry aria';
  thinkingEl.id = 'thinking-indicator';
  thinkingEl.innerHTML = `
    <div class="entry-speaker">ARIA</div>
    <div class="entry-bubble"><div class="thinking-dots"><span></span><span></span><span></span></div></div>
  `;
  panel.appendChild(thinkingEl);
  panel.scrollTop = panel.scrollHeight;
}

function hideThinking() {
  if (thinkingEl) {
    thinkingEl.remove();
    thinkingEl = null;
  }
}

// ── Audio playback ───────────────────────────────────────────────────────────

function playAudioBase64(dataUri) {
  if (!dataUri || !ttsEnabled) return;
  const audio = new Audio(dataUri);
  audio.play().catch(e => console.warn('Audio playback blocked:', e));
}

// ── TTS toggle ───────────────────────────────────────────────────────────────

document.getElementById('tts-toggle').addEventListener('change', (e) => {
  ttsEnabled = e.target.checked;
});

// ── Chat input (text) ────────────────────────────────────────────────────────

document.getElementById('send-btn').addEventListener('click', handleSend);
document.getElementById('chat-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') handleSend();
});

function handleSend() {
  if (isRecording) {
    // Send the voice memo
    stopMicRecording(true);
  } else {
    sendMessage();
  }
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  const ts = Date.now() / 1000;
  addConvoEntry({ speaker: 'User', text, ts });
  showThinking();
  pendingQuery = true;

  try {
    const resp = await fetch('/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await resp.json();
    hideThinking();
    addConvoEntry({ speaker: 'ARIA', text: data.response, ts: Date.now() / 1000 });
    setMood(data.mood);
    playAudioBase64(data.audio_base64);
  } catch (e) {
    hideThinking();
    console.error('Query failed:', e);
  }
  pendingQuery = false;
}

// ── Mic recording (voice memo UI) ────────────────────────────────────────────

document.getElementById('mic-btn').addEventListener('click', toggleMicRecording);

function toggleMicRecording() {
  if (isRecording) {
    // Cancel recording
    stopMicRecording(false);
  } else {
    startMicRecording();
  }
}

async function startMicRecording() {
  // Pause ambient so the two streams don't overlap
  if (isAmbient) { wasAmbient = true; stopAmbient(); }
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    recSeconds = 0;

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';
    mediaRecorder = new MediaRecorder(micStream, { mimeType });

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.start();
    isRecording = true;

    // Setup audio analyser for oscilloscope
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(micStream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    // Switch UI to recording mode
    document.getElementById('chat-input').classList.add('hidden');
    document.getElementById('recording-ui').classList.add('active');
    document.getElementById('mic-btn').classList.add('recording');
    document.getElementById('send-btn').classList.add('send-recording');
    document.getElementById('send-btn').textContent = 'Send';
    document.getElementById('recording-timer').textContent = '0:00';
    handleState('listening');

    // Start timer
    recTimerInterval = setInterval(() => {
      recSeconds++;
      const m = Math.floor(recSeconds / 60);
      const s = String(recSeconds % 60).padStart(2, '0');
      document.getElementById('recording-timer').textContent = `${m}:${s}`;
    }, 1000);

    // Start oscilloscope
    drawRecordingWaveform();

  } catch (e) {
    console.error('Mic access denied:', e);
  }
}

function stopMicRecording(send) {
  // Stop timer
  clearInterval(recTimerInterval);

  // Stop oscilloscope
  if (recAnimFrame) {
    cancelAnimationFrame(recAnimFrame);
    recAnimFrame = null;
  }

  // Restore UI
  document.getElementById('chat-input').classList.remove('hidden');
  document.getElementById('recording-ui').classList.remove('active');
  document.getElementById('mic-btn').classList.remove('recording');
  document.getElementById('send-btn').classList.remove('send-recording');
  document.getElementById('send-btn').textContent = 'Send';

  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    if (send) {
      mediaRecorder.onstop = () => {
        const mimeType = mediaRecorder.mimeType;
        const blob = new Blob(audioChunks, { type: mimeType });
        sendVoiceQuery(blob);
        cleanupMicStream();
      };
    } else {
      mediaRecorder.onstop = () => {
        cleanupMicStream();
        handleState('idle');
        if (wasAmbient) { wasAmbient = false; startAmbient(); }
      };
    }
    mediaRecorder.stop();
  } else {
    cleanupMicStream();
    if (!send) {
      handleState('idle');
      if (wasAmbient) { wasAmbient = false; startAmbient(); }
    }
  }

  isRecording = false;
}

function cleanupMicStream() {
  if (micStream) {
    micStream.getTracks().forEach(t => t.stop());
    micStream = null;
  }
  if (audioContext) {
    audioContext.close().catch(() => {});
    audioContext = null;
    analyser = null;
  }
}

// ── Recording oscilloscope ───────────────────────────────────────────────────

function drawRecordingWaveform() {
  const canvas = document.getElementById('recording-canvas');
  const rCtx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;

  function draw() {
    if (!analyser) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteTimeDomainData(dataArray);

    rCtx.clearRect(0, 0, W, H);

    // Draw center line (dim)
    rCtx.beginPath();
    rCtx.strokeStyle = 'rgba(239, 68, 68, 0.15)';
    rCtx.lineWidth = 1;
    rCtx.moveTo(0, H / 2);
    rCtx.lineTo(W, H / 2);
    rCtx.stroke();

    // Draw waveform
    rCtx.beginPath();
    rCtx.strokeStyle = 'rgba(239, 68, 68, 0.8)';
    rCtx.lineWidth = 2;
    rCtx.shadowBlur = 6;
    rCtx.shadowColor = 'rgba(239, 68, 68, 0.5)';

    const sliceWidth = W / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * H) / 2;
      if (i === 0) rCtx.moveTo(x, y);
      else rCtx.lineTo(x, y);
      x += sliceWidth;
    }

    rCtx.lineTo(W, H / 2);
    rCtx.stroke();
    rCtx.shadowBlur = 0;

    recAnimFrame = requestAnimationFrame(draw);
  }

  draw();
}

// ── Send voice query ─────────────────────────────────────────────────────────

async function sendVoiceQuery(blob) {
  handleState('processing');
  showThinking();
  pendingQuery = true;
  const formData = new FormData();
  formData.append('audio', blob, 'recording.webm');

  try {
    const resp = await fetch('/voice-query', {
      method: 'POST',
      body: formData,
    });
    const data = await resp.json();
    hideThinking();

    if (data.text) {
      addConvoEntry({ speaker: 'User', text: data.text, ts: Date.now() / 1000 });
    }
    if (data.response) {
      addConvoEntry({ speaker: 'ARIA', text: data.response, ts: Date.now() / 1000 });
      setMood(data.mood);
      playAudioBase64(data.audio_base64);
    }
    if (!data.text) {
      console.log('No speech detected');
    }
  } catch (e) {
    hideThinking();
    console.error('Voice query failed:', e);
  }
  pendingQuery = false;
  handleState('idle');
  if (wasAmbient) { wasAmbient = false; startAmbient(); }
}

// ── Voice clone panel ────────────────────────────────────────────────────────

function toggleVoicePanel() {
  document.getElementById('voice-panel').classList.toggle('open');
}

// Record sample for cloning
document.getElementById('clone-record-btn').addEventListener('click', toggleCloneRecording);

async function toggleCloneRecording() {
  if (isCloneRecording) {
    stopCloneRecording();
  } else {
    await startCloneRecording();
  }
}

async function startCloneRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    cloneChunks = [];
    cloneSeconds = 0;
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';
    cloneRecorder = new MediaRecorder(stream, { mimeType });

    cloneRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) cloneChunks.push(e.data);
    };

    cloneRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      clearInterval(cloneTimerInterval);
      const blob = new Blob(cloneChunks, { type: mimeType });
      uploadCloneAudio(blob);
    };

    cloneRecorder.start();
    isCloneRecording = true;
    document.getElementById('clone-record-btn').classList.add('recording');
    document.getElementById('clone-record-btn').textContent = 'Stop Recording';
    document.getElementById('clone-status').textContent = 'Recording... (30s+ recommended)';
    document.getElementById('clone-status').className = '';

    cloneTimerInterval = setInterval(() => {
      cloneSeconds++;
      document.getElementById('clone-timer').textContent = `${Math.floor(cloneSeconds / 60)}:${String(cloneSeconds % 60).padStart(2, '0')}`;
    }, 1000);
  } catch (e) {
    console.error('Mic access denied:', e);
    setCloneStatus('Microphone access denied', 'error');
  }
}

function stopCloneRecording() {
  if (cloneRecorder && cloneRecorder.state !== 'inactive') {
    cloneRecorder.stop();
  }
  isCloneRecording = false;
  document.getElementById('clone-record-btn').classList.remove('recording');
  document.getElementById('clone-record-btn').textContent = 'Record Sample';
}

// File upload for cloning
document.getElementById('clone-upload-btn').addEventListener('click', () => {
  document.getElementById('clone-file').click();
});

document.getElementById('clone-file').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) uploadCloneAudio(file);
});

async function uploadCloneAudio(blobOrFile) {
  setCloneStatus('Cloning voice...', '');
  const formData = new FormData();
  const filename = blobOrFile.name || 'sample.webm';
  formData.append('audio', blobOrFile, filename);
  formData.append('name', 'ARIA');

  try {
    const resp = await fetch('/clone-voice', {
      method: 'POST',
      body: formData,
    });
    const data = await resp.json();
    if (data.success) {
      setCloneStatus('Voice cloned successfully!', 'success');
      document.getElementById('voice-id-display').textContent = `ID: ${data.voice_id}`;
    } else {
      setCloneStatus(data.error || 'Cloning failed', 'error');
    }
  } catch (e) {
    console.error('Clone failed:', e);
    setCloneStatus('Upload failed', 'error');
  }
}

function setCloneStatus(text, cls) {
  const el = document.getElementById('clone-status');
  el.textContent = text;
  el.className = cls || '';
}

// Check voice status on load
async function checkVoiceStatus() {
  try {
    const resp = await fetch('/voice-status');
    const data = await resp.json();
    if (data.has_voice) {
      document.getElementById('voice-id-display').textContent = `ID: ${data.voice_id}`;
      setCloneStatus('Voice active', 'success');
    }
  } catch (e) {
    // server may not be ready yet
  }
}

// ── Waveform animation ────────────────────────────────────────────────────────

const canvas = document.getElementById('wave');
const ctx = canvas.getContext('2d');
let phase = 0;

function drawWave() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const W = canvas.width;
  const H = canvas.height;
  const cy = H / 2;

  let amp, speed, color;
  if (currentState === 'idle') {
    amp = 4; speed = 0.02;
    color = 'rgba(139, 92, 246, 0.4)';
  } else if (currentState === 'listening') {
    amp = 16; speed = 0.06;
    color = 'rgba(167, 139, 250, 0.9)';
  } else if (currentState === 'processing') {
    amp = 8; speed = 0.1;
    color = 'rgba(99, 102, 241, 0.8)';
  } else {
    amp = 20; speed = 0.08;
    color = 'rgba(52, 211, 153, 0.9)';
  }

  phase += speed;

  ctx.beginPath();
  ctx.moveTo(0, cy);
  for (let x = 0; x <= W; x++) {
    const y = cy
      + Math.sin((x / W) * Math.PI * 6 + phase) * amp
      + Math.sin((x / W) * Math.PI * 10 + phase * 1.3) * (amp * 0.4);
    if (x === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.shadowBlur = 10;
  ctx.shadowColor = color;
  ctx.stroke();

  requestAnimationFrame(drawWave);
}

// ── Day/night theme ──────────────────────────────────────────────────────────

function applyTimeTheme() {
  const hour = new Date().getHours();
  document.body.classList.remove('daytime', 'evening');
  if (hour >= 7 && hour < 18) {
    document.body.classList.add('daytime');
  } else if (hour >= 18 && hour < 22) {
    document.body.classList.add('evening');
  }
  // else: default dark night theme
}

// ── Proactive greeting ───────────────────────────────────────────────────────

let hasGreeted = false;

function proactiveGreeting() {
  if (hasGreeted) return;
  hasGreeted = true;

  const hour = new Date().getHours();
  let greeting, mood;
  if (hour >= 5 && hour < 12) {
    greeting = "Good morning! Ready to take on the day?";
    mood = "warm";
  } else if (hour >= 12 && hour < 17) {
    greeting = "Hey! How's your afternoon going?";
    mood = "curious";
  } else if (hour >= 17 && hour < 22) {
    greeting = "Good evening. How was your day?";
    mood = "warm";
  } else {
    greeting = "Burning the midnight oil? I'm here if you need me.";
    mood = "thoughtful";
  }

  setTimeout(() => {
    addConvoEntry({ speaker: 'ARIA', text: greeting, ts: Date.now() / 1000 });
    setMood(mood);
  }, 800);
}

// ── Init ──────────────────────────────────────────────────────────────────────

applyTimeTheme();
connect();
drawWave();
checkVoiceStatus();
proactiveGreeting();
