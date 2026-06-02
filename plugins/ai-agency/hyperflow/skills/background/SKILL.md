---
name: background
description: |
  Use when the user wants to see, inspect, cancel, or prune background agents fired during prior chain runs. Read/manage `.hyperflow/background/registry.json` and the per-agent output buffers at `.hyperflow/background/<id>.md`. Standalone — never auto-invoked.
  Trigger with /hyperflow:background, "list background agents", "what's running in background", "cancel background agent", "show background result".
allowed-tools: Read, Write, Edit, Bash(ls:*), Bash(cat:*), Bash(rm:*), Bash(find:*), Glob, Grep
argument-hint: "<list|show|cancel|prune> [id|--all]"
version: 4.7.0
license: MIT
compatibility: Designed for Claude Code
tags: [background, orchestration, lifecycle]
---

# Background

Read-only-by-default management interface for background agents fired by other hyperflow skills (dispatch quality gates, deploy CI watcher, scaffold analysis refresh, cache compact, scope speculative prefetch). Reads from `.hyperflow/background/registry.json` + per-agent output buffers.

Full doctrine: [background-agents.md](../hyperflow/background-agents.md).

## Subcommands

| Subcommand | Description |
|---|---|
| `list` | Print the registry: in-flight · completed-uncollected · stalled · errored |
| `show <id>` | Print one agent's output buffer (`.hyperflow/background/<id>.md`) |
| `cancel <id>` | Cancel one specific in-flight agent |
| `cancel --all` | Cancel every in-flight agent (use before closing a session) |
| `prune` | Delete completed `.hyperflow/background/<id>.md` files older than 7 days |

Default subcommand when none provided: `list`.

## Subcommand Details

### `list`

Read `.hyperflow/background/registry.json`. Group entries by status and print a compact table:

```markdown
## In flight (N)

| ID                                | Purpose                              | Fired      | Timeout | Blocks  |
|-----------------------------------|--------------------------------------|------------|---------|---------|
| `bg-1718049600-quality-gates-b2`  | Layer 5 gates Batch 2                | 17:30      | 18:00   | step3   |
| `bg-1718049820-ci-watcher`        | GitHub Actions watch for v4.7.0      | 17:33      | 18:33   | —       |

## Completed (uncollected, N)

| ID                                | Purpose                              | Completed  | Duration | Output |
|-----------------------------------|--------------------------------------|------------|----------|--------|
| `bg-1718045400-scaffold-refresh`  | Refresh .hyperflow/architecture.md   | 16:42      | 2m 18s   | 1.4kb  |

## Stalled / Errored (N)

| ID                                | Purpose                              | Status            | Reason            |
|-----------------------------------|--------------------------------------|-------------------|-------------------|
| `bg-1717980000-cache-compact`     | Compact learnings.md                 | STALLED           | timeout (30m)     |
```

Print one trailing line: `<count> in flight · <count> uncollected · <count> needs attention`. If registry is empty, print `No background agents.` and stop.

### `show <id>`

Read `.hyperflow/background/<id>.md` and print it verbatim. If the agent is still running, print the registry entry first then `Output buffer not yet written.` and stop.

### `cancel <id>`

1. Read registry, find the entry.
2. If `status: running`, signal cancellation per the provider's mechanism (Claude Code: use the runtime's cancellation API for that subagent ID; if unavailable, mark the entry `status: cancelled` and leave the agent to time out on its own — the foreground orchestrator will drop the result on collection).
3. Update registry entry: `status: cancelled`, `cancelled_at: <now>`.
4. Print `Cancelled <id> — <purpose>`.

If the agent already completed, print `Agent <id> already <status> — nothing to cancel.`

### `cancel --all`

For every entry with `status: running`, run the `cancel` flow. Print summary: `Cancelled N agents.`

### `prune`

`find .hyperflow/background/ -name "bg-*.md" -mtime +7 -delete` plus remove their entries from `registry.json` (only entries with `status: complete | error | stalled | cancelled` older than 7 days are pruned). Print: `Pruned N output buffers · N registry entries`.

## Flow

1. Parse subcommand from invocation (default: `list`).
2. Read `.hyperflow/background/registry.json` (if absent, treat as empty).
3. Execute subcommand.
4. Print result.

