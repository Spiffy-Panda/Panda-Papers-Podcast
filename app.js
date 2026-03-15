// === State ===
const state = {
  sentences: [],
  currentIndex: 0,
  isPlaying: false,
  utterance: null,
  rate: 1.0,
  selectedVoice: null,
};

// === DOM refs ===
const readerContent = document.getElementById('readerContent');
const statusBadge = document.getElementById('statusBadge');
const btnPlayPause = document.getElementById('btnPlayPause');
const btnPrev = document.getElementById('btnPrev');
const btnNext = document.getElementById('btnNext');
const speedRange = document.getElementById('speedRange');
const speedValue = document.getElementById('speedValue');
const voiceSelect = document.getElementById('voiceSelect');
const progressFill = document.getElementById('progressFill');
const btnLoadText = document.getElementById('btnLoadText');
const btnSendPrompt = document.getElementById('btnSendPrompt');
const btnFetchUrl = document.getElementById('btnFetchUrl');
const textInput = document.getElementById('textInput');
const promptInput = document.getElementById('promptInput');
const urlInput = document.getElementById('urlInput');

// === Tabs ===
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
  });
});

// === Voice loading ===
function loadVoices() {
  const voices = speechSynthesis.getVoices();
  voiceSelect.innerHTML = '';
  voices.forEach((voice, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = `${voice.name} (${voice.lang})`;
    // Default to a Zira-like or female English voice
    if (voice.name.includes('Zira') || voice.name.includes('zira')) {
      opt.selected = true;
      state.selectedVoice = voice;
    }
    voiceSelect.appendChild(opt);
  });
  if (!state.selectedVoice && voices.length > 0) {
    state.selectedVoice = voices[0];
  }
}

speechSynthesis.onvoiceschanged = loadVoices;
loadVoices();

voiceSelect.addEventListener('change', () => {
  const voices = speechSynthesis.getVoices();
  state.selectedVoice = voices[voiceSelect.value];
});

// === Speed control ===
speedRange.addEventListener('input', () => {
  state.rate = parseFloat(speedRange.value);
  speedValue.textContent = `${state.rate.toFixed(1)}x`;
});

// === Text loading ===
function splitSentences(text) {
  // Split on sentence-ending punctuation followed by space or end
  return text
    .split(/(?<=[.!?~])\s+/)
    .map(s => s.trim())
    .filter(s => s.length > 0);
}

function loadContent(text) {
  speechSynthesis.cancel();
  state.isPlaying = false;
  state.currentIndex = 0;
  state.sentences = splitSentences(text);

  renderSentences();
  updatePlayPauseUI();
  updateProgress();
  setStatus('Ready');
}

