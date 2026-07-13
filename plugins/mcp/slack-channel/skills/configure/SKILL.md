---
name: configure
description: Configure Slack channel tokens (bot token + app-level token). Use when writing or rotating the Slack bot and app-level tokens for the slack-channel plugin. Trigger with "/slack-channel:configure", "configure slack tokens", or "set up my slack bot token".
version: 1.0.1
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Requires Claude Code with the slack-channel plugin and a Slack app that already exists (tokens come from api.slack.com/apps); POSIX shell for chmod/mkdir.
tags: [slack, tokens, configuration, security]
user-invocable: true
argument-hint: "<bot-token> <app-token>"
allowed-tools: [Write, "Bash(chmod:*)", "Bash(mkdir:*)"]
---

# /slack-channel:configure

## Overview

Configure the Slack channel with your bot token and app-level token. This is
the single place tokens touch disk: the skill validates both token prefixes,
writes them to the state directory's `.env`, and locks the file to owner-only
permissions. It never echoes tokens back. The install walkthrough
(`/slack-channel:install` Step 3) delegates here.

## Prerequisites

- A Slack app already created (via `/slack-channel:install` Step 1 or
  manually at api.slack.com/apps) with:
  - the **Bot User OAuth Token** (`xoxb-...`) from **OAuth & Permissions**, and
  - the **App-Level Token** (`xapp-...`, scope `connections:write`) from
    **Socket Mode** settings.
- A writable home directory — state lives at `~/.claude/channels/slack/`.

## Usage

Pass both tokens as arguments, bot token first:

```
/slack-channel:configure <xoxb-bot-token> <xapp-app-token>
```

## Instructions

1. Parse the two arguments from `$ARGUMENTS`:
   - First token must start with `xoxb-` (Bot User OAuth Token)
   - Second token must start with `xapp-` (App-Level Token)

2. If either token is missing or has the wrong prefix, show this error and stop:
   ```
   Error: Two tokens required.
     - Bot token (starts with xoxb-) from OAuth & Permissions
     - App token (starts with xapp-) from Socket Mode settings

   Usage: /slack-channel:configure xoxb-... xapp-...
   ```

3. Create the state directory if it doesn't exist:
   ```
   ~/.claude/channels/slack/
   ```

4. Write the `.env` file at `~/.claude/channels/slack/.env`:
   ```
   SLACK_BOT_TOKEN=<bot-token>
   SLACK_APP_TOKEN=<app-token>
   ```

5. Set file permissions to owner-only:
   ```bash
   chmod 600 ~/.claude/channels/slack/.env
   ```

6. Confirm success:
   ```
   Slack channel configured.

   Start Claude with the Slack channel:
     claude --channels plugin:slack-channel@claude-code-plugins

   Or for development:
     claude --dangerously-load-development-channels server:slack

   Next: opt in a channel and pick its interaction mode with
   /slack-channel:access channel <id>  (defaults to mention-to-engage;
   pass --ambient for a dedicated bot channel). See ACCESS.md "Interaction modes".
   ```

## Output

- On success: `~/.claude/channels/slack/.env` written with both tokens and
  mode `0600`, plus the confirmation block above (server start command and
  the pointer to channel opt-in). Tokens are never echoed.
- On failure: the two-token usage error from step 2 and no file changes.

## Error Handling

- **Missing token or wrong prefix** — show the step-2 error block and stop;
  nothing is written. Bot tokens must start with `xoxb-`, app tokens with
  `xapp-`.
- **Tokens swapped** — the prefix check catches it; re-run with the bot token
  first.
- **Existing `.env`** — re-running overwrites it in place; this is the
  supported token-rotation path (Slack tokens are reusable; rotation happens
  at api.slack.com/apps).
- **Revoked/invalid tokens** — this skill only validates prefixes, not
  liveness. If the server later fails auth, run `/slack-channel:install
  doctor` (checks 4–5 test both tokens live against the Slack API).

## Examples

Both flows are the same command — the second run simply overwrites `.env`:

```
# First-time setup (tokens copied from api.slack.com/apps)
/slack-channel:configure xoxb-1234567890-EXAMPLE xapp-1-A0EXAMPLE

# Rotation after regenerating tokens in the Slack UI — same command, overwrites .env
/slack-channel:configure xoxb-NEW-TOKEN xapp-NEW-TOKEN
```

## Security

- Never echo the tokens back in the confirmation message
- Never log tokens to stdout or any file other than `.env`
- Always set 0o600 permissions on the `.env` file

## Resources

- [`skills/install/SKILL.md`](https://github.com/jeremylongshore/claude-code-slack-channel/blob/main/skills/install/SKILL.md) — the full install lifecycle that delegates to this skill (Step 3) and the doctor that verifies token liveness
- [`skills/access/SKILL.md`](https://github.com/jeremylongshore/claude-code-slack-channel/blob/main/skills/access/SKILL.md) — the next step after configuring: channel opt-in and pairing
- [`ACCESS.md`](https://github.com/jeremylongshore/claude-code-slack-channel/blob/main/ACCESS.md) — interaction modes referenced in the confirmation message
- [`README.md`](https://github.com/jeremylongshore/claude-code-slack-channel/blob/main/README.md) — quick start, including Node.js and Docker server alternatives
