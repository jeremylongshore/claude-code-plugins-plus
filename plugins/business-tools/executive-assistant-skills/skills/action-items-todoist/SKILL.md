---
name: action-items-todoist
description: "Extract action items from today's Granola/Grain meetings, create Todoist tasks, complete fulfilled tasks, and draft meeting-triggered follow-up emails. Use when running the daily action items cron, post-meeting cron, or when user asks to process meeting action items. NOT for general email drafting without meeting context."
---
# Action Items → Todoist + Email Drafts

## Config — read before starting
Read `../config/user.json` (resolves to `~/executive-assistant-skills/config/user.json`).
Extract and use throughout:
- `name`, `full_name` — to identify your action items in meeting notes (e.g. "Gonto (Martin)")
- `whatsapp` — for result delivery
- `workspace` — absolute path to OpenClaw workspace

Do not proceed until you have these values.

## Debug Logging (MANDATORY)
Read `../config/DEBUG_LOGGING.md` for the full convention. Use `python3 {user.workspace}/scripts/skill_log.py action-items <level> "<message>" ['<details>']` at every key step. Log BEFORE and AFTER every external call (gog, mcporter, todoist-cli). On any error, log the full command and stderr before continuing.

## Steps

### 0. Check today's calendar for meetings (BOTH accounts)
Before querying Granola, get today's actual meetings from BOTH calendars to know what to expect:
```bash
python3 {user.workspace}/scripts/skill_log.py action-items INFO "Starting action-items run"

# Get today's date in YYYY-MM-DD and tomorrow's
TODAY=$(date -u -d "$(TZ=America/Argentina/Buenos_Aires date +%Y-%m-%d)" +%Y-%m-%d)
TOMORROW=$(date -u -d "$(TZ=America/Argentina/Buenos_Aires date -d '+1 day' +%Y-%m-%d)" +%Y-%m-%d)

# Check BOTH calendars
gog --account {user.primary_email} --no-input calendar list primary --from "${TODAY}T00:00:00-03:00" --to "${TOMORROW}T00:00:00-03:00" --json 2>&1
gog --account {user.work_email} --no-input calendar list primary --from "${TODAY}T00:00:00-03:00" --to "${TOMORROW}T00:00:00-03:00" --json 2>&1
```
Log the results: `python3 {user.workspace}/scripts/skill_log.py action-items DEBUG "Calendar events found" '{"primary": N, "work": M, "total": N+M}'`

Merge events from both calendars. Filter for meetings with attendees (skip solo/personal events). This gives you the ground truth of what meetings happened today — use it to cross-check Granola results and catch any meetings Granola missed.

**CRITICAL date syntax:** Use explicit ISO8601 dates with `-03:00` offset. Do NOT use relative expressions like `+1 day`, `today`, or `tomorrow` in gog flags — they may not be supported. Always compute the actual date strings.

### 1. Get today's meetings from Granola

**Timezone note:** Granola stores meeting times in UTC. For ART (UTC-3), querying "today" means using today's date AND tomorrow's date in UTC. E.g., for March 3 ART, query `custom_start: "2026-03-03"` and `custom_end: "2026-03-04"` to capture all ART-day meetings.

```bash
mcporter call granola list_meetings --args '{"time_range": "custom", "custom_start": "<today YYYY-MM-DD>", "custom_end": "<tomorrow YYYY-MM-DD>"}'
```
Collect meeting IDs and titles. Log: `python3 {user.workspace}/scripts/skill_log.py action-items INFO "Granola meetings found" '{"count": N, "titles": [...]}'`

**Cross-check with calendar:** Compare Granola meetings against the calendar events from Step 0. If a calendar meeting with attendees has no Granola match (by time overlap within 15 min), log a warning — it may not have been recorded. Proceed with what Granola has, but note unmatched meetings in the output.

Skip if no meetings (from either Granola or calendar).

### 2. Query Granola for MY action items + email triggers
```bash
mcporter call granola query_granola_meetings --args '{"query": "What are all of {user.name} ({user.full_name}) personal action items, follow-ups, and commitments from these meetings? Only things HE needs to do, not what others committed to. For each item, include the specific person, company, project, or candidate name involved — never use generic references. Also identify: any promises made to do ANYTHING via email (intros, follow-ups, sending docs, sharing info, connecting people, etc.), and whether each meeting was a FIRST meeting with that person/company or a follow-up.", "document_ids": ["<id1>", "<id2>", ...]}'
```
Pass ALL meeting IDs. Preserve citation links.

### 3. Create Todoist tasks

> **Note:** Load env in the same command — each shell call is a fresh session.

Read `{user.workspace}/skills/todoist-api/SKILL.md` for CLI usage. For each action item:
```bash
source {user.workspace}/.env && todoist-cli add "<actionable title>" --description "<context: meeting name, meeting date/time, who requested, Granola link>" --priority <1-4> --labels "<relevant>"
```

