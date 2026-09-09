# Cron Jobs

Configure these cron jobs in OpenClaw after completing `docs/setup.md`.

Use `openclaw cron add` or edit the crons section in `~/.openclaw/openclaw.json`.

> **Tip:** Set all times in your local timezone using the `tz` field. Adjust to match your work schedule.

---

## 1. Daily Meeting Prep

**When:** 8:30 AM on work days (before meetings start)
**Skill:** `meeting-prep`

```json
{
  "name": "Daily Meeting Prep",
  "schedule": {
    "kind": "cron",
    "expr": "30 8 * * 1-5",
    "tz": "America/New_York"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "thinking": "high",
    "timeoutSeconds": 1200,
    "model": "opus",
    "message": "Read ~/executive-assistant-skills/meeting-prep/SKILL.md and run daily meeting prep for today."
  },
  "delivery": {
    "mode": "none"
  }
}
```

> Adjust `expr` and `tz` for your work days and timezone.
> 1200s timeout (20 min) — needed for multi-meeting days with full research.

---

## 2. Daily Action Items → Todoist

**When:** 6:00 PM on work days (after all meetings end)
**Skill:** `action-items-todoist`

```json
{
  "name": "Daily Action Items → Todoist",
  "schedule": {
    "kind": "cron",
    "expr": "0 18 * * 1-5",
    "tz": "America/New_York"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "thinking": "high",
    "timeoutSeconds": 1200,
    "model": "opus",
    "message": "Read ~/executive-assistant-skills/action-items-todoist/SKILL.md and extract action items from today's meetings into Todoist. Draft follow-up emails as needed."
  },
  "delivery": {
    "mode": "announce",
    "channel": "whatsapp"
  }
}
```

---

## 3. Daily Executive Digest

**When:** 9:00 AM on weekdays
**Skill:** `executive-digest`

```json
{
  "name": "Daily Executive Digest",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * 1-5",
    "tz": "America/New_York"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "thinking": "high",
    "timeoutSeconds": 600,
    "model": "opus",
    "message": "Read ~/executive-assistant-skills/executive-digest/SKILL.md and generate the daily executive digest."
  },
  "delivery": {
    "mode": "announce",
    "channel": "whatsapp"
  }
}
```

---

## 4. Todoist Due-Today Email Drafts

**When:** 7:00 AM on work days (before the day starts)
**Skill:** `todoist-due-drafts`

Checks Todoist for tasks due today (and overdue) that involve pinging, emailing, or following up with someone. Auto-drafts the emails in the correct Gmail account/thread and sends a WhatsApp notification listing what was drafted. Doesn't send anything — just creates drafts for review.

```json
{
  "name": "Todoist Due-Today Email Drafts",
  "schedule": {
    "kind": "cron",
    "expr": "0 7 * * 1-5",
    "tz": "America/Argentina/Buenos_Aires"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "thinking": "high",
    "timeoutSeconds": 600,
    "model": "sonnet",
    "message": "Read ~/executive-assistant-skills/todoist-due-drafts/SKILL.md and process today's due tasks. Draft emails for any outreach/ping/follow-up tasks and notify via WhatsApp.\n\nAfter done: python3 scripts/cron_canary.py ping todoist-due-drafts"
  },
  "delivery": {
    "mode": "announce",
    "channel": "whatsapp"
  }
}
```

---

## 5. Granola Token Refresh

**When:** Every 5 hours (Granola tokens expire in ~6h)

```json
{
  "name": "Refresh Granola MCP token",
  "schedule": {
    "kind": "cron",
    "expr": "0 */5 * * *",
    "tz": "UTC"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "timeoutSeconds": 60,
    "model": "opus",
    "message": "Refresh the Granola MCP OAuth token. Read ~/.mcporter/credentials.json, extract refresh_token, POST to https://mcp-auth.granola.ai/oauth2/token with grant_type=refresh_token and client_id=client_01KHKZRS1RYY7SB7Z0A8Z13BE1, save new access_token and refresh_token back to credentials.json. Output NO_REPLY on success, alert on failure."
  },
  "delivery": {
    "mode": "none"
  }
}
```

---

## Notes

- **`sessionTarget: isolated`** is mandatory for all crons — shared sessions remember previous runs and may skip work thinking it's already done.
- **`model: opus`** for meeting-prep, action-items, and digest — these require deep reasoning and extraction quality. Use `sonnet` only for lightweight tasks (token refresh, health checks).
- **`thinking: high`** improves extraction and classification quality.
- All skill paths use `~/executive-assistant-skills/` absolute references so they work correctly from isolated cron sessions regardless of working directory.
