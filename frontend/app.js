// ── ARIA Dashboard ────────────────────────────────────────────────────────────

const WS_URL = `ws://${location.hostname}:8000/ws/dashboard`;

let ws = null;
let currentState = 'idle';
let memoryCount = 0;

// ── WebSocket ─────────────────────────────────────────────────────────────────

function connect() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.log('Connected to ARIA backend');
  };

  ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    if (msg.event === 'history')            handleHistory(msg);
    else if (msg.event === 'transcript')    handleTranscript(msg);
    else if (msg.event === 'pendant_state') handleState(msg.state);
    else if (msg.event === 'tool_use')      handleToolUse(msg);
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
    memories.forEach(m => addMemoryItem(m));
  }
}

function handleTranscript({ speaker, text, ts }) {
  addTranscriptEntry({ speaker, text, ts });
  if (speaker === 'User' || speaker === 'ARIA') {
    addConvoEntry({ speaker, text, ts });
  }
}

function handleToolUse({ tool, args, result, ts }) {
  const panel = document.getElementById('activity-panel');
  const div = document.createElement('div');
  div.className = 'tool-item';
  div.innerHTML = `
    <div class="tool-name">${escHtml(tool)}</div>
    <div class="tool-args">${escHtml(JSON.stringify(args))}</div>
    <div class="tool-result">${escHtml(result.substring(0, 150))}</div>
    <div class="entry-time">${fmtTime(ts)}</div>
  `;
  panel.appendChild(div);
  panel.scrollTop = panel.scrollHeight;
}

function handleState(state) {
  currentState = state;
  const badge = document.getElementById('status-badge');
  badge.textContent = state.toUpperCase();
  badge.className = state;
  document.body.className = state === 'speaking' ? 'speaking' : '';
}

// ── DOM helpers ───────────────────────────────────────────────────────────────

function fmtTime(ts) {
  return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function makeEntry({ speaker, text, ts }) {
  const cls = speaker === 'ARIA' ? 'aria' : speaker === 'Ambient' ? 'ambient' : 'user';
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

function addMemoryItem(m) {
  const panel = document.getElementById('activity-panel');
  const div = document.createElement('div');
  div.className = 'memory-item';
  div.innerHTML = `
    <div class="memory-key">${escHtml(m.key || m.category || '')}</div>
    <div class="memory-val">${escHtml(m.value || m.content || '')}</div>
  `;
  panel.appendChild(div);
}

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Chat input ────────────────────────────────────────────────────────────────

document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  const ts = Date.now() / 1000;
  addConvoEntry({ speaker: 'User', text, ts });

  try {
    await fetch('/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
  } catch (e) {
    console.error('Query failed:', e);
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

// ── Microphone (Web Speech API) ───────────────────────────────────────────────

const micBtn = document.getElementById('mic-btn');
let recognition = null;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onresult = (e) => {
    const text = e.results[0][0].transcript;
    document.getElementById('chat-input').value = text;
    sendMessage();
  };

  recognition.onend = () => {
    micBtn.classList.remove('recording');
    micBtn.textContent = '🎤';
  };

  recognition.onerror = (e) => {
    console.error('Speech error:', e.error);
    micBtn.classList.remove('recording');
    micBtn.textContent = '🎤';
  };

  micBtn.addEventListener('click', () => {
    if (micBtn.classList.contains('recording')) {
      recognition.stop();
    } else {
      micBtn.classList.add('recording');
      micBtn.textContent = '⏹';
      recognition.start();
    }
  });
} else {
  micBtn.title = 'Speech not supported in this browser — use Chrome';
  micBtn.style.opacity = '0.4';
}

// ── Browser Audio (talk to ARIA via laptop mic/speaker) ──────────────────────

const BROWSER_AUDIO_WS = `ws://${location.hostname}:8000/ws/browser-audio`;
let baWs = null;
let baContext = null;
let baStream = null;
let baProcessor = null;
let baPlayCtx = null;
let baNextPlayTime = 0;
let baTalking = false;

const talkBtn = document.getElementById('talk-btn');

talkBtn.addEventListener('click', () => {
  if (baTalking) {
    stopTalking();
  } else {
    startTalking();
  }
});

async function startTalking() {
  baTalking = true;
  talkBtn.classList.add('active');
  talkBtn.textContent = 'STOP';

  baPlayCtx = new AudioContext({ sampleRate: 24000 });
  baNextPlayTime = 0;

  baWs = new WebSocket(BROWSER_AUDIO_WS);
  baWs.binaryType = 'arraybuffer';

  baWs.onopen = async () => {
    console.log('Browser audio WS connected');
    try {
      baStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      console.error('Mic access denied:', e);
      stopTalking();
      return;
    }

    baContext = new AudioContext();
    const source = baContext.createMediaStreamSource(baStream);
    baProcessor = baContext.createScriptProcessor(4096, 1, 1);
    const srcRate = baContext.sampleRate;
    const tgtRate = 24000;

    baProcessor.onaudioprocess = (e) => {
      if (!baWs || baWs.readyState !== WebSocket.OPEN) return;
      const input = e.inputBuffer.getChannelData(0);
      const ratio = tgtRate / srcRate;
      const outLen = Math.floor(input.length * ratio);
      const pcm = new Int16Array(outLen);
      for (let i = 0; i < outLen; i++) {
        const srcIdx = i / ratio;
        const idx = Math.floor(srcIdx);
        const frac = srcIdx - idx;
        const s = idx + 1 < input.length
          ? input[idx] * (1 - frac) + input[idx + 1] * frac
          : input[idx];
        pcm[i] = Math.max(-32768, Math.min(32767, Math.floor(s * 32767)));
      }
      baWs.send(pcm.buffer);
    };

    source.connect(baProcessor);
    baProcessor.connect(baContext.destination);
    baWs.send(JSON.stringify({ event: 'start' }));
  };

  baWs.onmessage = (evt) => {
    if (evt.data instanceof ArrayBuffer) {
      playAudioChunk(evt.data);
    }
  };

  baWs.onclose = () => {
    if (baTalking) stopTalking();
  };
}

function stopTalking() {
  baTalking = false;
  talkBtn.classList.remove('active');
  talkBtn.textContent = 'TALK TO ARIA';

  if (baWs && baWs.readyState === WebSocket.OPEN) {
    baWs.send(JSON.stringify({ event: 'stop' }));
    setTimeout(() => baWs.close(), 500);
  }

  if (baProcessor) { baProcessor.disconnect(); baProcessor = null; }
  if (baContext) { baContext.close(); baContext = null; }
  if (baStream) { baStream.getTracks().forEach(t => t.stop()); baStream = null; }
  if (baPlayCtx) { baPlayCtx.close(); baPlayCtx = null; }
}

function playAudioChunk(buffer) {
  if (!baPlayCtx || baPlayCtx.state === 'closed') return;
  const int16 = new Int16Array(buffer);
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;

  const audioBuf = baPlayCtx.createBuffer(1, float32.length, 24000);
  audioBuf.getChannelData(0).set(float32);

  const src = baPlayCtx.createBufferSource();
  src.buffer = audioBuf;
  src.connect(baPlayCtx.destination);

  const startTime = Math.max(baPlayCtx.currentTime, baNextPlayTime);
  src.start(startTime);
  baNextPlayTime = startTime + audioBuf.duration;
}

// ── Init ──────────────────────────────────────────────────────────────────────

connect();
drawWave();
