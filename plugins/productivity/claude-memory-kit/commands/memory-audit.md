---
name: memory-audit
description: Review and prune stale entries from MEMORY.md
---

Audit MEMORY.md and prune stale entries.

1. Read MEMORY.md — if missing, say "No MEMORY.md to audit."
2. Review each entry:
   - Completed tasks → mark done or remove
   - Outdated decisions → flag for review
   - Resolved questions → remove
   - Patterns still relevant → keep
3. Present summary: "N entries reviewed. X stale, Y kept, Z removed."
4. Ask for confirmation before writing changes
5. Rewrite MEMORY.md with only current entries
6. Add audit timestamp at the top: `last_audited: [ISO timestamp]`