function renderSentences() {
  if (state.sentences.length === 0) {
    readerContent.innerHTML = '<p class="placeholder-text">Paste text, enter a prompt, or load a source to get started!</p>';
    return;
  }

  readerContent.innerHTML = state.sentences
    .map((s, i) => {
      let cls = 'sentence';
      if (i < state.currentIndex) cls += ' read';
      if (i === state.currentIndex) cls += ' active';
      return `<span class="${cls}" data-index="${i}">${s} </span>`;
    })
    .join('');

  // Scroll active sentence into view
  const active = readerContent.querySelector('.sentence.active');
  if (active) {
    active.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

// === Playback ===
function speakCurrent() {
  if (state.currentIndex >= state.sentences.length) {
    stop();
    setStatus('Done');
    return;
  }

  const text = state.sentences[state.currentIndex];
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = state.rate;
  if (state.selectedVoice) utt.voice = state.selectedVoice;

  utt.onend = () => {
    if (!state.isPlaying) return;
    state.currentIndex++;
    renderSentences();
    updateProgress();
    speakCurrent();
  };

  utt.onerror = (e) => {
    // 'interrupted' and 'canceled' are expected when pausing/stopping
    if (e.error !== 'interrupted' && e.error !== 'canceled') {
      console.error('Speech error:', e.error);
    }
  };

  state.utterance = utt;
  renderSentences();
  setStatus('Playing');
  speechSynthesis.speak(utt);
}

function play() {
  if (state.sentences.length === 0) return;
  state.isPlaying = true;
  updatePlayPauseUI();
  speakCurrent();
}

function pause() {
  state.isPlaying = false;
  speechSynthesis.cancel();
  updatePlayPauseUI();
  setStatus('Paused');
}

function stop() {
  state.isPlaying = false;
  speechSynthesis.cancel();
  updatePlayPauseUI();
}

function skipNext() {
  const wasPlaying = state.isPlaying;
  speechSynthesis.cancel();
  state.isPlaying = false;

  if (state.currentIndex < state.sentences.length - 1) {
    state.currentIndex++;
    renderSentences();
    updateProgress();
  }

  if (wasPlaying) play();
}

function skipPrev() {
  const wasPlaying = state.isPlaying;
  speechSynthesis.cancel();
  state.isPlaying = false;

  if (state.currentIndex > 0) {
    state.currentIndex--;
    renderSentences();
    updateProgress();
  }

  if (wasPlaying) play();
}

// === UI helpers ===
function updatePlayPauseUI() {
  const iconPlay = btnPlayPause.querySelector('.icon-play');
  const iconPause = btnPlayPause.querySelector('.icon-pause');
  if (state.isPlaying) {
    iconPlay.classList.add('hidden');
    iconPause.classList.remove('hidden');
  } else {
    iconPlay.classList.remove('hidden');
    iconPause.classList.add('hidden');
  }
}

function setStatus(text) {
  statusBadge.textContent = text;
  statusBadge.className = 'status-badge';
  if (text === 'Playing') statusBadge.classList.add('playing');
  else if (text === 'Paused') statusBadge.classList.add('paused');
}

function updateProgress() {
  if (state.sentences.length === 0) {
    progressFill.style.width = '0%';
    return;
  }
  const pct = (state.currentIndex / state.sentences.length) * 100;
  progressFill.style.width = `${pct}%`;
}

// === Event listeners ===
btnPlayPause.addEventListener('click', () => {
  if (state.isPlaying) pause();
  else play();
});

btnNext.addEventListener('click', skipNext);
btnPrev.addEventListener('click', skipPrev);

btnLoadText.addEventListener('click', () => {
  const text = textInput.value.trim();
  if (text) loadContent(text);
});

btnSendPrompt.addEventListener('click', () => {
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  // Placeholder: replace with actual AI API call
  const placeholder = `[AI Prompt received: "${prompt}"]\n\nThis is where the AI-generated response will appear. Connect your preferred AI backend (OpenAI, Anthropic, local model, etc.) by editing the btnSendPrompt handler in app.js.`;
  loadContent(placeholder);
});

btnFetchUrl.addEventListener('click', async () => {
  const url = urlInput.value.trim();
  if (!url) return;

  setStatus('Fetching...');
  try {
    // Use a CORS proxy or your own backend in production
    const resp = await fetch(url);
    const html = await resp.text();

    // Basic text extraction: strip tags
    const doc = new DOMParser().parseFromString(html, 'text/html');
    // Try article content first, fall back to body
    const article = doc.querySelector('article') || doc.querySelector('main') || doc.body;
    const text = article.innerText || article.textContent;
    loadContent(text.trim());
  } catch (err) {
    loadContent(`Failed to fetch URL: ${err.message}\n\nTip: Due to CORS, fetching may not work for all sites directly from the browser. Consider adding a proxy backend.`);
  }
});

// === Keyboard shortcuts ===
document.addEventListener('keydown', (e) => {
  // Don't capture when typing in inputs
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;

  if (e.code === 'Space') {
    e.preventDefault();
    if (state.isPlaying) pause();
    else play();
  } else if (e.code === 'ArrowRight') {
    e.preventDefault();
    skipNext();
  } else if (e.code === 'ArrowLeft') {
    e.preventDefault();
    skipPrev();
  }
});
