---
name: status
description: |
  Use when the user wants a one-screen view of current hyperflow project state — version, profile freshness, memory count, and live progress on every in-flight task. Read-only; never modifies state, never dispatches workers.
  Trigger with /hyperflow:status, "what is hyperflow doing", "show task progress", "where are we".
allowed-tools: Read, Bash(git:*), Bash(ls:*), Bash(stat:*), Bash(date:*), Glob, Grep
argument-hint: ""
version: 3.1.2
license: MIT
compatibility: Designed for Claude Code
tags: [introspection, read-only, project-state]
---

# Status

Read-only snapshot of the current hyperflow project, with live progress on every active task file. Standalone — does not auto-chain and is never invoked by other skills. Invoked manually via `/hyperflow:status`.

The skill has two sections:

1. **Static snapshot** — version, profile freshness, memory count
2. **In-flight work** — per-task live progress (sub-tasks done/total, tokens, wall-clock, ETA)

## What to read

### Static snapshot

| Field | Source | Fallback |
|-------|--------|----------|
| Version | Latest git tag matching `v*` + tag commit date | `(missing)` |
| Profile | `.hyperflow/profile.md` file modification time | `(missing)` |
| Memory | Line count of `.hyperflow/memory/index.md` minus header rows | `(none)` |
| Active tasks | Files matching `.hyperflow/tasks/*.md` | `(none)` |

### In-flight work (per task file)

For every `.hyperflow/tasks/*.md`, parse its `## Status` block (written by `/hyperflow:scope` at creation and updated by `/hyperflow:dispatch` after each sub-task PASS — see scope/SKILL.md Step 4):

| Field | Source | Behaviour |
|-------|--------|----------|
| Slug | basename of the task file minus `.md` | always present |
| Done / total | `Sub-tasks: <done> / <total>` from Status block | falls back to counting `[x]` vs `[x]`+`[ ]` checkboxes if Status missing |
| Done sub-task names | lines with `[x]` from the `## Batches` section | listed under the bar |
| Running sub-task | the first `[~]` checkbox (dispatch marks `~` while a sub-task is mid-flight) | `(idle)` if none |
| Pending sub-task count | count of `[ ]` checkboxes | shown as `N pending` |
| Tokens used | `Tokens used:` line from Status block | `(not tracked yet)` if Status absent |
| Wall-clock | `Wall-clock:` line from Status block | `(not started)` if no `Started:` |
| ETA | `ETA:` line from Status block | `(computing)` if <3 sub-tasks done |

## How to compute each field

### Version

```bash
tag=$(git tag --sort=-v:refname | grep -E '^v[0-9]' | head -1)
released=$(git log -1 --format=%ci "$tag" 2>/dev/null | cut -d' ' -f1)
```

If `$tag` is empty → print `(missing)`.

### Profile freshness

```bash
profile=".hyperflow/profile.md"
now=$(date +%s)
mtime=$(stat -f %m "$profile" 2>/dev/null || stat -c %Y "$profile" 2>/dev/null)
hours=$(( (now - mtime) / 3600 ))
```

- File absent → `(missing)`
- `hours <= 24` → `fresh   (analyzed Xh ago)`
- `hours > 24`  → `stale   (analyzed Xh ago)`

### Memory entry count

Count table-body rows in `.hyperflow/memory/index.md` (lines starting with `|`, minus header + separator):

```bash
count=$(grep -c '^|' .hyperflow/memory/index.md 2>/dev/null)
entries=$(( count - 2 ))
```

If file absent or count ≤ 0 → `(none)`.

### Active tasks list

```bash
tasks=$(ls .hyperflow/tasks/*.md 2>/dev/null)
```

If no files → show `(none)` and skip the In-flight section entirely.

### Per-task Status parsing

For each `.hyperflow/tasks/<slug>.md`:

