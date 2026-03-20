# Slack Channel for Claude Code

Two-way Slack ↔ Claude Code bridge. Chat with Claude from Slack DMs and channels, just like you'd chat in the terminal.

[![CI](https://github.com/jeremylongshore/claude-code-slack-channel/actions/workflows/ci.yml/badge.svg)](https://github.com/jeremylongshore/claude-code-slack-channel/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Research Preview** — Channels require Claude Code v2.1.80+ and `claude.ai` login.

## How It Works

```
Slack workspace (cloud)
    ↕ WebSocket (Socket Mode — outbound only, no public URL)
server.ts (local MCP server, spawned by Claude Code)
    ↕ stdio (MCP transport)
Claude Code session
```

Socket Mode means **no public URL needed** — works behind firewalls, NAT, anywhere.

## Quick Start

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → From scratch
2. **Socket Mode**: Settings → Socket Mode → Enable → Generate App-Level Token (`xapp-...`) with `connections:write` scope
3. **Event Subscriptions**: Enable → Subscribe to bot events:
   - `message.im` — DMs
   - `message.channels` — public channels
   - `message.groups` — private channels
   - `app_mention` — @ mentions
4. **Bot Token Scopes** (OAuth & Permissions):
   - `chat:write` — send messages
   - `channels:history` — read public channels
   - `groups:history` — read private channels
   - `im:history` — read DMs
   - `reactions:write` — add reactions
   - `files:read` — download shared files
   - `files:write` — upload files
   - `users:read` — resolve display names
5. **Install to Workspace** → Copy Bot Token (`xoxb-...`)

### 2. Configure Tokens

```bash
/slack-channel:configure xoxb-your-bot-token xapp-your-app-token
```

### 3. Run

Pick your runtime:

#### Option A: Bun (recommended)

```bash
cd slack && bun install
# Current (claude-code-plugins marketplace):
claude --channels plugin:slack-channel@claude-code-plugins
# Future (after upstream approval):
# claude --channels plugin:slack-channel@claude-plugins-official
```

#### Option B: Node.js / npx

```bash
cd slack && npm install
# In .mcp.json, change command to: "npx", args: ["tsx", "server.ts"]
claude --channels plugin:slack-channel@claude-code-plugins
```

#### Option C: Docker

```bash
cd slack && docker build -t claude-slack-channel .
# In .mcp.json, change command to: "docker", args: ["run", "--rm", "-i", "-v", "~/.claude/channels/slack:/state", "claude-slack-channel"]
claude --channels plugin:slack-channel@claude-code-plugins
```

### 4. Pair Your Account

1. DM the bot in Slack — you'll get a 6-character pairing code
2. In your terminal: `/slack-channel:access pair <code>`
3. You're connected. Chat away.

## Access Control

See [ACCESS.md](ACCESS.md) for the full schema.

```bash
/slack-channel:access policy allowlist       # Only pre-approved users
/slack-channel:access add U12345678          # Add a user
/slack-channel:access remove U12345678       # Remove a user
/slack-channel:access channel C12345678      # Opt in a channel
/slack-channel:access channel C12345678 --mention  # Require @mention
/slack-channel:access status                 # Show current config
```

## Security

- **Sender gating**: Every inbound message hits a gate. Ungated messages are silently dropped before reaching Claude.
- **Outbound gate**: Replies only work to channels that passed the inbound gate.
- **File exfiltration guard**: Cannot send `.env`, `access.json`, or other state files through the reply tool.
- **Prompt injection defense**: System instructions explicitly tell Claude to refuse pairing/access requests from Slack messages.
- **Bot filtering**: All `bot_id` messages are dropped (prevents bot-to-bot loops).
- **Link unfurling disabled**: All outbound messages set `unfurl_links: false, unfurl_media: false`.
- **Token security**: `.env` is `chmod 0o600`, never logged, never in tool results.
- **Static mode**: Set `SLACK_ACCESS_MODE=static` to freeze access at boot (no runtime mutation).

## Development

```bash
# Dev mode (bypasses plugin allowlist):
claude --dangerously-load-development-channels server:slack
```

## One-Pager & System Analysis

[Full project one-pager and operator-grade system analysis](https://gist.github.com/jeremylongshore/2bef9c630d4269d2858a666ae75fca53)

## License

MIT
