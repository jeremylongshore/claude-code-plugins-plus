---
name: setup
description: Set up Promptbook — connect your account to start tracking builds
version: 1.4.0
author: Promptbook
license: MIT
allowed-tools: Bash
---

# Promptbook Setup

Help the user connect their Promptbook account using the device-code auth flow. Run all commands yourself via Bash — the user just waits for the browser sign-in.

## Privacy note
What is sent to promptbook.gg: session ID, project name, model, timestamps, prompt count, token counts, build time, lines changed, language, file extension counts, and tool usage counts. No source code, prompt content, file contents, file paths, or working directory is ever sent. To generate a title and summary for each build, the plugin calls Claude Haiku via the user's own Claude credentials — this data goes to Anthropic (same as normal Claude Code usage), never to Promptbook.
The plugin stays inactive until setup writes consent into `~/.promptbook/config.json`. Continuing with setup means the user consents to this data collection. After each session ends, a short background process may continue briefly to submit stats and generate the title/summary.

## Steps

1. **Create a setup session** by calling the API. Run this via Bash:
   ```bash
   curl -sL -X POST "https://promptbook.gg/api/auth/setup-session"
   ```
   Parse the JSON response to extract three values: `token`, `device_code`, and `setup_url`.

2. **Open the browser** for the user to sign in. Use the `setup_url` value from step 1:
   ```bash
   open "<setup_url value>"   # macOS
   xdg-open "<setup_url value>"  # Linux
   ```
   Tell the user: "Opening promptbook.gg — sign in or create an account to continue."
   If the browser can't be opened, show them the URL to open manually.

3. **Poll for authorization** — check every 2 seconds using the `token` value from step 1:
   ```bash
   curl -sL "https://promptbook.gg/api/auth/setup-session/<token value>/status"
   ```
   Parse the JSON response and check whether the `status` field equals `"authorized"`. Use a unique variable name like `poll_result` or `auth_status` to avoid colliding with shell built-ins (do NOT use a variable named `status`). Timeout after 5 minutes.

4. **Exchange the device code for an API key** using the `device_code` value from step 1. Use double quotes so the variable interpolates:
   ```bash
   curl -sL -X POST "https://promptbook.gg/api/auth/setup-session/exchange" \
     -H "Content-Type: application/json" \
     -d "{\"device_code\": \"<device_code value>\"}"
   ```
   Parse the JSON response to extract `api_key`.

5. **Save the config** to `~/.promptbook/config.json`. This is the canonical config location shared by both plugin and bash installs:
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

6. **Verify setup** with the server using the api_key from step 4:
   ```bash
   curl -sL -X POST "https://promptbook.gg/api/auth/verify-setup" \
     -H "Authorization: Bearer <api_key value>"
   ```

7. **Confirm completion.** Tell the user:
   - "You're all set! Tracking starts on your **next** Claude Code session."
   - "By completing setup, you've opted in to Promptbook tracking for this plugin install."
   - "Here's how it works: when you start a new session, the plugin automatically tracks your prompts, tokens, build time, and lines changed. When the session ends, it creates a build on promptbook.gg with a link you can share."
   - "After the session ends, a short background task may continue briefly to submit stats and generate your title/summary."
   - "This current session won't be tracked — start a new one to see it in action."
   - "Run `/setup` again anytime to reconnect or switch accounts."

8. **Offer history backfill.** After setup is complete, ask the user: "Want me to scan your Claude Code history for past sessions? I can find builds from the last 90 days and upload them to your profile."

   If they say yes, first find the bundled backfill script in the installed plugin:
   - `find ~/.claude -path "*/promptbook/scripts/backfill-history.js" -type f 2>/dev/null | head -1`

   If it does not exist, stop and tell the user the plugin install looks incomplete. Do not download code from the network.

   Then start it in the background:
   ```bash
   nohup node <path-to-backfill-history.js> \
     --days 90 \
     --generate-summaries \
     > "$HOME/.promptbook/backfill-history.log" 2>&1 < /dev/null &
   ```
   Before starting it, count matching JSONL files so you can tell the user roughly how much history was found:
   ```bash
   find "$HOME/.claude/projects" -name "*.jsonl" -type f 2>/dev/null | wc -l
   ```
   Tell the user: "Found <count> session files. History import started in the background. See status at https://promptbook.gg/setup/history"
   If the user declines, that's fine — they can always run it later.

## Important
- Run all curl commands via Bash, not by asking the user to do anything.
- The entire flow should be automated — the user just waits for the browser sign-in.
- If any step fails, give a clear error message and suggest running `/setup` again.
- Never display the API key to the user.
