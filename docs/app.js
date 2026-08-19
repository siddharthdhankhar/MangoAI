/**
 * app.js — MangoAI Frontend Logic
 * Connects to the FastAPI backend.
 *
 * Set window.MANGO_API_URL before this script loads to point at your
 * Railway deployment. Falls back to localhost for local development.
 */

// ── CONFIG ────────────────────────────────────────────────────────────────
const API_BASE = 'https://mangoai-fz1g.onrender.com';

// ── DOM REFS ──────────────────────────────────────────────────────────────
const chatWindow     = document.getElementById('chat-window');
const chatInput      = document.getElementById('chat-input');
const sendBtn        = document.getElementById('send-btn');
const resetBtn       = document.getElementById('reset-btn');
const statusDot      = document.getElementById('status-dot');
const statusText     = document.getElementById('status-text');
const capGrid        = document.getElementById('capabilities-grid');
const quickChips     = document.querySelectorAll('.chip');
const startChattingBtn = document.getElementById('start-chatting-btn');

// ── STATE ─────────────────────────────────────────────────────────────────
let isLoading = false;

// ── INIT ──────────────────────────────────────────────────────────────────
(async function init() {
  await checkApiStatus();
  await loadCapabilities();
  autoResizeTextarea();
})();

// ── API STATUS CHECK ──────────────────────────────────────────────────────
async function checkApiStatus() {
  try {
    const res = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      setStatus('online', 'Connected');
    } else {
      setStatus('offline', 'API Error');
    }
  } catch {
    setStatus('offline', 'Server offline');
    showOfflineWarning();
  }
}

function setStatus(state, text) {
  statusDot.className  = `status-dot ${state}`;
  statusText.textContent = text;
}

function showOfflineWarning() {
  appendMessage(
    'ai',
    `⚠️ <strong>Can't reach the API server.</strong><br/>
     Please run: <code style="background:rgba(245,158,11,0.15);color:#FCD34D;padding:2px 8px;border-radius:4px;font-size:13px;">uvicorn api:app --reload</code><br/>
     …in your project folder, then refresh this page.`,
    null,
    'error'
  );
}

// ── LOAD CAPABILITIES ─────────────────────────────────────────────────────
async function loadCapabilities() {
  try {
    const res  = await fetch(`${API_BASE}/capabilities`);
    const caps = await res.json();
    renderCapabilities(caps);
  } catch {
    capGrid.innerHTML = '<p style="color:var(--col-text-muted);text-align:center;grid-column:1/-1;padding:32px">Could not load capabilities — start the API server first.</p>';
  }
}

function renderCapabilities(caps) {
  capGrid.innerHTML = '';
  caps.forEach((cap, i) => {
    const card = document.createElement('div');
    card.className = 'cap-card';
    card.style.setProperty('--i', i);
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
    card.title = `Try: "${cap.example}"`;
    card.innerHTML = `
      <span class="cap-icon">${cap.icon}</span>
      <div class="cap-name">${cap.name}()</div>
      <div class="cap-desc">${cap.description}</div>
      <div class="cap-example">"${cap.example}"</div>
    `;
    // Clicking a capability card sends its example prompt
    card.addEventListener('click', () => {
      chatInput.value = cap.example;
      autoResizeTextarea();
      document.getElementById('chat-section').scrollIntoView({ behavior: 'smooth' });
      setTimeout(() => sendMessage(), 500);
    });
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') card.click();
    });
    capGrid.appendChild(card);
  });
}

// ── MESSAGING ─────────────────────────────────────────────────────────────
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || isLoading) return;

  isLoading = true;
  chatInput.value = '';
  autoResizeTextarea();
  sendBtn.disabled = true;

  // Append user bubble
  appendMessage('user', escapeHtml(text), null);

  // Show typing indicator
  const typingEl = appendTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text }),
    });

    typingEl.remove();

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
      appendMessage('ai', `Error: ${err.detail || res.statusText}`, null, 'error');
    } else {
      const data = await res.json();
      appendMessage('ai', formatResponse(data.response), data.tool_used, null, data.timestamp);
    }
  } catch (err) {
    typingEl.remove();
    appendMessage('ai', '⚠️ Could not reach the server. Is the API running?', null, 'error');
    setStatus('offline', 'Disconnected');
  } finally {
    isLoading = false;
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

/**
 * Appends a message bubble to the chat window.
 * @param {'user'|'ai'} role
 * @param {string} html - Already-safe HTML content
 * @param {string|null} toolUsed - function name if a tool was called
 * @param {string|null} variant - 'error' for error styling
 * @param {string|null} time - timestamp string
 */
function appendMessage(role, html, toolUsed, variant = null, time = null) {
  const wrap = document.createElement('div');
  wrap.className = `message message-${role}${variant ? ' message-' + variant : ''}`;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = role === 'user' ? '👤' : '🥭';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerHTML = html;

  // Meta row (time + tool badge)
  const meta = document.createElement('div');
  meta.className = 'message-meta';

  const timeEl = document.createElement('span');
  timeEl.className = 'message-time';
  timeEl.textContent = time || formatTime();
  meta.appendChild(timeEl);

  if (toolUsed) {
    const badge = document.createElement('span');
    badge.className = 'tool-badge';
    badge.textContent = `⚙ ${toolUsed}()`;
    badge.title = `Gemini called: ${toolUsed}`;
    meta.appendChild(badge);
  }

  bubble.appendChild(meta);
  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  chatWindow.appendChild(wrap);
  scrollToBottom();

  return wrap;
}

function appendTypingIndicator() {
  const wrap = document.createElement('div');
  wrap.className = 'typing-indicator';

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = '🥭';

  const dots = document.createElement('div');
  dots.className = 'typing-dots';
  dots.innerHTML = `
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  `;

  wrap.appendChild(avatar);
  wrap.appendChild(dots);
  chatWindow.appendChild(wrap);
  scrollToBottom();
  return wrap;
}

// ── RESET CHAT ────────────────────────────────────────────────────────────
resetBtn.addEventListener('click', async () => {
  try {
    await fetch(`${API_BASE}/reset`, { method: 'POST' });
  } catch { /* ignore */ }

  chatWindow.innerHTML = '';
  // Re-add welcome message
  appendMessage(
    'ai',
    `Hey there! I'm <strong>Mango</strong> 👋<br/>Fresh conversation started. What can I help you with?`,
    null
  );
});

// ── EVENT LISTENERS ───────────────────────────────────────────────────────
sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

chatInput.addEventListener('input', autoResizeTextarea);

quickChips.forEach((chip) => {
  chip.addEventListener('click', () => {
    chatInput.value = chip.dataset.prompt;
    autoResizeTextarea();
    document.getElementById('chat-section').scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => sendMessage(), 300);
  });
});

startChattingBtn.addEventListener('click', (e) => {
  setTimeout(() => chatInput.focus(), 700);
});

// ── UTILITIES ─────────────────────────────────────────────────────────────
function autoResizeTextarea() {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
}

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function formatTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Light formatting for AI responses:
 * - Converts **bold** → <strong>
 * - Converts newlines → <br>
 */
function formatResponse(text) {
  if (!text) return '(no response)';
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}
