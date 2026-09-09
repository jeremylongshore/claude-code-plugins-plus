---
name: executive-digest
description: "Generate the daily executive digest — a single WhatsApp summary of everything needing attention: stalled scheduling, pending intros, unanswered emails, promised follow-ups, open Todoist tasks, and upcoming calendar events. Use when running the daily digest cron, or when user asks for a status digest, daily summary, \"what's pending\", or \"catch me up\"."
---
# Daily Executive Digest

## Config — read before starting
Read `../config/user.json` (resolves to `~/executive-assistant-skills/config/user.json`).
Extract and use throughout:
- `primary_email`, `work_email` — both Gmail accounts to check
- `whatsapp` — for delivery
- `workspace` — absolute path to OpenClaw workspace

Do not proceed until you have these values.

## Debug Logging (MANDATORY)
Read `../config/DEBUG_LOGGING.md` for the full convention. Use `python3 {user.workspace}/scripts/skill_log.py exec-digest <level> "<message>" ['<details>']` at every key step. Log BEFORE and AFTER every external call (gog, mcporter, todoist-cli). On any error, log the full command and stderr before continuing.

## Steps

### 1. Read rules and state
- Read `{user.workspace}/style/DIGEST_RULES.md` for format and rules
- Read state files:
  - `{user.workspace}/state/scheduling-threads.json` — stalled threads (>3 days since proposed)
  - `{user.workspace}/state/decisions-memory.json` — context on people/companies
  - `{user.workspace}/state/digest-state.json` — avoid repeating items

Schema: `{"lastRun": "ISO date", "surfacedItems": [{"id": "<thread_id|task_id>", "type": "intro|followup|draft|task|calendar", "surfacedAt": "ISO date"}]}`. Use consistent IDs: Gmail thread IDs for email items, Todoist task IDs for tasks, calendar event IDs for calendar items. Do NOT use semantic strings like "calendar:golf-mar5" — always use the actual service ID. An item is "repeated" if its ID appeared in the last digest run. Re-surface only if its status changed since then.

### Error handling
If any data source (Gmail, Calendar, Todoist, Granola) fails or times out:
- Log the error, note it in the digest as "⚠️ [Source] unavailable — skipped"
- Continue with remaining sources — never halt the entire digest for one failure
- If BOTH Gmail accounts fail, abort and notify: "⚠️ Digest failed — Gmail unreachable"

### 2. Check Todoist
```bash
source {user.workspace}/.env
todoist-cli review
```
Include: overdue tasks, today's tasks, inbox (needs triage).
Format as "📋 Open Tasks" section: task name, due date, priority.
Highlight overdue first. Skip no-due-date tasks unless in inbox.

### 3. Check calendar (next 7 days) — BOTH accounts MANDATORY
```bash
gog --account {user.primary_email} --no-input calendar list primary --from "<today>T00:00:00-03:00" --to "<today+7>T00:00:00-03:00" --json
gog --account {user.work_email} --no-input calendar list primary --from "<today>T00:00:00-03:00" --to "<today+7>T00:00:00-03:00" --json
```
Use actual ISO8601 dates with ART timezone offset (-03:00). Relative dates like 'today' and '+7 days' are not supported by gog.
**CRITICAL: You MUST run BOTH commands and merge ALL events from both calendars into a single timeline.** Events live on different calendars — showing only one gives an incomplete picture. Deduplicate by time+title if the same event appears on both. Look for OOO, travel, vacation blocks, back-to-back conflicts, and double-bookings across calendars.

**RSVP check:** For each upcoming meeting with external attendees, check the `attendees[].responseStatus` field. If NO attendee (other than Gonto) has `accepted`, flag it in the digest and suggest pinging them to confirm attendance. Frame as: "⚠️ [Meeting] — nobody accepted yet. Ping [names] to confirm?"

### 4. Check Gmail for pending items — BOTH accounts

**Universal rule (applies to ALL sub-steps below):** Before surfacing ANY email item, check the FULL thread for replies from Gonto's team (Gonto, Alfred/Howie, or Giulia — see team-handled threads check in §4a). If ANY team member already replied → skip the item. If a draft exists for an already-replied thread → delete the draft silently (`gog gmail drafts delete <draftId> --force`). This prevents surfacing stale items.

Use `gog --account {email} --no-input gmail search "query" --json` for all searches. Run each query against BOTH accounts.

#### 4a. Pending intros and follow-ups
- Recent intros not actioned: `subject:(intro OR introduction OR connecting) newer_than:7d`
- Follow-ups from others: `(following up OR checking in OR circling back) newer_than:7d`
- Drafts awaiting send

**Team-handled threads (MANDATORY check):**
Before flagging ANY intro, follow-up, or email item as "pending" or "no reply", check the FULL thread for replies from Gonto's team. ANY reply from the following people counts as the item being handled:
- Gonto himself (m@gon.to, gonto@hypergrowthpartners.com)
- Alfred/Howie — scheduling assistant (alfred@hypergrowthpartners.com, alfred@hybridautopilotrun.com)
- Giulia (giulia@growth.li, giulia@hypergrowthpartners.com)

