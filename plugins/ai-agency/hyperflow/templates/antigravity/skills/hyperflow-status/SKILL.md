---
name: hyperflow-status
description: Hyperflow project status. Use to see current hyperflow state — "what is hyperflow doing", "show task progress", "where are we". Read-only — reports in-flight tasks, memory count, and progress. Never modifies state or runs work.
---

# hyperflow-status — read-only state (Antigravity single-agent)

One-screen view of hyperflow project state. **Read-only** — never edits files or runs work. Follow the `hyperflow` doctrine.

## Steps

1. Read `.hyperflow/tasks/*.md`; for each, report the status block (progress bar, sub-tasks done/total, branch).
2. Count `.hyperflow/specs/*.md` and `.hyperflow/audits/*.md`.
3. Count `.hyperflow/memory/*` entries.
4. Print a compact summary: active tasks + their progress, spec/audit counts, memory size. If `.hyperflow/` is absent, say so and suggest `hyperflow-scaffold`.

## Rules

- Never modify any file. Never dispatch work. Output is a single status block.
