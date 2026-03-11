---
name: memory
description: |
  Execute extract and use project memories from previous sessions for context-aware assistance.
  Use when recalling past decisions, checking project conventions, or understanding user preferences.
  Trigger with phrases like "remember when", "like before", or "what was our decision about".
  
allowed-tools: Read, Write
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Memory

## Overview

Memory provides persistent context across Claude Code sessions by storing and retrieving project decisions, user preferences, and coding conventions from a local JSON file. When a new session starts, stored memories load automatically so previously established patterns carry forward without re-explanation. Developers working on long-running projects use this skill to maintain consistency across context window boundaries.

## Prerequisites

- Project memory file at `.claude/memories/project_memory.json` (created automatically on first memory save)
- Read and Write permissions for the `.claude/memories/` directory
- Claude Never Forgets plugin installed (`/plugin install yldrmahmet/claude-never-forgets`)

## Instructions

1. **Access stored memories.** On session start, locate and read the memory file at `.claude/memories/project_memory.json` using the Read tool. Parse the JSON structure containing timestamped memory entries. See `{baseDir}/references/implementation.md` for the full retrieval workflow.
2. **Match memories to current context.** Scan memory entries for keywords and topics relevant to the current task. Extract applicable decisions (e.g., "use pnpm instead of npm"), architectural patterns, library choices, and coding style preferences.
3. **Apply memories silently.** Incorporate remembered preferences into responses and tool usage without announcing them. When a memory dictates a package manager, testing framework, or naming convention, follow it automatically.
4. **Store new memories.** When significant decisions occur -- library selections, architectural choices, user-stated preferences, or tool rejections -- write them to the memory file with a timestamp. Add entries via the `/remember` command or through automatic capture of conversation signals.
5. **Resolve conflicts.** When a stored memory contradicts a current explicit request, prioritize the current request. Flag the conflict if appropriate and update the memory entry to reflect the new decision. Remove outdated memories that no longer apply.
6. **Handle cleanup.** When memory entries exceed 10, consolidate by removing noise (greetings, acknowledgments) and preserving high-value entries (preferences, decisions, corrections). The cleanup threshold is configurable in `hooks/stop_cleanup.py`.

## Output

- Automatic loading of stored memories at session start
- Silent application of remembered preferences to tool usage and responses
- New memory entries written with timestamps for significant decisions
- Consolidated memory file after cleanup (preserves important entries, removes noise)
- Explicit memory listing via `/memories` command

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Memory file not found | First session or file deleted | Initialize a new memory file at `.claude/memories/project_memory.json` with an empty JSON structure |
| Conflicting memories | Multiple entries contradict each other | Apply the most recent memory; suggest cleanup via `/forget` to remove outdated entries |
| Invalid memory format | File corrupted or manually edited with syntax errors | Back up the existing file, recreate with valid JSON structure, restore recoverable entries |
| Permission denied | File or directory lacks read/write permissions | Check file permissions on `.claude/memories/`; request necessary access or use an alternative storage location |

## Examples

**Automatic preference recall across sessions:**
```
Session 1:
User: "Always use Vitest instead of Jest for this project"
→ Stored to project_memory.json

Session 2:
User: "Add tests for the auth module"
→ Memory loaded: "use Vitest instead of Jest"
→ Test files created with Vitest syntax automatically
```

**Manual memory management:**
```bash
/remember "This project uses Tailwind CSS v4 with the Vite plugin"
/remember "Deploy to Cloudflare Workers, not Vercel"
/memories          # Lists all stored memories with timestamps
/forget "Vercel"   # Removes the Vercel-related memory
```

**Tool rejection captured as correction:**
```
User declines a suggested `npm install` action
→ Memory stored: "User prefers pnpm over npm"
→ Future sessions use pnpm automatically
```

## Resources

- `{baseDir}/references/implementation.md` -- Step-by-step guide for accessing, applying, updating, and resolving memory conflicts
- `{baseDir}/references/errors.md` -- Detailed error scenarios with recovery procedures
- `/remember [text]` -- Add a new memory entry manually
- `/forget [text]` -- Remove a matching memory from storage
- `/memories` -- Display all currently stored memories with timestamps
