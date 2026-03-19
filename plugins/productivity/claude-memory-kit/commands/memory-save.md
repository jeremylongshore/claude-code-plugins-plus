---
name: memory-save
description: Save current session context to MEMORY.md before compaction or session end
---

Save the current session context to MEMORY.md.

1. Read `tasks/current-task.md` if it exists
2. Collect from the current session:
   - Active goals and tasks
   - Decisions made (with rationale)
   - Patterns discovered
   - Open questions
   - Concrete next steps
3. Write to MEMORY.md using the template from the memory-kit skill's `references/output-format.md`
4. Confirm: "Memory saved to MEMORY.md. N items captured."

If MEMORY.md already exists, overwrite it with the fresh snapshot.