```bash
gog --account {user.work_email} --no-input gmail thread get <threadId>
```
Scan ALL messages in the thread. If ANY message is from any of the above addresses, the item is handled — do NOT surface it.

**Previously resolved items (MANDATORY check):**
Before surfacing ANY item, check `{user.workspace}/state/digest-state.json` for the `resolvedItems` array. If the item's ID (thread ID, task ID, or item key) appears in `resolvedItems`, do NOT re-surface it. When the user tells you an item is "done" or "already handled", immediately add its ID to the `resolvedItems` array in the state file.

Schema for resolvedItems: `"resolvedItems": [{"id": "<threadId|taskId|itemKey>", "resolvedAt": "ISO date", "note": "brief reason"}]`

**Draft hygiene (MANDATORY):**
- For each draft candidate, check if a matching message (same thread/subject intent) was already sent from that account.
- If already sent, delete the stale draft and exclude it from digest output.
- Only report drafts that still require a send/edit decision.

**Stale draft auto-cleanup (MANDATORY):**
- For EVERY draft found, fetch the full thread (`gog --account <email> --no-input gmail thread get <threadId> --json`) and check if Gonto already replied manually (sent message in the same thread AFTER the draft was created).
- **Fallback if `gmail thread get` returns empty `{}`**: This is a known gog CLI issue for some threads. Use `gog --account <email> --no-input gmail search "in:sent thread:<threadId>" --json` instead to check for sent replies in that thread. If search also fails, use the original search result snippets + metadata to make a best-effort determination.
- If Gonto already replied in the thread → **delete the draft automatically** (`gmail drafts delete <draftId> --force`) and do NOT surface it in the digest.
- This catches cases where auto-drafted replies become stale because Gonto replied on his own.

#### 4b. Unanswered emails from known contacts
Search BOTH Gmail accounts for recent inbound emails (last 7 days) from real people (not newsletters, automated, or system notifications) that have NO reply.
- If no reply exists after 24-48h, surface it as needing a decision (reply, ignore, or delegate)
- Prioritize: known contacts > first-time senders, VIPs always surface
- Frame as: "[Name] emailed about [topic] — reply, ignore, or delegate?"

#### 4c. Promised follow-ups not yet executed
Scan for commitments made but not yet completed:
- **From SENT mail (last 14 days):** Look for promises like "I'll intro you", "I'll send the deck", "let me connect you with", "I'll follow up with" — then check if the intro/email was actually sent
- **From Todoist:** Check open tasks tagged with follow-up intent (intros, send deck, ping someone) that are overdue or due today
- **From Granola/Grain (last 7 days):** Query recent meetings for action items assigned to you that haven't been completed:
  ```bash
  mcporter call granola query_granola_meetings --args '{"query": "What are all of {user.name} personal action items and commitments from the last 7 days? Only things they need to do."}'
  ```
  Cross-check each item against: (a) sent emails — was the intro/follow-up actually sent? (b) Todoist — is there already an open task for it? (c) calendar — was the meeting/call already scheduled?
  Surface anything that fell through the cracks — promised but not yet actioned.
- Frame as: "Promised [action] to [person] on [date] — still pending"

**⚠️ MANDATORY sent-mail verification for EVERY promised follow-up (no exceptions):**
Before surfacing ANY item from this section, you MUST search SENT mail on BOTH accounts for evidence it was already fulfilled:
```bash
gog --account {user.primary_email} --no-input gmail search "to:<person_or_company> in:sent newer_than:14d" --json
gog --account {user.work_email} --no-input gmail search "to:<person_or_company> in:sent newer_than:14d" --json
```
Also search by name/company if email address is unknown. Check the thread content — a sent reply in the same thread as the commitment means it was fulfilled. If you find a sent email that addresses the commitment → do NOT surface it. Log: `python3 {user.workspace}/scripts/skill_log.py exec-digest DEBUG "Follow-up already sent" '{"person": "<name>", "thread": "<id>"}'`

This is the #1 source of false positives in the digest. Never skip this check.

### Additional checks (per DIGEST_RULES.md)
For sections not explicitly covered above, follow `{user.workspace}/style/DIGEST_RULES.md`:
- OOO conflict detection (§2)
- Action-required non-urgent emails — billing, contracts, renewals (§7)
- Decision memory integration — read and apply `{user.workspace}/state/decisions-memory.json` for context on people/companies

### 5. Compile and send
- Format per `{user.workspace}/style/DIGEST_RULES.md`
- If items exist → send via WhatsApp to {user.whatsapp}
- **Also send to Chief of Staff:** Send the full digest as a single Slack DM to {user.chief_of_staff.name} (DM channel: `{user.chief_of_staff.slack_dm_channel}`). Use the Slack API (`chat.postMessage`) with the bot token. Prefix with "📋 *Executive Digest — <date>*".
- Update `{user.workspace}/state/digest-state.json` with items surfaced
- Nothing needs attention:
  - **Cron context**: NO_REPLY (don't send anything)
  - **User asked for digest**: Send "Nothing needs attention today ✅"
