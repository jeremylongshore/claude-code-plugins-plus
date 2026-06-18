# Slack app creation — step-by-step

Reference for the `install` mode's Step 1 (manual path). If you want the
faster path, run `/slack-channel:install manifest` to generate a single
JSON file that pre-configures everything below in one import.

## What you'll end up with

Two tokens you'll paste into `/slack-channel:configure`:

- **Bot User OAuth Token**: starts with `xoxb-`. Authenticates the bot
  for sending messages, reading channels, etc.
- **App-Level Token**: starts with `xapp-`. Authenticates the Socket
  Mode WebSocket connection.

## Step 1.1: Create the app

1. Open https://api.slack.com/apps in your browser.
2. Click **Create New App** → **From scratch**.
3. Name: anything you like (e.g., "Claude Code Channel"). This name shows
   up in Slack as the bot's display name (you can change later).
4. Pick the workspace you want to install into.
5. Click **Create App**.

## Step 1.2: Enable Socket Mode

Socket Mode means the app speaks to Slack over an outbound WebSocket. No
public URL, no firewall punching, works from a laptop or a server.

1. In the left sidebar: **Settings** → **Socket Mode**.
2. Toggle **Enable Socket Mode**.
3. When prompted, give the token a name (e.g., `default`) and click
   **Generate**. The required scope is `connections:write`.
4. Copy the token — starts with `xapp-`. Keep it in a scratch buffer.

   You can also find this later under **Basic Information** → scroll to
   **App-Level Tokens**.

## Step 1.3: Configure Event Subscriptions

Tells Slack which events to push to the WebSocket.

1. Left sidebar: **Features** → **Event Subscriptions**.
2. Toggle **Enable Events**.
3. Scroll to **Subscribe to bot events**. Click **Add Bot User Event**
   and add each of these (one at a time):
   - `message.im` — direct messages to the bot
   - `message.channels` — public channels
   - `message.groups` — private channels
   - `app_mention` — `@bot` mentions in any channel the bot is in
4. Click **Save Changes** at the bottom.

## Step 1.4: Add OAuth scopes

These are the permissions the bot will hold once installed.

1. Left sidebar: **Features** → **OAuth & Permissions**.
2. Scroll to **Scopes** → **Bot Token Scopes** → **Add an OAuth Scope**.
3. Add all eight (one at a time):
   - `chat:write` — send messages
   - `channels:history` — read public channel messages
   - `groups:history` — read private channel messages
   - `im:history` — read DMs
   - `reactions:write` — add emoji reactions (used for ack indicators)
   - `files:read` — download files shared with the bot
   - `files:write` — upload files (used for long replies via `files.upload`)
   - `users:read` — resolve user IDs to display names

If you miss a scope, the bot will silently fail on whatever feature
needs it (e.g., reactions won't show without `reactions:write`). Add
all eight even if you don't think you need a feature yet.

## Step 1.5: Enable interactivity (for permission prompts)

Block Kit interactive prompts power the policy engine's `require_approval`
flow. Without interactivity enabled, approval buttons don't work.

1. Left sidebar: **Features** → **Interactivity & Shortcuts**.
2. Toggle **Interactivity** on.
3. The Request URL field can stay empty — Socket Mode handles interactivity
   over the same WebSocket.

## Step 1.6: Install to workspace

1. Left sidebar: **Settings** → **Install App** (or **Basic Information**
   → **Install your app**).
2. Click **Install to Workspace**.
3. Slack shows a permissions review screen. Click **Allow**.
4. You'll land on the **OAuth & Permissions** page with the installation
   complete. The **Bot User OAuth Token** (starts with `xoxb-`) is now
   visible at the top. Copy it — keep it next to the `xapp-` token in
   your scratch buffer.

## Step 1.7: (Optional) Set the bot display name + icon

1. Left sidebar: **Features** → **App Home**.
2. Configure the display name and default username Slack shows the bot as.
3. Optional: upload a custom icon.

These are cosmetic — the bot works without them.

## You now have

- `xoxb-...` (Bot User OAuth Token)
- `xapp-...` (App-Level Token with `connections:write`)
- An installed app

**Do not commit these tokens anywhere.** They go into
`~/.claude/channels/slack/.env` in Step 3, with mode `0600`. The
`/slack-channel:configure` skill handles this safely.

## Common mistakes to avoid

| Mistake | Symptom | Fix |
|---|---|---|
| Forgot to enable Socket Mode | Plugin fails to connect on start | Re-enable, regenerate `xapp-` token if it was deleted |
| Forgot `connections:write` on app token | "missing_scope" on Socket Mode connect | Generate a new app token with the scope |
| Forgot a bot event | Some message types don't reach the bot | Add the missing event, no reinstall needed |
| Forgot an OAuth scope | Feature silently fails (e.g., reactions, files) | Add the scope at OAuth & Permissions → reinstall app to workspace |
| Reinstalled and tokens changed | Old tokens stop working | Re-copy from OAuth & Permissions, run `/slack-channel:configure` again |

Reinstall is required after adding new OAuth scopes — Slack shows a
banner at the top of the OAuth page when this is needed.

## Next: Step 2 (add bot to channel)

Once you have both tokens copied, return to the install skill and
proceed to Step 2 — the silent-killer add-bot-to-channel step.
