# Slack Integration (Optional)

The Slack layer is provided by [`claude-code-slack-channel`](https://github.com/jeremylongshore/claude-code-slack-channel), a separate Claude Code plugin. It is **not bundled** with this project — install it independently if you want async team review via Slack.

## How It Works

When the Slack plugin is installed:
1. Triage results (Step 8) are displayed in the terminal AND sent to a configured Slack channel
2. Team members can send review commands from Slack
3. Claude processes commands from both terminal and Slack

When the Slack plugin is NOT installed:
1. Triage results display in the terminal (Step 8)
2. You interact directly in the terminal
3. Everything works — Slack is not required

## Setup

1. Install `claude-code-slack-channel` per its README
2. Register it in your Claude Code MCP config (separate from this plugin's `.mcp.json`)
3. Configure Slack tokens in the bridge's `.env`

See [000-docs/004-AT-REFF-slack-review-flow.md](../../000-docs/004-AT-REFF-slack-review-flow.md) for the review flow design.