**Task description MUST include:**
- Meeting name (e.g. "Braintrust Weekly")
- Meeting date and time (e.g. "Wed Mar 5, 15:00 ART")
- Who requested / context
- Granola citation link

**Rules:**
- **Only your actions**: Granola summaries often list "next steps" without clear ownership. Be skeptical — if the action could belong to the other person (e.g. "digest their own content", "check availability", "get back to us"), do NOT create a task. When in doubt, create a FOLLOW-UP task ("Ping X about Y") rather than an ownership task.
- **Capture commitments from others**: If the other person said they'd do something (e.g. "I'll get back in 2 days"), create a follow-up/ping task with the appropriate due date, not a task to do the thing yourself.
- **Specificity**: Every task MUST include specific name of person/company/project
- **Due dates**: If implied deadline, use `--due` with natural language
- **Labels**: Tag: intro, follow-up, email, urgent as appropriate
- **Priority**: 4=urgent/time-sensitive, 3=promised deliverables, 2=general follow-ups, 1=normal

#### No split tasks for sequential steps (MANDATORY)
Never create separate tasks for steps that are part of the same workflow. If the action is "prepare X then send X" — that's ONE task, not two. Examples:
- ❌ "Build proposal" + "Send proposal" → ✅ "Build and send proposal"
- ❌ "Write draft" + "Send email" → ✅ "Draft and send email to X"
- ❌ "Review deck" + "Share deck" → ✅ "Review and share deck with X"

One task per intent. The user will naturally do the steps in order.

#### Todo dedup (MANDATORY)
Before creating a task, run a duplicate check against open Todoist tasks:
1. Normalize proposed title (lowercase, trim punctuation, collapse whitespace)
2. Search open tasks (`source {user.workspace}/.env && todoist-cli list --filter "!completed"`) and compare normalized content
3. Treat near-identical intro tasks as duplicates (e.g., "Intro David to Marcos" vs "Intro David (n8n) to Marcos Nils")
4. If duplicate exists: do NOT create a new task; append meeting context to the existing task description when useful
5. In output, report dedup decisions under `Skipped as duplicates:`

### 4. Draft follow-up emails
For ANY email that needs drafting (intros, follow-ups, VC replies, sending docs, etc.):
- **Read and follow `~/executive-assistant-skills/email-drafting/SKILL.md`** — it is the single source of truth for all drafting rules, style, templates, humanization, and delivery
- Identify draft triggers from meeting notes:
  - Promised intros or follow-ups
  - Promised docs/PDFs/decks
  - First call with a VC or new lead
  - Any promise to email someone
- When in doubt about whether to draft → DRAFT IT
- **Exception**: The proposal-only commitment rule below overrides this. If the commitment is to build a proposal first, do NOT draft — create a Todoist task only.
- **HGP Deck**: `{user.workspace}/assets/HGP_Deck_2025.pdf` — attach via `--attach {user.workspace}/assets/HGP_Deck_2025.pdf`. Say "Hypergrowth Partners deck" in the email body (not "one-pager" or "our deck")
- **When drafting intros to known contacts**: search sent emails for previous intros to them, use the same format, tone, and description

#### Intro-specific hard requirements (MANDATORY)
If action items include intros, follow this exactly:
1. Create **one separate intro draft per intro pair** (never merge multiple intros into one generic follow-up).
2. Subject must be explicit: `Intro: <Person A> <> <Person B>`.
3. Body must include:
   - one-line who each person is,
   - one-line context for why this intro is happening,
   - close with `I'll let you two take it from here.` and `{user.signature}`.
4. **Never replace intro drafts with a generic recap email** like "Great meeting today" when intros were promised.
5. If recipient emails are known, create Gmail drafts immediately; if any email is missing, still generate the full draft text and report `MISSING_EMAIL: <name>`.
6. In the WhatsApp result, include an `Intro drafts created:` section listing each intro pair and whether it was drafted in Gmail or blocked by missing email.

#### First VC / first dealflow call follow-up (MANDATORY)
When the meeting is a FIRST call with a VC or dealflow company:
1. Create a first-meeting follow-up draft (unless blocked by proposal-only rule below).
2. Use meeting-specific context in the body (what was discussed, explicit next steps, concrete offers), not generic pleasantries.
3. Include your positioning (how you work) and attach `{user.workspace}/assets/HGP_Deck_2025.pdf` when relevant.
4. Allowed to use "Great meeting today" only for this first-meeting follow-up class.

#### Proposal-only commitment rule (MANDATORY)
If you committed to "build a proposal" (or equivalent: proposal/deck/scope draft to prepare first):
- **Do NOT draft an outbound email yet**.
- Create a **single** Todoist task to build AND send the proposal — e.g. "Build and send advisory proposal to Gabriel (BairesDev)".
- Do NOT create separate tasks for "build" and "send" — that's redundant. One task covers the full lifecycle.

