---
name: memory-kit
description: |
  Persistent context management for Claude Code sessions. Save, load, update,
  share, and audit session memory via MEMORY.md. Prevents context loss on
  compaction or session restart. Use when starting a session, before compaction,
  syncing context across teammates, or pruning stale memory entries.
  Trigger with "save memory", "load memory", "memory audit", "memory share".
allowed-tools: Read, Write, Edit, Bash(git:*)
version: 1.1.0
author: builtbyzac
license: MIT
---

# Memory Kit

## Current State
!`[ -f MEMORY.md ] && echo "MEMORY.md: $(wc -l < MEMORY.md) lines, last modified $(date -r MEMORY.md '+%Y-%m-%d %H:%M')" || echo "No MEMORY.md found"`
!`[ -f tasks/current-task.md ] && echo "Active task file found" || echo "No task file"`

## Overview

Claude Code sessions lose context on compaction and restart. Memory Kit persists
session state (goals, decisions, patterns, open questions) to a `MEMORY.md` file
that survives across sessions.

Five commands cover the full lifecycle:
- `/memory-save` — snapshot before compaction
- `/memory-load` — restore at session start
- `/memory-update` — log a decision mid-session
- `/memory-share` — push to git for teammates
- `/memory-audit` — prune stale entries

## Prerequisites

- A git repository (for `/memory-share`)
- Write access to the project root (MEMORY.md lives there)

## Output Format

For the MEMORY.md template structure, see [output-format.md](references/output-format.md).

## Error Handling

For error scenarios and recovery behavior, see [error-handling.md](references/error-handling.md).

## Examples

**Save before compaction:**
> "Save my memory" → reads current context, writes snapshot to MEMORY.md

**Load at session start:**
> "Load memory" → reads MEMORY.md, summarizes state, asks to resume or start new

**Quick mid-session log:**
> "Log decision: using Postgres over SQLite for concurrent writes" → appends to Decisions section

**Team sync:**
> "Share memory" → runs `scripts/memory-share.sh`, confirms push
