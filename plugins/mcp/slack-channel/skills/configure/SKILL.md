---
name: configure
description: Configure Slack channel tokens (bot token + app-level token)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
user-invocable: true
argument-hint: "<bot-token> <app-token>"
allowed-tools: Read, Write, Bash(chmod:*)
compatible-with: claude-code
tags: [mcp, configure]
---

# /slack-channel:configure

## Overview

Configure the Slack channel MCP plugin by providing your Slack bot token and app-level token. Writes credentials to a secure `.env` file with owner-only permissions.

## Prerequisites

- A Slack app created at [api.slack.com/apps](https://api.slack.com/apps) with Socket Mode enabled
- A Bot User OAuth Token (`xoxb-...`) from OAuth & Permissions
- An App-Level Token (`xapp-...`) from Socket Mode settings
- Write access to `~/.claude/channels/slack/`

## Usage

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
   ```

## Security

- Never echo the tokens back in the confirmation message
- Never log tokens to stdout or any file other than `.env`
- Always set 0o600 permissions on the `.env` file

## Output

On success, displays:
```
Slack channel configured.

Start Claude with the Slack channel:
  claude --channels plugin:slack-channel@claude-code-plugins
```

On validation failure, displays the error with correct usage syntax.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Missing token argument | Fewer than 2 arguments provided | Show usage with required token prefixes |
| Invalid bot token prefix | First token does not start with `xoxb-` | Explain where to find the Bot User OAuth Token |
| Invalid app token prefix | Second token does not start with `xapp-` | Explain where to find the App-Level Token in Socket Mode settings |
| Permission denied | Cannot write to `~/.claude/channels/slack/` | Check directory permissions and create parent dirs if needed |

## Examples

**Standard configuration:**
```
/slack-channel:configure xoxb-1234567890-abcdef xapp-1-ABCDEF-ghijkl
→ Slack channel configured.
```

**Missing token error:**
```
/slack-channel:configure xoxb-1234567890
→ Error: Two tokens required.
  - Bot token (starts with xoxb-) from OAuth & Permissions
  - App token (starts with xapp-) from Socket Mode settings
```

## Resources

- [Slack API: Creating an app](https://api.slack.com/start/quickstart) — app setup walkthrough
- [Slack Socket Mode](https://api.slack.com/apis/socket-mode) — how to enable and get app-level tokens
- Access control: `/slack-channel:access` — configure who can message your session
