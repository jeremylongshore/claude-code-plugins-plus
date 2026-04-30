---
name: boycott-filter
description: "Personal boycott list \u2014 users can conversationally tell the agent\
  \ which brands they\nwant to avoid, and why. A local sync server exposes the list\
  \ at http://127.0.0.1:7847,\nand a bundled Chrome extension warns the user when\
  \ they land on pages from boycotted\nbrands. Use when the user says things like\
  \ \"I'm done with X\", \"boycott Y\", \"never\nbuying from Z again\", \"remove X\
  \ from my boycott list\", or asks to see their list.\nTrigger phrases: \"boycott\"\
  , \"never buying from\", \"sick of\", \"add to boycott\",\n\"show my boycott list\"\
  , \"remove from boycott\".\n"
allowed-tools: Bash(curl:*)
version: 1.0.0
author: Bubble Invest <contact@bubbleinvest.com>
license: MIT
tags:
- boycott
- consumer
- shopping
- brands
- chrome-extension
- productivity
- ethical-consumption
user-invocable: true
compatibility: Designed for Claude Code
---
# Boycott Filter

Manage a personal boycott list conversationally. Users complain about brands, the agent adds them to a local list with their reason, and a Chrome extension warns them on any page from those brands — displaying their own words back to them.

## Overview

This skill is the conversational layer of a 3-part system:

1. **This skill** (Claude Code) — understands user intent, calls the local API
2. **Local sync server** (`scripts/server.js`, port 7847) — stores the list, serves it to the extension
3. **Chrome extension** (`extension/`) — scans pages, shows the warning banner

The user's value: they complain ONCE, they're reminded FOREVER — in their own voice, with their own reason. No more accidental clicks on brands they'd decided to stop supporting.

## Prerequisites

- Node.js 18+ installed
- Chrome (or any Manifest V3 browser) with the bundled extension loaded manually (see README)
- The local sync server must be running on port 7847

Check with:
```bash
curl -s http://127.0.0.1:7847/health
```

If not running, ask the user to run setup once in a terminal (the skill itself only has `curl` permission, by design — see README for security rationale):

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh
```

Tell the user: "The boycott server isn't running. Open a terminal and run: `bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh` — that starts the local server and shows you how to load the Chrome extension. Then ask me again."

## Instructions

### When the user wants to ADD a brand

Detect phrases like:
- "I'm done with X"
- "Never buying from X again"
- "Boycott X"
- "Add X to my boycott list"
- "Sick of X"

Extract:
- **Brand name** (the thing they want to avoid)
- **Reason** (their own words — critical, this is what will be shown back to them)
- **Aliases** (optional — if you know subsidiaries, offer them: Nestlé → Nespresso, KitKat, Purina, etc.)

Then call:

```bash
curl -s -X POST http://127.0.0.1:7847/add \
  -H 'Content-Type: application/json' \
  -d '{"name":"BRAND","reason":"USER_REASON","aliases":["alias1","alias2"]}'
```

Keep the reason in the user's voice — don't paraphrase into corporate language. If they said "cheap garbage everywhere", store "cheap garbage everywhere" — not "low quality products with aggressive advertising".

If the user didn't give a reason, ask: "Got it. Any specific reason you want to remember why you decided to boycott?"

### When the user wants to REMOVE a brand

Detect phrases like:
- "Remove X from my boycott list"
- "Unban X"
- "Actually I'm fine with X now"

Call:
```bash
curl -s -X DELETE http://127.0.0.1:7847/remove \
  -H 'Content-Type: application/json' \
  -d '{"name":"BRAND"}'
```

### When the user wants to SEE their list

```bash
curl -s http://127.0.0.1:7847/list
```

Display the brands and reasons nicely:
- "You're currently boycotting N brands:"
- `- Temu: "Cheap garbage everywhere"`
- `- Shein: "Fast fashion, not supporting"`
- `- Nestlé (+ Nespresso, KitKat): "Water extraction in drought zones"`

### When the user asks about the extension

Explain that the Chrome extension needs to be loaded manually once:
1. Open `chrome://extensions`
2. Enable Developer mode
3. Click "Load unpacked"
4. Select: `${CLAUDE_PLUGIN_ROOT}/extension/`

