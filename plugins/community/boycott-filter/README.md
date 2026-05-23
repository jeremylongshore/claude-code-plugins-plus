# Boycott Filter — Your AI Agent Remembers Why You Hate Them

**Tell your Claude agent which brands to avoid. Chrome extension warns you on any page from those brands — with your own reasons displayed.**

The problem: you decide to boycott a brand. Two weeks later, you've forgotten why, and you click "buy". This plugin fixes that. You complain to your agent once, the extension reminds you forever.

---

## How it works

1. Tell Claude conversationally: *"Never buying from Temu again, cheap garbage everywhere."*
2. Claude extracts the brand + your reason, adds it to your local boycott list.
3. Chrome extension reads the list, scans every page you visit.
4. On match: red warning banner at the top of the page, with the brand name and **your own words** as the reason.

All local. No cloud. No tracking. Your list never leaves your machine.

---

## Features

| Feature | Description |
|---------|-------------|
| **Conversational management** | Complain naturally, agent handles the list |
| **Reason tracking** | Your own words shown back to you as a reminder |
| **Brand aliases** | Boycott a parent company, catch all subsidiaries (Nestlé → Nespresso, KitKat, Purina, etc.) |
| **Red warning banner** | Slides in at top of matching pages, hard to miss |
| **Extension icon badge** | Match count visible at a glance |
| **Offline capable** | Extension caches the list, works without the server |
| **Popup UI** | Quick manual add/remove from the extension icon |
| **100% local** | Nothing leaves your Mac |

---

## Installation

```bash
/plugin install boycott-filter@claude-code-plugins-plus
```

### First-run setup

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh
```

This starts the local sync server on port 7847 and creates an empty boycott list.

### Chrome extension (one-time manual load)

Browser extensions can't be auto-installed from a Claude plugin. One-time manual load:

1. Open `chrome://extensions`
2. Enable **Developer mode** (toggle top right)
3. Click **Load unpacked**
4. Select the `extension/` folder inside this plugin directory

The plugin path is typically:

```
~/.claude/plugins/cache/claude-code-plugins-plus/boycott-filter/1.0.0/extension/
```

---

## Requirements

- **Node.js 18+** (for the sync server)
- **Chrome browser** (or Chromium / Brave / Edge — any Manifest V3 browser)
- That's it. No API keys, no accounts, no cloud.

---

## Usage

### Conversational examples

Say things like:

- *"Boycott Nestlé, their water practices are criminal."*
- *"I'm done with Shein — fast fashion, can't support it."*
- *"Add all Nestlé brands — Nespresso, KitKat, Purina, Perrier."*
- *"What's on my boycott list?"*
- *"Remove Amazon from the list."*

The agent calls the local API at `http://127.0.0.1:7847` to read/write the list.

### Manual via curl

```bash
# Add
curl -X POST http://127.0.0.1:7847/add \
  -H 'Content-Type: application/json' \
  -d '{"name":"Temu","reason":"Cheap garbage","aliases":["temu.com"]}'

# List
curl http://127.0.0.1:7847/list

# Remove
curl -X DELETE http://127.0.0.1:7847/remove \
  -H 'Content-Type: application/json' \
  -d '{"name":"Temu"}'
```

### Manual via extension popup

Click the extension icon → add/remove brands directly. Useful when the server isn't running (popup falls back to `chrome.storage`).

---

## How the warning looks

When you land on a page where a boycotted brand's name, domain, or alias appears, a red banner slides in at the top:

```
⛔ BOYCOTT ALERT — Temu
"Cheap garbage, ads everywhere"                               [X dismiss]
```

The reason is YOUR text. In your voice. That's the whole point.

The extension also sets a badge on its icon with the count of matches on the current page.

---

## Architecture

```
┌────────────────┐        ┌────────────────────┐        ┌─────────────────┐
│ Claude Code    │◄──────►│ Local sync server  │◄──────►│ Chrome extension│
│ (SKILL.md)     │  HTTP  │ (Node.js, :7847)   │  HTTP  │ (polls /list)   │
└────────────────┘        └────────────────────┘        └─────────────────┘
                                     │
                                     ▼
                          boycott-list.json
                          (local file, never leaves)
```

- **Server** (`scripts/server.js`): tiny Node HTTP server on port 7847. Stores the list as JSON. CORS-enabled so the Chrome extension can read it.
- **Skill** (`skills/boycott-filter/SKILL.md`): tells Claude how to add/remove brands when you mention them.
- **Extension** (`extension/`): content script scans every page, shows the banner. Background service worker syncs the list every 30s.

---

## API reference

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| GET | `/list` | — | Full boycott list |
| POST | `/add` | `{"name","reason","aliases":[]}` | Add a brand |
| DELETE | `/remove` | `{"name"}` | Remove a brand |
| GET | `/health` | — | Server status |

---

## Privacy

Everything runs locally:

- The list lives in `boycott-list.json` inside the plugin directory
- The sync server only listens on `127.0.0.1` — not reachable from other machines
- The Chrome extension never calls any external server
- No analytics, no telemetry, no cloud

---

## Demo

See a 28-second video demo at:

- https://github.com/vdk888/boycott-filter/blob/main/demo.mp4
- https://bubble-sentinel.netlify.app/boycott-filter.html (landing page)

---

## License

MIT — Bubble Invest 2026