## Overview

`/hyperflow:background` is the user-facing read/manage interface for background agents. The orchestrator itself maintains the registry as a side-effect of `run_in_background: true` Agent dispatches in other skills — this skill never *fires* a background agent, it only reads/manages the registry.

## Prerequisites

- `.hyperflow/background/registry.json` exists (created on first background dispatch by any other skill — if absent, all subcommands degrade gracefully).
- `.hyperflow/` initialized (run `/hyperflow:scaffold` if missing — though this skill works even without scaffold, since the registry is created on demand).

## Instructions

See [Subcommands](#subcommands) and [Subcommand Details](#subcommand-details). Summary:

1. Parse the subcommand (default `list` when none given).
2. Read the registry from `.hyperflow/background/registry.json`.
3. Execute the subcommand against the registry + per-agent output buffers.
4. Print compact result; do not modify any source code.

## Output

- `list` — table of in-flight / completed-uncollected / stalled+errored, with one trailing summary line.
- `show <id>` — file contents of `.hyperflow/background/<id>.md`.
- `cancel <id>` / `cancel --all` — one-line confirmation per cancelled agent + total.
- `prune` — count of pruned buffers + registry entries.

## Error Handling

| Failure | Behavior |
|---|---|
| Registry file missing | Treat as empty — `list` prints `No background agents.`; other subcommands print `No registry — fire a background agent first.` and stop. |
| Registry JSON malformed | Print `Registry malformed — back up to .hyperflow/background/registry.json.bak and re-create empty.` Move file, write empty registry, continue. |
| `show <id>` for unknown id | List 3 closest IDs by Levenshtein distance. |
| `cancel <id>` for already-completed agent | Print `Agent <id> already <status> — nothing to cancel.` |
| Provider cancellation API unavailable | Mark entry `status: cancelled` in registry; the foreground orchestrator drops the result on collection. Print `Marked <id> as cancelled (provider has no live cancellation API — agent will run to completion or timeout, but result will be discarded).` |
| Prune called with no eligible entries | Print `Nothing to prune — no completed buffers older than 7 days.` |

## Examples

### List in-flight + completed background agents

```
/hyperflow:background list

## In flight (1)
| ID                                | Purpose                              | Fired | Timeout | Blocks |
|-----------------------------------|--------------------------------------|-------|---------|--------|
| `bg-1718049600-quality-gates-b2`  | Layer 5 gates Batch 2                | 17:30 | 18:00   | step3  |

## Completed (uncollected, 1)
| ID                                | Purpose                              | Completed | Duration | Output |
|-----------------------------------|--------------------------------------|-----------|----------|--------|
| `bg-1718045400-scaffold-refresh`  | Refresh .hyperflow/architecture.md   | 16:42     | 2m 18s   | 1.4kb  |

1 in flight · 1 uncollected · 0 needs attention
```

### Show a completed agent's output

```
/hyperflow:background show bg-1718045400-scaffold-refresh

# Background Result — Refresh .hyperflow/architecture.md

| Field      | Value                                |
|------------|--------------------------------------|
| Agent ID   | `bg-1718045400-scaffold-refresh`     |
| Fired at   | 2026-05-16T16:40:00Z                 |
| Completed  | 2026-05-16T16:42:18Z (2m 18s)        |
| Status     | complete                             |
| Tokens     | worker 4.2k                          |

## Output
<refreshed architecture.md content fragments + diff summary>
```

### Cancel everything before closing the session

```
/hyperflow:background cancel --all

Cancelled bg-1718049600-quality-gates-b2 — Layer 5 gates Batch 2
Cancelled bg-1718049820-ci-watcher — GitHub Actions watch for v4.7.0
Cancelled 2 agents.
```

## Resources

- [background-agents.md](../hyperflow/background-agents.md) — full doctrine: when to use, hard rules, registry shape, failure modes, anti-patterns.
- [DOCTRINE.md](../hyperflow/DOCTRINE.md) — rule 8 (background extensions), rule 9 (no AI-attributed background commits).
- [output-style.md](../hyperflow/output-style.md) — table conventions for `list` output.
