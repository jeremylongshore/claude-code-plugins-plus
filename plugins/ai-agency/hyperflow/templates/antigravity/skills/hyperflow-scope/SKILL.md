---
name: hyperflow-scope
description: Hyperflow planning phase. Use when a task is clear enough to decompose into batched steps before writing code — verbs like scope, decompose, "plan out", "break down", "plan this". Read-only with respect to source; writes a task file to .hyperflow/tasks/<slug>.md, then hands off to hyperflow-dispatch.
---

# hyperflow-scope — decomposition phase (Antigravity single-agent)

Decompose, don't build. The only writes are to `.hyperflow/`. Follow the `hyperflow` doctrine.

## Steps

1. **Research** the affected surface (files to read/modify/create, conventions, test patterns). If the request is actually a design question, redirect to `hyperflow-spec` and stop.
2. **Produce a batch graph.** Order batches topologically; each sub-task = one coherent change nameable in a single conventional-commit subject. **Split any sub-task** that touches >5 files, >500 LOC, spans 2+ subsystems, or would take a reviewer >10 min to grasp.
3. **Write `.hyperflow/tasks/<slug>.md`** with: status table (progress, branch, commit cadence) → Goal → Why → Scope-at-a-glance table → Affected files (created/modified) → Execution plan (batch graph) → Batches (each sub-task with role, files, complexity, acceptance criteria, commit-message stub) → Verification plan.
4. **Print** a one-line summary: `Plan ready — .hyperflow/tasks/<slug>.md (N batches, M sub-tasks)`.
5. **Hand off**: invoke the `hyperflow-dispatch` skill with the task slug.

## Rules

- No implementation code; no source edits.
- Single-batch plans for multi-file work are an anti-pattern — decompose.
- Always include a concrete verification plan.
