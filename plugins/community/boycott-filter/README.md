# Boycott Filter — Claude Code Plugin

Personal boycott list managed by your AI agent. Chrome extension warns you when you visit brands you've decided to avoid — with your own reasons.

## Why this exists

Ads on YouTube, Disney+, and every other platform have become so intrusive and omnipresent that they achieve the opposite of their goal — they make you want to *never* buy the product, just to spite the aggressive ad stuffing. So we built a tool to enforce that instinct and actually make it count. When you're fed up with a brand's marketing practices, you tell your AI agent, and from that point on you're reminded every time you're about to give them money. Turn your frustration into a real impact on their sales.

## How it works

1. Tell your Claude agent: *"Never buying from Temu again, cheap garbage everywhere"*
2. Agent adds Temu to your boycott list with your reason
3. Next time you visit a page with Temu products, a red banner reminds you why you hate them

## Features

| Feature | Description |
|---------|-------------|
| **Conversational management** | Just complain to your agent — it handles the rest |
| **Reason tracking** | Your own words are shown back to you as a reminder |
| **Brand aliases** | Boycott a parent company and catch all subsidiaries |
| **Chrome extension** | Red warning banner + badge on every matching page |
| **Offline capable** | Extension caches the list locally, works without the server |
| **Local & private** | Everything runs on your machine. No cloud, no tracking |

## Installation

### As a Claude Code Plugin

```bash
/plugin marketplace add vdk888/boycott-filter

/plugin install boycott-filter@boycott-filter-marketplace
```

### Setup

```bash
/boycott-filter:boycott-filter
```

Claude will start the local server and guide you through loading the Chrome extension.

Or manually:

```bash
# Start the server
node scripts/server.js &

# Load extension in Chrome:
# chrome://extensions → Developer mode → Load unpacked → select extension/
```

### Requirements

- Node.js 18+
- Chrome browser
- That's it.

## Usage

Just talk to your agent naturally:

- *"Boycott Nestl, their water practices are awful"*
- *"I'm done with Shein, add them to the list"*
- *"What's on my boycott list?"*
- *"Remove Amazon from the boycott list"*
- *"Add all Nestl brands — Nespresso, KitKat, Purina"*

## API

The local server runs on `http://127.0.0.1:7847`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/list` | Get boycott list |
| POST | `/add` | Add company `{"name":"X","reason":"...","aliases":["Y"]}` |
| DELETE | `/remove` | Remove company `{"name":"X"}` |
| GET | `/health` | Server status |

## License

MIT — Bubble Invest 2026