```bash
# Extract Status block fields
sub_done=$(grep '^Sub-tasks:' "$file" | sed -E 's|.*: *([0-9]+) */ *([0-9]+).*|\1|')
sub_total=$(grep '^Sub-tasks:' "$file" | sed -E 's|.*: *([0-9]+) */ *([0-9]+).*|\2|')
tokens=$(grep '^Tokens used:' "$file" | sed 's|^Tokens used: *||')
wall=$(grep '^Wall-clock:' "$file" | sed 's|^Wall-clock: *||')
eta=$(grep '^ETA:' "$file" | sed 's|^ETA: *||')
started=$(grep '^Started:' "$file" | sed 's|^Started: *||')
```

If the Status block is missing or malformed (old-style task file from before this format), fall back to counting checkboxes directly:

```bash
done=$(grep -c '^- \[x\]' "$file" 2>/dev/null)
running=$(grep -c '^- \[~\]' "$file" 2>/dev/null)
pending=$(grep -c '^- \[ \]' "$file" 2>/dev/null)
total=$(( done + running + pending ))
```

### Done sub-task names (for the indented list)

```bash
grep '^- \[x\]' "$file" | sed -E 's|^- \[x\] *||' | head -5
```

Show up to the **last 3 completed** + the **currently running** sub-task. If there are more than 3 done, prefix the list with `… (N earlier done)`.

### Running sub-task

The dispatch skill marks the in-flight sub-task with `[~]` while the worker is running. After PASS + commit, dispatch flips `[~]` → `[x]`.

```bash
running=$(grep '^- \[~\]' "$file" | sed -E 's|^- \[~\] *||' | head -1)
```

If no `[~]` line exists → the dispatch is either between sub-tasks (idle for milliseconds) or has handed control back. Show `(idle — last update Xm Ys ago)` based on `Last update:` timestamp.

### Progress bar

20-char ASCII bar based on `done / total`:

```
[████████████░░░░░░░░] 12/20  60%
```

Use `█` (filled) and `░` (empty). No emoji or color icons.

## Output format

Print the block below verbatim. If no in-flight tasks, omit the `── In-flight work ──` section.

```
── Hyperflow Status ─────────────────────────────────────────
Version       v3.0.0     (released 2026-05-16)
Profile       fresh      (analyzed 2h ago)
Memory        12 entries
Active tasks  2

── In-flight work ───────────────────────────────────────────
Task:         implement-auth
  Progress    [███████████░░░░░░░░░] 8/14  57%
  Last done   T7: Reset email worker
  Running     T8: Login UI (Implementer · 14s elapsed)
  Pending     6 sub-tasks
  Tokens      thinking 89.2k · worker 142.0k · total 231.2k
  Wall-clock  4m 22s elapsed
  ETA         ~3m 16s remaining   (avg 32s/sub-task · 6 left)

Task:         fix-login-bug
  Progress    [░░░░░░░░░░░░░░░░░░░░] 0/3   0%
  Status      not started (created 8m ago, no dispatch run yet)
─────────────────────────────────────────────────────────────
```

When Profile is `(missing)`, omit the `(analyzed Xh ago)` parenthetical.

When Version is `(missing)`, print `Version       (missing)`.

When no `.hyperflow/tasks/*.md` files exist, omit the `── In-flight work ──` section entirely; the snapshot block stands alone.

## ETA computation

```
elapsed_seconds       = now - started_unix
avg_per_subtask       = elapsed_seconds / done
remaining_seconds     = avg_per_subtask * pending
```

Format as `Xm Ys` or `Hh Mm` (skip zero leading units). Show `(computing)` when `done < 3` — too few data points for a useful average.

If the task has multiple batches and the next batch is `sequential` per the planner output, multiply remaining by `1.1` to account for inter-batch synchronisation overhead.

## Failure modes

Every section degrades gracefully:

- Missing git tags → `Version  (missing)`
- Missing `.hyperflow/profile.md` → `Profile  (missing)`
- Missing `.hyperflow/memory/index.md` → `Memory  (none)`
- No `.hyperflow/tasks/*.md` files → `Active tasks  (none)`, no In-flight section
- Task file present but Status block malformed/missing → fall back to checkbox count, show `(not tracked yet)` for tokens/ETA
- `Started:` line absent → `Status  not started`, skip ETA

Never error out. Never modify any file. Never dispatch an agent.

## Doctrine

