---
name: beads-dolt
description: |
  Dolt and DoltHub-aware workflow for the beads (bd) task tracker. Diagnoses why
  bead work is not visible on DoltHub (no Dolt remote configured), applies the bd
  dolt remote add plus bd dolt push fix, explains the JSONL throttle and export
  model and the rapid-write-race safe pattern, and dispatches expert agents for
  sync, epic-closure audits, dependency mapping, and recovery. Use when beads are
  not showing in DoltHub, pushing beads to DoltHub, configuring bd dolt remotes,
  taming dolt server sprawl, auditing bead epics, mapping bead dependencies, or
  recovering from a bd or Dolt incident. Trigger with "/beads-dolt", "my beads
  aren't showing in DoltHub", "push beads to dolthub", or "audit my bead epics".
allowed-tools: "Read, Task, Bash(bd:*), Bash(dolt:*), Bash(curl:*)"
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: "Designed for Claude Code. Requires bd >= 1.0.4 with a Dolt-backed workspace; the dolt-mcp-server binary on PATH enables the SQL-capable agents."
argument-hint: "[diagnose|push|audit]"
tags: [beads, bd, dolt, dolthub, task-tracking, mcp, version-control]
metadata:
  category: productivity
---

# beads-dolt

The Dolt and DoltHub-aware layer for the [beads](https://github.com/gastownhall/beads) (bd) task tracker. It composes with — does not replace — the global beads skill: that skill runs the bead work cycle; this one handles the Dolt backend, DoltHub visibility, and the bd plus Dolt failure modes.

## Overview

bd stores every issue in a version-controlled [Dolt](https://github.com/dolthub/dolt) database. Two things bite teams repeatedly:

1. **"My beads aren't showing in DoltHub."** The overwhelmingly common cause is that the workspace's Dolt repo has **no remote configured** — so nothing is ever pushed. A file-protocol or GitHub backup does **not** make beads appear on DoltHub; only a Dolt remote plus a push does.
2. **JSONL appears stale after rapid writes.** This is the export *throttle*, not data loss. As of bd 1.0.4 the historical rapid-write race (failure mode 6) is fixed at the SQL-transaction level; the database is always correct, only the issues.jsonl file can lag.

This skill diagnoses both, applies the fixes, and routes deeper work to five bundled agents. **It keeps no frozen copy of bd/Dolt internals** — a baked snapshot goes stale the moment upstream ships a release. Verify version-specific behavior **live** (`bd --help`, `bd <cmd> --help`, `bd dolt show`) and consult the official upstream docs; [references/beads-dolt-internals.md](references/beads-dolt-internals.md) is only the directory of those authoritative sources. The installed binary wins on any conflict. The agents are built to fetch the current truth in their own context and report it back, so answers track the installed version rather than a guess.

**The fix for invisible-on-DoltHub, up front (don't stop at diagnosis):** the cause is almost always no remote, and the fix is two commands — `bd dolt remote add origin https://doltremoteapi.dolthub.com/ORG/REPO` then `bd dolt push --remote origin`. The DoltHub database must already exist (the push does NOT create it). Always carry the user all the way to these commands, not just the `bd dolt remote list` diagnostic.

## Prerequisites

- bd >= 1.0.4 with a Dolt-backed workspace (bd dolt show succeeds).
- For DoltHub: a dolt creds keypair authorized on your DoltHub account, and the **DoltHub database must already exist** (create it in the DoltHub UI — the push does **not** auto-create it).
- For the SQL-capable agents: the dolt-mcp-server binary on PATH (go install github.com/dolthub/dolt-mcp/mcp/cmd/dolt-mcp-server@latest). The plugin's .mcp.json wires it.

## Authentication

DoltHub pushes authenticate with a dolt creds keypair tied to your account (run dolt login once to create and authorize it), or with the DOLT_REMOTE_USER and DOLT_REMOTE_PASSWORD environment variables. The dolt-mcp connection uses DOLT_USER and DOLT_PASSWORD (bd's local server is unauthenticated by default — user root, empty password).

## Instructions

### Step 1: Diagnose visibility ("my beads aren't in DoltHub")

```bash
bd dolt show            # confirm the database name and server port
bd dolt remote list     # the smoking gun: "No remotes configured" means nothing is pushed
```

If no remote is configured, that is the root cause. Proceed to Step 2.

### Step 2: Configure the DoltHub remote and push

The DoltHub database must exist first (create it at dolthub.com, "Create Database"). Then:

```bash
# Use the bd wrapper (tracks the remote at the SQL layer and sets sync.remote for scheduled pushes)
bd dolt remote add origin https://doltremoteapi.dolthub.com/ORG/REPO
bd dolt push --remote origin
```

- The push is **history-preserving** — it transfers the full Dolt commit history, not a snapshot. (Flat-file dolt table import would lose history; do not use it for an existing bd database.)
- A PermissionDenied that reaches "Uploading…" first means **the creds work but the DoltHub repo doesn't exist yet** — create it, then re-push.
- Verify without cloning, via DoltHub's SQL API:

  ```bash
  curl -s "https://www.dolthub.com/api/v1alpha1/ORG/REPO/main?q=SELECT%20COUNT(*)%20FROM%20issues"
  ```

### Step 3: Keep it fresh (don't push per-command)

A per-command push is too slow. Schedule a push on the existing backup cadence (every 15–30 min, after bd export) rather than inline. See scripts/dolt-push-dolthub.sh.

### Step 4: Understand the JSONL throttle (not data loss)

export.interval defaults to **60s**: writes inside that window hit the database but not issues.jsonl until the next op after the window. For a gitignored .beads where a whole session fits in one window, set it to flush immediately:

```bash
bd config set export.interval 1s
```

As of recent bd the rapid-write race is reported fixed at the transaction level (verify with `bd version` + the upstream CHANGELOG) — so you do *not* need bd export between writes for database integrity; only batch plus flush if you need byte-fresh JSONL each step. Confirm current throttle/export behavior with `bd config --help` + `bd dolt --help`; [references/beads-dolt-internals.md](references/beads-dolt-internals.md) lists the authoritative sources.

### Step 5: Dispatch the right agent

Use the Task tool to dispatch the matching agent. Each fetches current bd/Dolt facts live in its own context (per the authority order in references/beads-dolt-internals.md) rather than reciting a snapshot.

| Situation | Agent |
|---|---|
| DoltHub remotes, push/pull, backup-vs-push, federation, drift, idle-server reaping | dolt-sync-advisor |
| "Which epics have all their children closed?" subtree/closure audit | bead-epic-auditor |
| Dependency graph, cycles, critical path (SQL via the Dolt MCP) | bead-dependency-mapper |
| Rapid-write-race recovery, embedded-to-server mode migration, dolt-server incident | bead-recovery-specialist |
| General bd expertise, three-layer mirror discipline, naming and hygiene | beads-guru |

The SQL-capable agents (bead-epic-auditor, bead-dependency-mapper) query the bead graph through the wired dolt MCP server (the query, list_databases, and list_dolt_commits tools).

## Output

- A clear root-cause statement for visibility issues (almost always "no remote configured").
- The exact bd dolt commands to fix it, plus a DoltHub-API verification one-liner.
- For audits and maps: the agent's structured result (e.g., a closure table or dependency graph), never raw IDs without context.

## Error Handling

| Symptom | Cause | Fix |
|---|---|---|
| Push gives PermissionDenied after "Uploading…" | DoltHub repo doesn't exist (creds are fine) | Create the database in the DoltHub UI, re-push |
| Push gives an auth error before uploading | Stale or absent dolt creds | dolt login (interactive), or set DOLT_REMOTE_USER and DOLT_REMOTE_PASSWORD |
| JSONL stale after a burst of writes | 60s export throttle | bd config set export.interval 1s, or flush with bd export |
| Many dolt sql-server processes pile up | Each workspace runs its own per-project server | Reap idle ones: scripts/dolt-idle-reaper.sh (bd respawns each on next use — non-destructive), cron it; or consolidate via shared-server mode (read `bd init --help` live for the current flags) |
| MCP server won't connect | Wrong port or database | bd dolt show for the live port and database; set DOLT_PORT and DOLT_DATABASE |

## Examples

**"My beads aren't showing up in DoltHub."**
Run bd dolt remote list; it shows "No remotes configured" — explain that is the root cause — bd dolt remote add origin https://doltremoteapi.dolthub.com/ORG/REPO (repo must pre-exist) — bd dolt push --remote origin — verify via the DoltHub SQL API.

**"Which of my epics have all their children closed?"**
Dispatch bead-epic-auditor; it queries the bead graph over the Dolt MCP and returns a closure table.

**"bd has 15 dolt servers running, it's a mess."**
Dispatch dolt-sync-advisor; it reaps idle servers with scripts/dolt-idle-reaper.sh (each respawns on its next bd command — non-destructive), or walks shared-server consolidation if you want one durable server — it reads `bd init --help` live for the current flags rather than assuming them.

## Resources

- [references/beads-dolt-internals.md](references/beads-dolt-internals.md) — the directory of authoritative *live* sources (the installed `bd --help`, official upstream beads/Dolt docs, the Dolt MCP repo). The agents fetch current facts from these in their own context; the plugin freezes no internals snapshot.
- Upstreams: [beads](https://github.com/gastownhall/beads), [Dolt](https://github.com/dolthub/dolt) and [DoltHub](https://www.dolthub.com), [dolt-mcp](https://github.com/dolthub/dolt-mcp).
