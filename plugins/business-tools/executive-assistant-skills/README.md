# executive-assistant-skills

OpenClaw skills that replace a human executive assistant.

After setting up these skills with [OpenClaw](https://docs.openclaw.ai/), I let go of my human EA and replaced her entirely with my Claw. These five skills handle the core of what an executive assistant does: prepping for meetings, following up on action items, drafting emails, and keeping you on top of everything.

## What's included

| Skill | What it replaces |
|-------|-----------------|
| `meeting-prep` | EA researching attendees, pulling email history, and briefing you before each call |
| `action-items-todoist` | EA reviewing meeting notes, creating follow-up tasks, and drafting emails you promised to send |
| `email-drafting` | EA drafting replies, intro emails, scheduling responses, and thank-you notes in your voice |
| `executive-digest` | EA giving you a morning status update: stalled threads, pending intros, overdue tasks, calendar conflicts |
| `todoist-due-drafts` | EA checking your task list each morning, drafting follow-up/ping emails for anything due today, and notifying you to review |
| `humanizer` | Making sure nothing your Claw writes sounds like AI wrote it (originally by [biostartechnology](https://clawhub.ai/biostartechnology/humanizer)) |

## How it works

Each skill is a markdown file (`SKILL.md`) that tells your Claw exactly how to do the job. Your Claw reads the skill, follows the instructions, and delivers results to WhatsApp (or Slack, Telegram, etc.).

Skills run on cron schedules — meeting prep fires before your first meeting, action items run after your last meeting, and the digest hits every morning. You can also trigger any skill manually by asking your Claw.

All personal config (email accounts, timezone, work schedule, etc.) lives in a single `config/user.json` that's gitignored and never committed.

## Prerequisites

- [OpenClaw](https://docs.openclaw.ai/) running (local or server)
- Two Gmail accounts connected via [gog](https://github.com/xhit/gog) CLI
- [Granola](https://granola.ai/) or [Grain](https://grain.com/) for meeting transcripts (via mcporter MCP)
- [Todoist CLI](https://github.com/joelhoelting/todoist-cli) for task management
- A `style/` directory in your OpenClaw workspace with email style guides (see `docs/setup.md`)

---

## Quick setup

### 1. Clone the repo

```bash
git clone https://github.com/mgonto/executive-assistant-skills.git ~/executive-assistant-skills
```

### 2. Create your config

```bash
cp ~/executive-assistant-skills/config/user.example.json ~/executive-assistant-skills/config/user.json
# Edit user.json with your values — it's gitignored
```

### 3. Tell OpenClaw to load these skills

Edit `~/.openclaw/openclaw.json`:

```json
{
  "skills": {
    "load": {
      "extraDirs": ["~/executive-assistant-skills"]
    }
  }
}
```

### 4. Restart

```bash
openclaw gateway restart
```

### 5. Set up crons

See `docs/crons.md` for ready-to-paste cron job configs.

---

## Config fields

See `config/user.example.json` for the full template:

| Field | Example | Used for |
|-------|---------|----------|
| `name` | `"YourName"` | Meeting transcript queries, task attribution |
| `primary_email` | `"you@gmail.com"` | Gmail account 1 |
| `work_email` | `"you@company.com"` | Gmail account 2 |
| `whatsapp` | `"+1234567890"` | Digest and alert delivery |
| `timezone` | `"America/New_York"` | Meeting times, cron scheduling |
| `scheduling_cc` | `"assistant@company.com"` | CC on scheduling emails |
| `scheduling_silent_cc` | `"colleague@company.com"` | Silent CC (not mentioned in body) |
| `slack_username` | `"yourname"` | Slack DM for meeting briefs |
| `signature` | `"--yourname"` | Email sign-off |
| `workspace` | `"/home/user/.openclaw/workspace"` | Absolute path to your OpenClaw workspace |

---

## Full setup guide

- `docs/setup.md` — complete setup (mcporter, OAuth, gog, Todoist CLI)
- `docs/crons.md` — cron job templates for all skills

---

## Repository conventions

- `config/user.json` is **gitignored** — each person creates their own
- `config/user.example.json` is the committed template
- `state/` and `logs/` are gitignored (machine-local)
- Skills reference workspace files (`style/`, `state/`, `scripts/`) via `{user.workspace}/` prefix for portability
