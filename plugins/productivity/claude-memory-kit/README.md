# Claude Memory Kit

A set of 5 Claude Code skills for context management across resets and sessions.

## Overview

The Memory Kit gives Claude Code persistent memory. Instead of losing context on every reset or compaction, you can save, restore, update, share, and audit session memory using a structured MEMORY.md file.

Sold at https://builtbyzac.com/memory-kit.html for $19.

## Skills

### memory-save

Saves current session context to a MEMORY.md file before compaction. Captures active tasks, decisions made, patterns discovered, and next steps.

### memory-load

Restores context from MEMORY.md at session start. Reads the file and primes Claude with the saved state so work continues without re-explanation.

### memory-update

Logs decisions and patterns mid-session. Appends structured entries to MEMORY.md so nothing important gets lost between major saves.

### memory-share

Syncs memory to git for team use. Commits MEMORY.md so teammates and other Claude instances can pick up where you left off.

### memory-audit

Audits and prunes stale memory entries. Reviews MEMORY.md for outdated decisions, completed tasks, and obsolete context, then cleans it up.

## Usage

Place the skills in your `.claude/skills/memory-kit/` directory and invoke them by name:

- `/memory-save` — before any compaction or end of session
- `/memory-load` — at the start of a new session
- `/memory-update` — after a key decision or discovery
- `/memory-share` — to push memory to git for team access
- `/memory-audit` — weekly or when MEMORY.md grows large

## License

MIT
