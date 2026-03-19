---
name: memory-load
description: Restore context from MEMORY.md at session start
---

Restore session context from MEMORY.md.

1. Check if MEMORY.md exists — if not, say "No memory file found. Starting fresh."
2. Read MEMORY.md
3. Summarize what was saved: session goal, key decisions, next steps
4. Report: "Memory loaded from [timestamp]. Continuing: [goal]. Next step: [first action]."
5. Ask if the user wants to resume the saved work or start something new
