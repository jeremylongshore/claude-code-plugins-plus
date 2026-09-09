/**
 * Boycott Filter — Popup UI
 */

const SERVER = 'http://127.0.0.1:7847';

const listEl = document.getElementById('list');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const countEl = document.getElementById('count');
const addInput = document.getElementById('add-input');
const addBtn = document.getElementById('add-btn');

let serverOnline = false;

async function checkServer() {
  try {
    const res = await fetch(`${SERVER}/health`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) {
      serverOnline = true;
      statusDot.className = 'dot connected';
      statusText.textContent = 'Agent connected';
      return true;
    }
  } catch {}
  serverOnline = false;
  statusDot.className = 'dot disconnected';
  statusText.textContent = 'Agent offline';
  return false;
}

async function loadList() {
  const stored = await chrome.storage.local.get('boycottList');
  const companies = stored?.boycottList?.companies || [];
  renderList(companies);
  countEl.textContent = `${companies.length} compan${companies.length === 1 ? 'y' : 'ies'}`;
}

function renderList(companies) {
  if (companies.length === 0) {
    listEl.innerHTML = `
      <div class="empty">
        <div class="emoji">✨</div>
        All clear. No companies boycotted yet.<br>
        Tell your Claude agent or add one below.
      </div>
    `;
    return;
  }

  listEl.innerHTML = companies.map(c => `
    <div class="company" data-name="${c.name}">
      <div class="company-info">
        <h3>${c.name}</h3>
        ${c.reason ? `<div class="reason">${c.reason}</div>` : ''}
        ${c.aliases?.length ? `<div class="aliases">Also: ${c.aliases.join(', ')}</div>` : ''}
      </div>
      <button class="remove-btn" data-name="${c.name}">✕</button>
    </div>
  `).join('');

  // Attach remove handlers
  for (const btn of listEl.querySelectorAll('.remove-btn')) {
    btn.addEventListener('click', () => removeCompany(btn.dataset.name));
  }
}

async function addCompany(name) {
  if (!name.trim()) return;

  if (serverOnline) {
    try {
      const res = await fetch(`${SERVER}/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim() })
      });
      if (res.ok) {
        // Trigger a sync from background
        chrome.runtime.sendMessage({ type: 'REQUEST_SYNC' });
        addInput.value = '';
        setTimeout(loadList, 500);
        return;
      }
    } catch {}
  }

  // Fallback: add directly to chrome.storage
  const stored = await chrome.storage.local.get('boycottList');
  const list = stored?.boycottList || { companies: [] };
  list.companies.push({
    name: name.trim(),
    reason: null,
    aliases: [],
    added_at: new Date().toISOString()
  });
  list.updated_at = new Date().toISOString();
  await chrome.storage.local.set({ boycottList: list });
  addInput.value = '';
  loadList();
}

async function removeCompany(name) {
  if (serverOnline) {
    try {
      const res = await fetch(`${SERVER}/remove`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });
      if (res.ok) {
        chrome.runtime.sendMessage({ type: 'REQUEST_SYNC' });
        setTimeout(loadList, 500);
        return;
      }
    } catch {}
  }

  // Fallback: remove from chrome.storage directly
  const stored = await chrome.storage.local.get('boycottList');
  const list = stored?.boycottList || { companies: [] };
  list.companies = list.companies.filter(c => c.name.toLowerCase() !== name.toLowerCase());
  list.updated_at = new Date().toISOString();
  await chrome.storage.local.set({ boycottList: list });
  loadList();
}

// Event handlers
addBtn.addEventListener('click', () => addCompany(addInput.value));
addInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') addCompany(addInput.value);
});

// Init
checkServer();
loadList();
