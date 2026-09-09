# Setup Guide

Complete setup for a new machine. Follow in order.

## 1. Clone the repo

```bash
git clone https://github.com/mgonto/executive-assistant-skills.git ~/executive-assistant-skills
```

> The repo must live at `~/executive-assistant-skills/`. Skills reference config at `../config/user.json` which resolves relative to each skill's location.

## 2. Create your user config

```bash
cp ~/executive-assistant-skills/config/user.example.json ~/executive-assistant-skills/config/user.json
```

Edit `user.json` with your personal values — it's gitignored and never committed.

Fields to fill in:
- `name` / `full_name` — your name (used in Granola queries)
- `whatsapp` — your WhatsApp phone number (e164 format, e.g. `+1234567890`)
- `timezone` — IANA timezone string (e.g. `America/Argentina/Buenos_Aires`)
- `work_days` — your working days (e.g. `["Monday", "Wednesday"]`)
- `availability_window` — hours available for meetings (e.g. `"15:00-19:00"`)
- `primary_email` — personal Gmail account
- `work_email` — work Gmail account
- `scheduling_cc` — scheduling assistant email (CC'd on all scheduling emails)
- `scheduling_silent_cc` — silent CC for scheduling visibility (never mentioned in email body)
- `slack_username` — your Slack username for DM delivery
- `calendar_id` — usually `"primary"`
- `signature` — email sign-off (e.g. `"--yourname"`)
- `workspace` — absolute path to your OpenClaw workspace (e.g. `/home/youruser/.openclaw/workspace`)

## 3. Configure OpenClaw to load these skills

Edit `~/.openclaw/openclaw.json`. Find the `"skills"` key and add `"load"`:

```json
{
  "skills": {
    "load": {
      "extraDirs": ["~/executive-assistant-skills"]
    },
    "install": {
      "nodeManager": "npm"
    }
  }
}
```

Then restart the gateway:

```bash
openclaw gateway restart
```

## 4. Build your email style guide

The `email-drafting` skill writes emails in your voice — but it needs to learn your voice first. You do this by analyzing your sent emails and creating a style guide.

### Generate the style files

Ask your Claw:

> "Read my last 200 sent emails from both accounts and create an email writing style guide. Analyze: sentence length, greeting patterns, sign-off patterns, vocabulary, tone, punctuation habits, and common phrases. Save it to `style/EMAIL_STYLE.md`."

Then:

> "Now create `style/EMAIL_TEMPLATES.md` with template patterns for the email types I send most: intros, follow-ups, scheduling, thank-you notes, VC/investor replies. Base each template on real examples from my sent mail."

Finally, create an empty feedback log:

```bash
touch ~/.openclaw/workspace/style/FEEDBACK_LOG.md
```

This is where corrections accumulate over time. Every time you tell your Claw "that draft was too formal" or "I wouldn't say it that way," it logs the feedback. Latest corrections always override the original style guide.

### What you end up with

```
~/.openclaw/workspace/style/
├── EMAIL_STYLE.md          # Your writing voice (auto-generated from sent mail)
├── EMAIL_TEMPLATES.md      # Template patterns for common email types
├── FEEDBACK_LOG.md          # Running log of your corrections (starts empty)
├── DIGEST_RULES.md          # Format rules for the executive digest
└── MEETING_PREP_RULES.md   # Additional research steps for meeting prep
```

The digest and meeting prep rules files are optional — create them if you want to customize the output format beyond the defaults in the skill files.

## 5. Keep USER.md in sync

Your OpenClaw workspace should have a `USER.md` with the same info as `user.json` in human-readable form. Skills read `user.json` programmatically; `USER.md` provides context to the agent in every session. Keep both in sync when you update one.

## 5. Install mcporter

```bash
npm i -g mcporter
```

Create `~/.openclaw/workspace/config/mcporter.json` (or wherever mcporter expects its config):

```json
{
  "servers": {
    "granola": {
      "type": "http",
      "url": "https://mcp.granola.ai/mcp"
    },
    "grain": {
      "type": "http",
      "url": "https://mcp.grain.com/mcp"
    },
    "todoist": {
      "type": "http",
      "url": "https://ai.todoist.net/mcp"
    }
  }
}
```

## 6. Authenticate Granola (OAuth on headless VPS)

Granola uses OAuth. On a headless server (no browser), the flow is:

1. Run any mcporter call — it triggers OAuth and starts a local callback server:
   ```bash
   mcporter list-tools granola
   ```
2. If it crashes on `xdg-open`, note the auth URL and callback port from the output
3. From your local machine, SSH tunnel the callback port:
   ```bash
   ssh -R <PORT>:localhost:<PORT> user@your-vps
   ```
4. Open the auth URL in your local browser, complete OAuth
5. Callback hits the SSH tunnel → mcporter receives the authorization code
6. Tokens saved to `~/.mcporter/credentials.json`

### Granola token refresh

Granola tokens expire every ~6 hours. Set up the refresh cron (see `docs/crons.md`).

If the refresh token itself expires (e.g. after an outage), re-run:
```bash
mcporter auth granola --reset
```

## 7. Authenticate Grain (OAuth)

Same OAuth flow as Granola:
```bash
mcporter list-tools grain
```

## 8. Authenticate Todoist

Todoist tokens last ~10 years. Same OAuth flow:
```bash
mcporter list-tools todoist
```

## 9. Install todoist-cli

```bash
npm install -g todoist-cli  # or the package name used in your setup
```

Create `~/.openclaw/workspace/.env` with your Todoist API token:
```bash
TODOIST_API_TOKEN=your_token_here
```

## 10. Set up Google workspace CLI (gog)

Used for Gmail and Calendar access:
```bash
# Follow gog setup instructions in workspace/skills/gog/SKILL.md
```

Authenticate both accounts:
```bash
gog auth login --account your-primary@email.com
gog auth login --account your-work@email.com
```

## 11. Verify everything works

```bash
mcporter list-tools granola   # should list meeting tools
mcporter list-tools grain     # should list transcript tools
mcporter list-tools todoist   # should list task tools
gog gmail list "in:inbox" --account your@email.com --max 1 --json
source ~/.openclaw/workspace/.env && todoist-cli today --json  # should list today's tasks
```

Then set up cron jobs per `docs/crons.md`.

### Skill-specific notes

- **todoist-due-drafts** requires both `todoist-cli` (step 9) and `gog` (step 10) to be working. It reads Todoist tasks, searches Gmail for existing threads, and creates drafts — so all three auth flows must be complete. It also depends on the `email-drafting` skill's style guide (step 4).
