---
name: memory-kit
description: |
  Persistent context management for Claude Code sessions. Save, load, update,
  share, and audit session memory via MEMORY.md. Use when starting a session,
  before compaction, or to sync context across teammates.
allowed-tools: Read, Write, Edit, Bash(git:*)
version: 1.0.0
author: Claude Code Plugins Contributors
license: MIT
---

# Memory Kit Skills

Five skills for persistent context management in Claude Code.

---

## memory-save

Save current session context to MEMORY.md before compaction or session end.

**Steps:**
1. Read tasks/current-task.md if it exists
2. Collect: active goals, decisions made this session, patterns discovered, open questions, next steps
3. Write to MEMORY.md in this format:

```
## Memory Snapshot
saved: {ISO timestamp}
session_goal: {what you were working on}

### Active Tasks
- {task 1}
- {task 2}

### Decisions Made
- {decision and brief rationale}

### Patterns Discovered
- {pattern: what it means}

### Next Steps
- {concrete next action}

### Open Questions
- {unresolved question}
```

4. Confirm: "Memory saved to MEMORY.md. {N} items captured."

---

## memory-load

Restore context from MEMORY.md at session start.

**Steps:**
1. Check if MEMORY.md exists. If not, say "No memory file found. Starting fresh."
2. Read MEMORY.md
3. Summarize what was saved: goal, key decisions, next steps
4. Say: "Memory loaded from {timestamp}. Continuing: {session_goal}. Next step: {first next step}."
5. Ask if the user wants to resume or start something new

---

## memory-update

Log a decision or pattern mid-session without a full save.

**Steps:**
1. Ask what to log if not specified: decision, pattern, or note
2. Append to MEMORY.md under the relevant section (create section if missing)
3. Add a timestamp to the entry
4. Confirm: "Logged to MEMORY.md: {brief description}"

---

## memory-share

Sync MEMORY.md to git so teammates or other Claude instances can use it.

**Steps:**
1. Check git status — confirm MEMORY.md exists and has changes
2. Stage: `git add MEMORY.md`
3. Commit: `git commit -m "chore: update session memory [{timestamp}]"`
4. Push: `git push`
5. Confirm: "Memory synced to {branch}. Teammates can run /memory-load to restore context."
6. If push fails, report the error and suggest resolving manually

---

## memory-audit

Review and prune stale entries from MEMORY.md.

**Steps:**
1. Read MEMORY.md
2. Check each entry:
   - Completed tasks: mark done or remove
   - Outdated decisions: flag for review
   - Resolved questions: remove
   - Patterns still relevant: keep
3. Present a summary: "{N} entries reviewed. {X} stale, {Y} kept, {Z} removed."
4. Ask for confirmation before writing changes
5. Rewrite MEMORY.md with only current entries
6. Add audit timestamp: `last_audited: {ISO timestamp}`
