---
name: boycott-filter
description: Manage your personal boycott list. Add brands to avoid, track reasons, sync with Chrome extension. Use when the user complains about a brand, says "never buying from X again", wants to block a company, or mentions the boycott filter.
version: 1.0.0
author: Bubble Invest
license: MIT
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
---

# Boycott Filter

Personal boycott list managed conversationally through Claude Code, synced to a Chrome extension that warns you when you visit boycotted brands.

## When to use

- User says "never buying from X again", "I hate X", "boycott X", "block X"
- User complains about a brand, company, or product they want to avoid
- User asks to see, add, remove, or update their boycott list
- User asks about the Chrome extension or boycott filter status

## How it works

1. User tells you about a brand they want to avoid (casually or explicitly)
2. You extract: **company name**, **reason** (from their complaint), and **aliases** (known sub-brands)
3. You add it to the boycott list via the local sync server
4. Chrome extension picks it up within 30 seconds and warns on matching pages

## Server

The boycott filter runs a local HTTP server on port 7847.

### Start the server

```bash
node ~/.claude/plugins/cache/boycott-filter-marketplace/boycott-filter/1.0.0/scripts/server.js &
```

### API

**Base URL:** `http://127.0.0.1:7847`

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| GET | `/list` | — | Get the full boycott list |
| POST | `/add` | `{"name":"X","reason":"...","aliases":["Y","Z"]}` | Add a company |
| DELETE | `/remove` | `{"name":"X"}` | Remove a company |
| GET | `/health` | — | Check server status |

### Add a company

```bash
curl -s -X POST http://127.0.0.1:7847/add \
  -H 'Content-Type: application/json' \
  -d '{"name":"Temu","reason":"Cheap garbage, ads everywhere","aliases":["temu.com"]}'
```

### Remove a company

```bash
curl -s -X DELETE http://127.0.0.1:7847/remove \
  -H 'Content-Type: application/json' \
  -d '{"name":"Temu"}'
```

### List all boycotted companies

```bash
curl -s http://127.0.0.1:7847/list
```

## Chrome Extension

The extension must be loaded manually (one-time setup):

1. Open `chrome://extensions`
2. Enable **Developer mode** (toggle top right)
3. Click **Load unpacked**
4. Select the `extension/` folder from this plugin directory

The extension:
- Polls the server every 30 seconds for list updates
- Scans every page for boycotted company names and aliases
- Shows a red warning banner at the top with the company name and **your reason**
- Badge on the extension icon shows match count
- Works offline (falls back to cached list in chrome.storage)
- Popup UI for quick add/remove

## Conversational patterns

When the user says something like:
- "Ugh, another Shein ad. Never buying from them." → Add Shein with reason "Sick of their ads"
- "Boycott Nestlé, their water practices are criminal" → Add Nestlé with reason "Criminal water practices", aliases: ["Nestle", "Nespresso", "KitKat", "Purina"]
- "Remove Temu from my boycott list" → Remove Temu
- "What's on my boycott list?" → GET /list and display

**Always capture the reason** — it's the key feature. The user's own words remind them why they decided to boycott when they encounter the brand later.

**Suggest aliases** when you know them — parent companies own many brands. Ask the user if they want to include subsidiaries.

## Data

The boycott list is stored at:
```
~/.claude/plugins/cache/boycott-filter-marketplace/boycott-filter/1.0.0/boycott-list.json
```

Format:
```json
{
  "companies": [
    {
      "name": "Temu",
      "reason": "Cheap garbage, ads everywhere",
      "aliases": ["temu.com"],
      "added_at": "2026-04-12T15:00:00Z"
    }
  ],
  "updated_at": "2026-04-12T15:00:00Z"
}
```

## Setup

On first use, start the server:

```bash
bash ~/.claude/plugins/cache/boycott-filter-marketplace/boycott-filter/1.0.0/scripts/setup.sh
```

Then load the Chrome extension manually (see above).
