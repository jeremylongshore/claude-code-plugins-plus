---
name: schedule-after-usage-reset
description: "Schedule a task to run after the Claude usage limit resets. Use when the user says things like: schedule this after my usage resets, run this when my tokens refresh, queue this task for after the limit lifts, or any variation of wanting to defer a task until after a Claude usage/token limit reset. Finds the reset time from the Anthropic usage API and calls /schedule with that exact time. Trigger with phrases like \"schedule after my usage resets\" or \"run this when my limit lifts\"."
allowed-tools: Bash(security:*), Bash(curl:*), Bash(python3:*), Bash(date:*)
version: "1.0.0"
author: patricksong1993 (https://github.com/patricksong1993)
license: MIT
compatibility: Designed for Claude Code
tags: [scheduling, rate-limit, automation, claude-code]
---

# Schedule After Usage Reset

Automatically find the usage reset time and call `/schedule` with it. No questions asked.

## Overview

When the user wants to defer a task until after their Claude usage/token limit
resets, this skill removes the manual step of looking up the reset time. It reads
the reset timestamp from the Anthropic usage API, converts it to the user's local
timezone, adds a small buffer, and hands the task off to the `/schedule` skill at
that exact time. The user never has to figure out *when* the limit lifts — they
just say what they want run.

## Prerequisites

- Running inside Claude Code with a valid OAuth credential stored under the
  `Claude Code-credentials` keychain entry (read via `/usr/bin/security`).
- Network access to `https://api.anthropic.com` to query the usage endpoint.
- `python3` available on `PATH` (used to parse the JSON token and API response).
- The `schedule` skill installed — this skill defers the actual scheduling to it.

## Instructions

### 1. Get the reset time

Fetch from the Anthropic usage API:

```bash
token_json=$(/usr/bin/security find-generic-password -s 'Claude Code-credentials' -w 2>/dev/null)
access_token=$(echo "$token_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('claudeAiOauth',{}).get('accessToken',''))")
curl -s -H "Authorization: Bearer $access_token" \
     -H "anthropic-beta: oauth-2025-04-20" \
     -H "User-Agent: claude-code/2.1" \
     "https://api.anthropic.com/api/oauth/usage"
```

Parse `five_hour.resets_at` (or `seven_day.resets_at`). Convert UTC → user's local
timezone. Add 5 minutes as buffer.

### 2. Get the task

If not provided as an argument, ask: "What should I run after the reset?"

### 3. Call /schedule

Invoke the `schedule` skill, passing the task and the reset time + 5min buffer:

```
/schedule "<task>" at <HH:MM> <timezone>
```

The `schedule` skill handles everything from there — just like calling it directly.

## Output

- A `/schedule` invocation has been created for the user's task at the reset time
  plus the 5-minute buffer, expressed in the user's local timezone.
- A short confirmation of what was queued and when it will run (for example:
  "Queued `<task>` to run at 14:35 America/New_York, just after your usage resets").
- The `/schedule` skill owns execution from that point — this skill's job ends once
  the handoff has been made.

## Error Handling

- **Rate limited (HTTP 429):** wait 15 seconds and retry the usage request once.
- **Still failing after the retry:** ask the user for the reset time directly and
  proceed with `/schedule` using their answer.
- **Missing or empty access token:** the keychain lookup returned nothing — ask the
  user for the reset time rather than guessing.

## Examples

**Defer a build until the limit lifts**

```
User: schedule a full test run for after my usage resets
→ Read five_hour.resets_at from the usage API (e.g. 19:30 UTC)
→ Convert to local time and add 5 min → 14:35 America/New_York
→ /schedule "run the full test suite" at 14:35 America/New_York
```

**Reset time unavailable**

```
User: queue this report for when my tokens refresh
→ Usage API still 429 after one retry
→ Ask: "What time does your usage reset?" → user says 3:00 PM
→ /schedule "<task>" at 15:05 <timezone>
```

## Resources

- Anthropic usage endpoint: `https://api.anthropic.com/api/oauth/usage`
  (`five_hour.resets_at` / `seven_day.resets_at` carry the reset timestamps).
- The `schedule` skill — this skill is a thin front-end that resolves the reset
  time and then defers all scheduling to it.
