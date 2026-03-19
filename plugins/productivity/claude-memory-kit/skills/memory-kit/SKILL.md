---
name: memory-kit
description: |
  Persistent context management for Claude Code sessions. Save, load, update,
  share, and audit session memory via MEMORY.md. Prevents context loss on
  compaction or session restart. Use when starting a session, before compaction,
  syncing context across teammates, or pruning stale memory entries.
  Trigger with "save memory", "load memory", "memory audit", "memory share".
allowed-tools: Read, Write, Edit, Bash(git:*)
version: 1.0.0
author: builtbyzac
license: MIT
---

# Memory Kit

## Overview

Claude Code sessions lose context on compaction and restart. Memory Kit persists
session state (goals, decisions, patterns, open questions) to a `MEMORY.md` file
that survives across sessions. Five operations cover the full lifecycle: save,
load, update, share, and audit.

## Prerequisites

- A git repository (for memory-share)
- Write access to the project root (MEMORY.md lives there)

## Instructions

### 1. memory-save

Save current session context to MEMORY.md before compaction or session end.

1. Read `tasks/current-task.md` if it exists
2. Collect: active goals, decisions made this session, patterns discovered, open questions, next steps
3. Write to MEMORY.md using the output format below
4. Confirm: "Memory saved to MEMORY.md. N items captured."

### 2. memory-load

Restore context from MEMORY.md at session start.

1. Check if MEMORY.md exists — if not, say "No memory file found. Starting fresh."
2. Read MEMORY.md
3. Summarize: goal, key decisions, next steps
4. Report: "Memory loaded from [timestamp]. Continuing: [goal]. Next step: [first action]."
5. Ask if the user wants to resume or start something new

### 3. memory-update

Log a decision or pattern mid-session without a full save.

1. Ask what to log if not specified: decision, pattern, or note
2. Append to MEMORY.md under the relevant section (create section if missing)
3. Add a timestamp to the entry
4. Confirm: "Logged to MEMORY.md: [brief description]"

### 4. memory-share

Sync MEMORY.md to git so teammates or other Claude instances can use it.

1. Check git status — confirm MEMORY.md exists and has changes
2. Stage: `git add MEMORY.md`
3. Commit: `git commit -m "chore: update session memory [timestamp]"`
4. Push: `git push`
5. Confirm: "Memory synced to [branch]. Teammates can run /memory-load to restore context."
6. If push fails, report the error and suggest resolving manually

### 5. memory-audit

Review and prune stale entries from MEMORY.md.

1. Read MEMORY.md
2. Check each entry:
   - Completed tasks: mark done or remove
   - Outdated decisions: flag for review
   - Resolved questions: remove
   - Patterns still relevant: keep
3. Present a summary: "N entries reviewed. X stale, Y kept, Z removed."
4. Ask for confirmation before writing changes
5. Rewrite MEMORY.md with only current entries
6. Add audit timestamp at the top

## Output

memory-save writes MEMORY.md in this format:

```markdown
## Memory Snapshot
saved: 2026-03-19T14:30:00Z
session_goal: Implementing auth middleware

### Active Tasks
- Refactor token validation
- Add rate limiting to /api/login

### Decisions Made
- Use JWT with 15min expiry (balances security vs UX)

### Patterns Discovered
- Auth tests require test DB seeded with fixtures

### Next Steps
- Write integration tests for token refresh

### Open Questions
- Should refresh tokens rotate on each use?
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| MEMORY.md missing on load | "No memory file found. Starting fresh." |
| MEMORY.md missing on update | Create the file with proper structure first |
| Git push fails on share | Report the error, suggest manual resolution |
| No changes on audit | "All entries current. Nothing to prune." |
| Empty MEMORY.md | Treat as fresh — no entries to load or audit |

## Examples

**Save before compaction:**
> "Save my memory" → reads current context, writes snapshot to MEMORY.md

**Load at session start:**
> "Load memory" → reads MEMORY.md, summarizes state, asks to resume or start new

**Quick mid-session log:**
> "Log decision: using Postgres over SQLite for concurrent writes" → appends to Decisions section

**Team sync:**
> "Share memory" → commits and pushes MEMORY.md to current branch

**Weekly cleanup:**
> "Audit memory" → reviews entries, flags 3 stale items, asks before pruning
