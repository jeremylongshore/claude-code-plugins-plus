# contributing-clanker

> Local-only OSS contribution command center. 41 deterministic gates against AI-slop failure modes.

A Claude Code plugin that turns `/contribute` into a discipline tool: every external action (claim, design issue, PR open, comment) passes through phase-appropriate gates that BLOCK or WARN on traps real maintainers complain about. Markdown-only state. No daemons. No SQLite. Filesystem is the tracker.

[![version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/jeremylongshore/contributing-clanker)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/jeremylongshore/contributing-clanker/blob/master/LICENSE)
[![gates](https://img.shields.io/badge/gates-41%20installed-orange.svg)](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/005-AT-SPEC-gate-inventory.md)
[![failure modes](https://img.shields.io/badge/catalog-62%20modes-red.svg)](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/007-DR-CATG-failure-mode-catalog.md)

**Links:** [source repo](https://github.com/jeremylongshore/contributing-clanker) · [gate inventory](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/005-AT-SPEC-gate-inventory.md) · [failure-mode catalog](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/007-DR-CATG-failure-mode-catalog.md) · [risk register](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/010-OD-RISK-operations-and-risk.md) · [architecture](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/002-AT-ARCH-system-architecture.md)

---

## One-Pager

### The Problem

OSS maintainers are drowning in AI-generated low-quality contributions. The pattern is consistent:

- Bots and AI-assisted contributors **claim issues without checking** if they're already shipped, already assigned, or against repo policy
- They **open PRs against `CONTRIBUTING.md` rules** they didn't read (wrong base branch, wrong commit format, missing CLA, banned `Co-Authored-By` lines)
- They **auto-respond to maintainer feedback** in ways that violate the repo's etiquette norms
- They **edit vendored code, version files, or changelogs** because the AI didn't recognize "do not touch" boundaries

The damage isn't always rejection — sometimes the contribution is technically fine, but the surrounding behavior burns maintainer trust, gets the contributor a soft-ban, and feeds the public "AI ruins OSS" narrative.

### The Solution

`contributing-clanker` is a **local-first discipline tool** for AI-assisted OSS contribution. Three layers:

1. **Per-repo dossiers** — `@researcher` reads each upstream's `CONTRIBUTING.md`, linked policy docs, and bot-detected review patterns into a markdown dossier at `~/.contribute-system/research/<owner>__<repo>.md`. Cached. Refreshed on a 14-day staleness threshold.
2. **41 deterministic gates** — one bash script per failure mode. `(candidate, dossier, intended action) → PASS / WARN / BLOCK / INFORM`. Read-only. Pluggable. The gates read the dossier, not live `gh` (latency dominates: most pre-PR sweeps complete in single-digit seconds).
3. **Lifecycle workflow** — `/contribute` walks each candidate through `open → shortlist → claimed → working → submitted → merged`. At each transition, the orchestrator runs the relevant gate set. BLOCK refuses the transition; WARN surfaces in the briefing.

Default behavior: **open a Design Issue first, not a PR**. The skill defaults to design-issue-then-PR because auto-PRs generate "whack-a-mole slopfests" for maintainers. PR comes after maintainer approval of the approach.

### W5 — Who, What, When, Where, Why

| | |
|---|---|
| **Who** | Solo OSS contributors using AI assistance who want to contribute *well*, not just contribute. |
| **What** | A Claude Code plugin (`/contribute`) + a 41-gate runtime under `~/.contribute-system/`. |
| **When** | Every transition: claim, comment, open Design Issue, open PR. Background scout sweeps for ranked candidates. |
| **Where** | Entirely local. Reads live GitHub state via `gh` for the few queries that demand it; everything else hits the cached markdown dossier. |
| **Why** | Because shipping faster than maintainers can review is a failure mode, not a feature. The catalog of 62 enumerated AI-slop patterns is the receipt. |

### Stack

| Layer | Tool |
|---|---|
| Skill orchestration | Claude Code (`/contribute`) + 5 subagents (`@scout`, `@researcher`, `@draft-writer`, `@test-runner`, `@repo-analyzer`) |
| Gate execution | bash + `jq` + `gh` CLI; one script per failure mode under `~/.contribute-system/gates/` |
| State | Markdown candidate files + per-repo markdown dossiers + JSONL append-only event log |
| Prereqs | `gh` authenticated, `jq` on PATH, Claude Code 1.x |

### Key Differentiators

- **Catalog-anchored gates.** Every gate maps to one of 62 enumerated failure modes ([catalog](https://github.com/jeremylongshore/contributing-clanker/blob/master/000-docs/007-DR-CATG-failure-mode-catalog.md)). New gates require a real-world trigger — speculative guards are rejected in review.
- **Override with audit trail.** `--override-gate <ID> "reason"` is an explicit escape hatch. Reasons land in `~/.contribute-system/log.jsonl`. The bundled `audit-overrides.sh` reports gates overridden ≥50% of the time — those are wrong, not yours.
- **Filesystem-only.** No SQLite. No Cloud Functions. No daemons. The candidate file IS the tracker. Greppable. Git-trackable. Survives any tool.
- **Default to design-issue first.** PRs come after maintainer approval. The skill explicitly refuses to auto-submit external content.
- **Per-repo opt-out.** A dossier can disable specific gates with `disabled_gates: [...]`. Honors weird-but-legitimate repo conventions without forking the gate set.

---

## Operator-Grade System Analysis

### Architecture summary

Three layers, deliberately uncoupled. Each can be disabled independently without breaking the others:

```
                      ┌──────────────────────────┐
                      │  /contribute (the skill) │   Layer 3 — lifecycle
                      │  open → shortlist →      │   walks transitions,
                      │  claimed → working →     │   invokes gate-runner
                      │  submitted → merged      │   per transition
                      └────────────┬─────────────┘
                                   │
                      ┌────────────▼─────────────┐
                      │  gate-runner.sh          │   Layer 2 — gates
                      │  41 scripts × phase A-G  │   stateless,
                      │  → PASS/WARN/BLOCK/SKIP  │   read-only,
                      └────────────┬─────────────┘   plug-in
                                   │
                      ┌────────────▼─────────────┐
                      │  Per-repo dossiers       │   Layer 1 — knowledge
                      │  ~/.contribute-system/   │   built by @researcher,
                      │  research/<o>__<r>.md    │   refreshed @ 14d
                      └──────────────────────────┘
```

### Trust boundaries

| Boundary | Trust posture |
|---|---|
| User → skill | Full. The skill is the user's tool. |
| Skill → gates | Full read-trust on the dossier; treats `gh` output as untrusted (validates JSON shape via `jq`). |
| Gates → external (GitHub) | `gh_safe` retry wrapper: 3 retries + exponential backoff + 30s per-call timeout. On exhausted retries, gate returns SKIP, not BLOCK. |
| User data | Lives only at `~/.contribute-system/`. Plugin install creates the dirs; uninstall removes plugin-shipped scripts but **leaves user data intact**. |

### Failure modes the system itself can hit

| Mode | Detection | Response |
|---|---|---|
| Gate has a bug, exits non-zero unexpectedly | `lib/preamble.sh` ERR trap converts to fail-closed BLOCK with reason "gate crashed at line N" | Engineer reviews log.jsonl, fixes the bug; user-side, the candidate is just blocked, not silently passed |
| Gate latency exceeds 10s | Per-gate `timeout 10` in gate-runner | Gate returns SKIP with reason "gate timed out"; user warned, transition continues |
| Dossier is stale (>14d) | Skill Step 0.5 checks `last_refreshed:` field at runtime | Auto-invokes `@researcher refresh` before transition; if refresh fails, surfaces a WARN |
| User overrides a gate routinely (≥50%) | `audit-overrides.sh --since=30` cron-style report | Surface to user; the gate is wrong, not the user — refine or retire |
| Candidate state drifts vs. live GitHub | Reconciliation step in skill (manual: "reconcile candidates") | Walks candidates with `pr_number:`, calls `gh pr view`, updates `status:` field atomically |

### Observability surface

- `~/.contribute-system/log.jsonl` — append-only event log: every gate run, every transition attempt, every override, every scout/researcher invocation, with UTC timestamps
- `audit-overrides.sh [--since=N --scope=org:X --gate=ID --json]` — per-gate override-rate report
- `catalog-coverage.sh` — coverage of installed gates against the 62-mode catalog (currently 41 of 65 = 63%)

### Recovery posture

| Failure | Recovery |
|---|---|
| One gate over-fires across all repos | `chmod -x ~/.contribute-system/gates/<gate>.sh` (runner skips it) |
| One gate over-fires on a specific repo | Edit dossier: `disabled_gates: [<gate>]` |
| Dossier mis-reads a repo | `rm` the dossier, `@researcher build` from scratch |
| Lifecycle workflow misbehaves | Edit `~/.claude/skills/contribute/SKILL.md` (markdown — surgical edit safe) |
| Whole system is wrong | Skip the skill — `gh issue comment` / `gh pr create` directly. Opt-in via `/contribute`; nothing forces its use. |

### What this is NOT

- A bounty board — pre-2026-04-30 versions had Algora/Gumroad framing; that's gone
- A tracker — no SQLite, no dashboard, no cloud backend
- A multi-user system — Phase 1 is single-user. Phase 3 (containerized service) only triggers if multi-user demand surfaces
- An auto-PR generator — defaults to design-issue-first; never auto-submits without explicit human approval

---

## Install

```bash
/plugin install contributing-clanker
```

The post-install hook creates `~/.contribute-system/{candidates,research,gates,gates/lib,bin,check-runs,test-logs}` and copies the runtime scripts in. Your candidate state and dossier history are yours — uninstall preserves them.

**Prerequisites**: `gh` authenticated (`gh auth status`) and `jq` on `PATH`.

## Verify

After install, in any Claude Code session:

```
/contribute
```

The skill activates, reports state (PRs in flight, claimed candidates, ready-to-pick queue), and stays out of the way until you give it work.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/contribute` doesn't activate after install | Restart Claude Code |
| `gh: not logged in` | `gh auth login` |
| `jq: command not found` | `apt-get install jq` (or equivalent for your platform) |
| Gate BLOCKs unexpectedly | Run `audit-overrides.sh --gate=<ID>` to see if it's a known false-positive cluster; override with `--override-gate <ID> "reason"` if the BLOCK is wrong; submit a refinement to the source repo if the gate itself needs fixing |
| Dossier missing for a repo | First contribution to that repo; `@researcher` auto-builds on first transition |
| Stale dossier (>14 days) | Auto-refresh on next gate run; or `@researcher refresh <owner>/<repo>` |
| Want to disable one gate for one repo | Edit the dossier: `disabled_gates: [<gate-id>]` |

## License

MIT — see [LICENSE](https://github.com/jeremylongshore/contributing-clanker/blob/master/LICENSE) in the source repo.
