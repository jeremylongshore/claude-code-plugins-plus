---
name: hyperflow-cache
description: Hyperflow memory manager. Use to view, search, add, edit, prune, or clear hyperflow project memory — "show memory", "search memory for X", "clear memory", "what does hyperflow remember about Y". CRUD over .hyperflow/memory/ only — never touches source code.
---

# hyperflow-cache — memory CRUD (Antigravity single-agent)

Manage `.hyperflow/memory/` entries. **Only memory files** — never source code. Follow the `hyperflow` doctrine.

## Operations

- **view / list** — print the entries in `.hyperflow/memory/{decisions,learnings,pitfalls,patterns}.md`.
- **search `<term>`** — grep the memory files; show matching entries with their file + heading.
- **add** — append a tagged entry to the right category file (decisions / learnings / pitfalls / patterns). Use the format: `## <topic>` then `- <fact> (recorded <YYYY-MM-DD>)`.
- **edit `<entry>`** — update an existing entry in place (don't duplicate).
- **prune / clear** — remove stale or wrong entries. Confirm via AskUserQuestion before a destructive clear (binary Yes/No).

## Rules

- Scope is `.hyperflow/memory/` only. Don't record what the repo/git already captures; record the non-obvious why.
