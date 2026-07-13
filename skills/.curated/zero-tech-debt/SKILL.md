---
name: zero-tech-debt
description: |
  Rebuild a feature as if the correct product architecture existed from day one — remove compatibility cruft, dead abstractions, and historical compromises instead of preserving them. Use when the operator says "refactor properly," "clean up," "rewrite," "modernize," "remove legacy," "simplify," "rethink," "pay down tech debt," or signals frustration with accumulated complexity. Do NOT use for hotfixes, bug repros, surgical patches, or security backports — blast-radius minimization wins there. Trigger with "/zero-tech-debt", "do it right this time", "the way it should have been built", "refactor toward intent".
allowed-tools: Read, Edit, Glob, Grep, Bash(git:*), Bash(rg:*), Bash(fd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code
tags: [refactoring, tech-debt, architecture, cleanup, modernization, code-quality]
user-invocable: true
---

# Zero Tech Debt

Build toward the intended product shape — not the historical sequence of patches, migrations, wrappers, aliases, and temporary decisions that created the current implementation.

The goal is not "minimal diff."
The goal is a cleaner, more coherent system with fewer moving parts, fewer hidden assumptions, and lower long-term operational cost.

## Core Principle

Treat the current implementation as evidence, not authority.

Preserve only the parts that still serve the intended architecture, UX, reliability model, and operational constraints. Everything else is eligible for deletion.

## Operating Mode (read this section every invocation)

1. **Confirm scope** — `Read` [`references/01-when-to-use.md`](references/01-when-to-use.md). If the request smells like a hotfix, security backport, or time-boxed patch, stop and recommend a targeted change instead.
2. **Pre-flight** — walk [`references/02-preflight-checklist.md`](references/02-preflight-checklist.md). Every box must be checked before touching code. Tests, callers, rollback path, single-paragraph end-state description, no in-flight migration, telemetry accounted for. Use `Glob` to locate test files and `Grep` / `Bash(rg:*)` to enumerate external callers of the surface being changed.
3. **Run the 7-step workflow** — [`references/03-workflow.md`](references/03-workflow.md). Define end state → audit reality → delete before adding → optimize around final shape → collapse duplicate decision logic → remove historical leakage → validate.
4. **Use the audit patterns** — [`references/04-audit-patterns.md`](references/04-audit-patterns.md) lists the concrete `Grep` / `Bash(rg:*)` / `Bash(fd:*)` targets (TODO/DEPRECATED markers, `_v2`/`_old` suffixes, stale feature flags, dual-mode forks, etc.). Each match is a *candidate*, not an automatic deletion.
5. **Apply decision filters when choices tie** — [`references/05-decision-filters.md`](references/05-decision-filters.md) covers tiebreakers and named anti-patterns to avoid.
6. **Apply edits with `Edit`** — once a deletion / rename / consolidation is approved, use `Edit` to apply the change atomically. Stage with `Bash(git:*)` so the operator can review per commit before push.
7. **Report back in shape-change terms** — [`references/06-outcomes-and-reporting.md`](references/06-outcomes-and-reporting.md). The diff lists every line; the summary makes the architectural delta legible.

## Scope Discipline (this is the most common failure mode)

A zero-tech-debt refactor will tempt unbounded scope. Hold the line:

- **One coherent end state per refactor** — not three loosely related ones
- If deletion reveals deeper rot, document it and stop; do not chain refactors mid-flight
- Resist "while I'm here" additions unrelated to the deletion path
- New features wait for a separate change
- If the work cannot fit in a single reviewable unit, split along ownership boundaries — never along file counts

## Final Rule

Do not optimize for preserving the past.

Optimize for making the next 2 years of development simpler.

---

See [`references/`](references/) for the full methodology — each file is a single concern, loadable on demand.