After that, it auto-syncs every 30 seconds from the local server.

## Output

- **Confirmation messages** for add/remove actions — include the exact reason captured
- **List displays** grouped by company with reasons visible
- **Server status** if asked

For add, confirm like:
> "Added Temu to your boycott list. Reason: *cheap garbage, ads everywhere*. You'll see a red banner next time you land on temu.com or any page mentioning Temu."

## API reference (the local server)

| Method | Endpoint | Body | Returns |
|--------|----------|------|---------|
| GET | `/list` | — | `{"companies":[...], "updated_at":"..."}` |
| POST | `/add` | `{"name","reason","aliases":[]}` | `{"ok":true, "list":{...}}` |
| DELETE | `/remove` | `{"name"}` | `{"ok":true, "list":{...}}` |
| GET | `/health` | — | `{"status":"ok", "companies":N}` |

## Error Handling

- **Server not running** (connection refused on port 7847): run the setup script. Don't silently fail — tell the user.
- **Brand already on list**: server returns 409, tell the user gracefully ("Already on your list, reason: ...").
- **Brand not found on removal**: server returns 404, tell the user it wasn't on the list.
- **Invalid JSON**: server returns 400. Should not happen if the skill constructs the body correctly.

## Examples

**Example 1: Add with reason (most common)**

User: *"Ugh, another Shein ad. Never buying from them, fast fashion is killing everything."*

Agent action:
```bash
curl -s -X POST http://127.0.0.1:7847/add \
  -H 'Content-Type: application/json' \
  -d '{"name":"Shein","reason":"fast fashion is killing everything","aliases":["shein.com","SHEIN"]}'
```

Response: "Added Shein. Next time you land on a page mentioning them, you'll see your reason: *'fast fashion is killing everything'*."

**Example 2: Parent + subsidiaries**

User: *"Boycott Nestlé, their water extraction practices in drought zones are criminal."*

Agent action:
```bash
curl -s -X POST http://127.0.0.1:7847/add \
  -H 'Content-Type: application/json' \
  -d '{"name":"Nestlé","reason":"water extraction practices in drought zones are criminal","aliases":["Nestle","Nespresso","KitKat","Purina","Perrier","San Pellegrino"]}'
```

Response: "Added Nestlé with their main subsidiaries (Nespresso, KitKat, Purina, Perrier, San Pellegrino). The extension will match any of these. Want me to add more? Nestlé owns ~2,000 brands."

**Example 3: List view**

User: *"What's on my boycott list?"*

Agent action:
```bash
curl -s http://127.0.0.1:7847/list
```

Response formatting:
> You're currently boycotting 3 brands:
> - **Temu** — *"Cheap garbage, ads everywhere"*
> - **Shein** — *"Fast fashion is killing everything"*
> - **Nestlé** (+ Nespresso, KitKat, Purina, Perrier) — *"Water extraction practices in drought zones are criminal"*

**Example 4: Remove**

User: *"Actually remove Temu, I need something urgent from there."*

Agent action:
```bash
curl -s -X DELETE http://127.0.0.1:7847/remove \
  -H 'Content-Type: application/json' \
  -d '{"name":"Temu"}'
```

Response: "Removed Temu from your list. You won't get the warning anymore. (No judgment — but you can always add it back later.)"

## Resources

- **Server source**: `scripts/server.js` (bundled with this plugin)
- **Chrome extension**: `extension/` (bundled with this plugin, load manually once)
- **Setup script**: `scripts/setup.sh`
- **GitHub repo**: https://github.com/vdk888/boycott-filter (full source)
- **Landing page demo**: https://bubble-sentinel.netlify.app/boycott-filter.html
- **Video demo**: https://github.com/vdk888/boycott-filter/blob/main/demo.mp4