This skill has no Worker/Reviewer dispatch — it is a pure read. It does not count as a hyperflow run and does not append to memory. Output style follows [output-style.md](references/output-style.md) — no decorative icons, em-dash separators, plain status words.

## Overview

`/hyperflow:status` prints a one-screen snapshot of the project's hyperflow state plus a live progress block for every in-flight task. Useful when picking up a session mid-flight, deciding whether to invoke `/hyperflow:dispatch`, or auditing whether a chain run is still healthy. Pure read — no agents, no writes, no chain side-effects.

## Prerequisites

- Git repository (for the version line — degrades to `(missing)` otherwise).
- `.hyperflow/` directory (for profile/memory/tasks lines — each section degrades to `(missing)` or `(none)` if absent).
- No prerequisites for invocation itself — runs anywhere.

## Instructions

See [What to read](#what-to-read) and [How to compute each field](#how-to-compute-each-field) above for the full operational spec. Summary:

1. Read version from latest git tag matching `v*`.
2. Stat `.hyperflow/profile.md` for freshness; bucket into fresh/stale/missing.
3. Count entries in `.hyperflow/memory/index.md`.
4. Glob `.hyperflow/tasks/*.md` and parse each Status block for live progress.
5. Render the static snapshot block; render the In-flight block per task (if any).
6. Stop. No prompts, no follow-ups.

## Output

See [Output format](#output-format) above for the exact block. Two sections — static snapshot and (if there are active tasks) In-flight work with per-task progress bar, last-done sub-task, currently-running sub-task, pending count, tokens, wall-clock, ETA.

## Error Handling

| Failure | Behavior |
|---|---|
| Not a git repo | `Version  (missing)`; everything else still renders if `.hyperflow/` exists. |
| `.hyperflow/profile.md` missing | `Profile  (missing)` (no parenthetical). |
| `.hyperflow/memory/index.md` missing | `Memory  (none)`. |
| No task files | Omit the In-flight section entirely; just print the snapshot. |
| Task file with malformed Status block | Fall back to counting `[x]` vs `[ ]` checkboxes; show `(not tracked yet)` for tokens/ETA. |
| `stat` flag differs between BSD (macOS) and GNU (Linux) | Try `stat -f %m` then fall back to `stat -c %Y`. |

Never errors out. Never modifies any file. Never dispatches an agent.

## Examples

### Healthy project, no active tasks

```
── Hyperflow Status ─────────────────────────────────────────
Version       v3.1.2     (released 2026-05-16)
Profile       fresh      (analyzed 2h ago)
Memory        12 entries
Active tasks  (none)
─────────────────────────────────────────────────────────────
```

### Mid-dispatch with two active tasks

```
── Hyperflow Status ─────────────────────────────────────────
Version       v3.1.2     (released 2026-05-16)
Profile       fresh      (analyzed 2h ago)
Memory        12 entries
Active tasks  2

── In-flight work ───────────────────────────────────────────
Task:         implement-auth
  Progress    [███████████░░░░░░░░░] 8/14  57%
  Last done   T7: Reset email worker
  Running     T8: Login UI (Implementer · 14s elapsed)
  Pending     6 sub-tasks
  Tokens      thinking 89.2k · worker 142.0k · total 231.2k
  Wall-clock  4m 22s elapsed
  ETA         ~3m 16s remaining   (avg 32s/sub-task · 6 left)

Task:         fix-login-bug
  Progress    [░░░░░░░░░░░░░░░░░░░░] 0/3   0%
  Status      not started (created 8m ago, no dispatch run yet)
─────────────────────────────────────────────────────────────
```

### Brand new install (no .hyperflow/ yet)

```
── Hyperflow Status ─────────────────────────────────────────
Version       v3.1.2     (released 2026-05-16)
Profile       (missing)
Memory        (none)
Active tasks  (none)
─────────────────────────────────────────────────────────────
```

## Resources

- [output-style.md](references/output-style.md) — em-dash style, no decorative chars, plain status words.
- [DOCTRINE.md](references/DOCTRINE.md) — orchestration rules (status is exempt from per-step agent dispatch).