### 5. Check if existing Todoist tasks were fulfilled in today's meetings
After processing action items, also check if any **existing open Todoist tasks** were addressed/completed during today's meetings:
1. List open tasks: `source {user.workspace}/.env && todoist-cli list`
2. For each meeting, check if the discussion covered or fulfilled any open task (e.g., "Share AI strategy with Colin" → discussed AI strategy directly with Colin in the call)
3. If a task was clearly fulfilled in the meeting, **complete it**: `source {user.workspace}/.env && todoist-cli complete <task_id>`
4. Report completed tasks in the output: "✅ Completed: [task] — fulfilled during [meeting name]"

This ensures Todoist stays clean and reflects what actually happened.

## Error handling
- If `gog calendar` fails: log the error with full command + stderr (`python3 {user.workspace}/scripts/skill_log.py action-items ERROR "gog calendar failed" '{"command": "...", "stderr": "..."}'`), continue with the other account and/or Granola-only.
- If `mcporter call granola` fails with auth errors: report "⚠️ Granola auth expired, run `mcporter auth granola --reset`" and stop.
- If `todoist-cli` fails: verify `.env` is sourced and token is valid. Report error.
- If Grain MCP is unavailable: proceed with Granola-only extraction, note in output "⚠️ Grain unavailable, results are Granola-only."
- If any step fails, continue with remaining steps when possible — don't abort the entire run for one failure.

## Deduplication (CRITICAL — prevents duplicate tasks)

### Meeting-level dedup
- **FIRST STEP before any processing**: Read `{user.workspace}/state/processed-meetings-YYYY-MM-DD.json` (if it exists — array of Granola meeting IDs)
- Skip any meetings whose ID is already in that list — do NOT re-process them
- **Immediately after processing each meeting** (before moving to the next), append its Granola meeting ID to the file. Do NOT wait until the end — write after each meeting to prevent races with other crons.
- This file is the single source of truth for "was this meeting already processed today?"

> **Note:** Titles are fragile for recurring meetings that share the same name. Always dedup by Granola meeting ID.

### Task-level dedup
- Before creating ANY task, check BOTH open AND recently completed tasks for near-duplicates:
  1. Fetch open tasks: `source {user.workspace}/.env && todoist-cli list`
  2. Fetch today's completed tasks: use Todoist Sync API `completed/get_all` with `since=<today 00:00 UTC>` or `source {user.workspace}/.env && todoist-cli list --filter "completed today"` if supported
  - Same person + same action intent = duplicate (e.g. "Text Morgane about Hank" and "Text Morgane (Braintrust) after Hank call")
  - Normalize: lowercase, strip parentheticals, collapse whitespace
  - If duplicate exists in EITHER open or completed → SKIP, do not create
- Report skipped duplicates in output: "⏭️ Skipped (already exists): [task]"
- **Why check completed tasks**: The user may have already completed a task created by a post-meeting cron earlier today. Recreating it is wrong — the work is done.

### Why both layers matter
Post-meeting crons fire per-meeting. The daily end-of-day cron processes ALL meetings. Without meeting-level dedup, the same meeting gets processed twice. Without task-level dedup, even if the meeting is re-processed (e.g. file write failed), individual tasks won't be duplicated.

### Dedup is NON-NEGOTIABLE
If a meeting appears in `processed-meetings-YYYY-MM-DD.json`, do NOT process it again under any circumstances — even if you think the post-meeting cron "might have missed something." The post-meeting cron already handled it. If it had issues, the user will ask for a re-run manually.

## Output
- Tasks created or drafts composed → list tasks with short summary
- Tasks completed (fulfilled in meetings) → list with ✅
- **Always name the specific meetings** processed (e.g. "from Fyxer call, Braintrust weekly, HGP Staff") — never say "from today's meetings"
- No meetings or no action items → NO_REPLY

## Cross-check with Grain (ACTIVE — transcript-level verification)
Grain MCP is available with full transcript access. After extracting action items from Granola:

1. **Find the meeting in Grain**: `mcporter call grain.list_attended_meetings --args '{}'`
   Note: Grain's schema does not support `start_date`/`end_date` filters. Call with empty args and filter the results manually by `start_datetime` to match today's date range.
2. **Fetch the transcript**: `mcporter call grain.fetch_meeting_transcript --args '{"meeting_id": "<grain_meeting_id>"}'`
3. **Cross-check each action item against the transcript**:
   - Is the action item actually assigned to you, or to the other person?
   - Are there commitments with timelines that Granola missed (e.g. "I'll get back in 2 days")?
   - Are there action items Granola dropped entirely?
4. **Prefer Grain's transcript** over Granola's summary when they conflict
5. Also use `grain.fetch_meeting_notes` for Grain's own AI-generated notes as a second opinion

If a Grain meeting can't be found (e.g. recording wasn't on), fall back to Granola only + skepticism rules.

#### Matching Grain to Granola meetings
Match by time overlap (within 15 min of start time), not by title. Grain and Granola may name the same meeting differently. If no Grain match found within the time window, proceed without cross-check.
