---
name: setup
description: |
  Set up Promptbook — connect your account to start tracking builds.
  Use when the user wants to enable session analytics on promptbook.gg.
  Trigger with "/setup" or "set up promptbook".
version: 1.4.0
author: Promptbook <contact@promptbook.gg>
license: MIT
allowed-tools: Bash(curl:*), Bash(open:*), Bash(xdg-open:*), Bash(mkdir:*), Bash(cat:*), Bash(chmod:*), Bash(node:*), Bash(nohup:*), Bash(find:*), Bash(wc:*), Read
compatible-with: claude-code
tags: [analytics, telemetry, setup, onboarding]
---

# Promptbook Setup

## Overview

Connect a Promptbook account using the device-code OAuth flow. After consent, the plugin tracks session metrics (prompts, tokens, build time, lines changed) and publishes shareable build cards on promptbook.gg.

## Prerequisites

- Internet access (calls promptbook.gg API)
- A browser for the sign-in step
- Node.js installed (used by hook scripts)

## Privacy Note

**What IS sent to promptbook.gg:** session ID, project name, model, timestamps, prompt count, token counts, build time, lines changed, language, file extension counts, and tool usage counts.

**What is NEVER sent:** source code, prompt content, file contents, file paths, or working directory.

To generate a title and summary for each build, the plugin calls Claude Haiku via the user's own Claude credentials — this data goes to Anthropic (same as normal Claude Code usage), never to Promptbook.

The plugin stays inactive until setup writes consent into `~/.promptbook/config.json`. Continuing with setup means the user consents to this data collection. After each session ends, a short background process may continue briefly to submit stats and generate the title/summary.

## Instructions

Run all commands via Bash — the user just waits for the browser sign-in.

### 1. Create a setup session

```bash
curl -sL -X POST "https://promptbook.gg/api/auth/setup-session"
```

Parse the JSON response to extract three values: `token`, `device_code`, and `setup_url`.

### 2. Open the browser

Use the `setup_url` value from step 1:

```bash
open "<setup_url value>"   # macOS
xdg-open "<setup_url value>"  # Linux
```

Tell the user: "Opening promptbook.gg — sign in or create an account to continue."
If the browser cannot open, show the URL for manual access.

### 3. Poll for authorization

Check every 2 seconds using the `token` from step 1:

```bash
curl -sL "https://promptbook.gg/api/auth/setup-session/<token value>/status"
```

Parse the JSON and check whether `status` equals `"authorized"`. Use a unique variable name like `poll_result` or `auth_status` (do NOT use a variable named `status`). Timeout after 5 minutes.

### 4. Exchange device code for API key

```bash
curl -sL -X POST "https://promptbook.gg/api/auth/setup-session/exchange" \
  -H "Content-Type: application/json" \
  -d "{\"device_code\": \"<device_code value>\"}"
```

Parse the JSON response to extract `api_key`.

### 5. Save the config

Write to `~/.promptbook/config.json` — the canonical config location shared by both plugin and bash installs:

```bash
mkdir -p "$HOME/.promptbook"
cat > "$HOME/.promptbook/config.json" << 'JSONEOF'
{
  "api_key": "<api_key from step 4>",
  "api_url": "https://promptbook.gg",
  "auto_summary": true,
  "telemetry_consent": true
}
JSONEOF
chmod 600 "$HOME/.promptbook/config.json"
```

The `chmod 600` restricts config access to the owning user only — the file contains the API key.

### 6. Verify setup

```bash
curl -sL -X POST "https://promptbook.gg/api/auth/verify-setup" \
  -H "Authorization: Bearer <api_key value>"
```

### 7. Confirm completion

Tell the user:
- "You're all set! Tracking starts on your **next** Claude Code session."
- "By completing setup, you've opted in to Promptbook tracking for this plugin install."
- "After the session ends, a short background task may continue briefly to submit stats and generate your title/summary."
- "Run `/setup` again anytime to reconnect or switch accounts."

### 8. Offer history backfill

Ask the user: "Want me to scan your Claude Code history for past sessions? I can find builds from the last 90 days and upload them to your profile."

If yes, find the bundled backfill script:

```bash
find ~/.claude -path "*/promptbook/scripts/backfill-history.js" -type f 2>/dev/null | head -1
```

If it does not exist, stop and tell the user the plugin install looks incomplete. Do not download code from the network.

Count matching session files first:

```bash
find "$HOME/.claude/projects" -name "*.jsonl" -type f 2>/dev/null | wc -l
```

Then start in the background:

```bash
nohup node <path-to-backfill-history.js> \
  --days 90 \
  --generate-summaries \
  > "$HOME/.promptbook/backfill-history.log" 2>&1 < /dev/null &
```

Tell the user: "Found <count> session files. History import started in the background. See status at https://promptbook.gg/setup/history"

## Output

On success, display:
- Confirmation that tracking is active
- Link to the user's promptbook.gg profile
- Note that the current session is not tracked — start a new one

## Error Handling

- If any curl call fails, show the HTTP status and suggest running `/setup` again
- If the browser cannot open, display the URL for manual access
- If polling times out after 5 minutes, abort and suggest retrying
- Never display the API key to the user

## Examples

```
User: /setup
Agent: Creating setup session... Opening promptbook.gg — sign in or create an account.
       Waiting for authorization... Authorized! Saving config...
       You're all set! Tracking starts on your next Claude Code session.
       Want me to scan your history for past sessions?
```

## Resources

- [Promptbook website](https://promptbook.gg)
- [Plugin repository](https://github.com/promptbookgg/claude-code-plugin)
