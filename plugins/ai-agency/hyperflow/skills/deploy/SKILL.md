---
name: deploy
description: |
  Use when ready to ship — runs pre-push gates (lint, typecheck, build, tests, security sweep), commits, releases, and pushes. Standalone, never auto-invoked. Push always requires explicit confirmation.
  Trigger with /hyperflow:deploy, "ship it", "ready to push", "release", "cut a release", "deploy".
allowed-tools: Read, Write, Edit, Bash(git:*), Bash(npm:*), Bash(pnpm:*), Bash(./scripts/*:*), Glob, Grep, AskUserQuestion
argument-hint: ""
version: 3.1.2
license: MIT
compatibility: Designed for Claude Code
tags: [release, ci, automation, push-gates]
---

# Deploy

No gate skipped, no failure ignored. If any gate fails, halt and report. Never `--no-verify`. Never bypass.

**Failure recovery (rule 14).** Worker errors and Quality Gate failures follow the canonical policy in [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). Gate failures are user-surfaced, never auto-fixed — print the failing command + full stderr and halt the push. Never `--no-verify`, never force-push to main.

## Per-Step Agent Map

| Step | Sub-phase | Worker tier | Thinking tier | Notes |
|---|---|---|---|---|
| 1a | Repo-state scan | Worker A (git status), Worker B (git log) | Sonnet | — |
| 1b | Tool detection | Worker A (profile.md + lockfiles), Worker B (testing.md + devDeps) | Sonnet | — |
| 2a | Lint + typecheck (parallel) | Worker A (linter), Worker B (formatter), Worker C (tsc) | Sonnet | Step 3 (Security Sweep) runs in parallel with Step 2 at orchestrator level; 2a halts chain on any failure before 2b |
| 2b | Build gate | Worker A (prod build), Worker B (dev build) | Sonnet | Depends on 2a PASS |
| 2c | Test gate | Worker A (unit), Worker B (integration/E2E) | Sonnet | Parallel (P1); depends on 2b PASS |
| 3a | Secrets scan | Worker A (diff pattern), Worker B (file pattern) | **Opus** | Runs in parallel with Step 2 (pre-build; read-only) |
| 3b | Dependency audit | Worker A (CVE audit), Worker B (license check) | Sonnet | — |
| 4 | Commit | single Worker | Sonnet | atomic-exempt (DOCTRINE 12.2) |
| 5a | Release execution | single Worker | Sonnet | atomic-exempt (DOCTRINE 12.2) |
| 5b | Version sync | Worker A (manifests), Worker B (changelog) | Sonnet | — |
| 6 | Push gate | AskUserQuestion | — | structural gate; atomic-exempt |
| 7 | Output | single print | — | atomic-exempt (§12.1) |

## Step 1 — Survey State

Sub-phases run in parallel (P1).

### Step 1a — Repo-state scan

Two Workers in parallel:

- Worker A — `git status --short` — uncommitted changes, staged files
- Worker B — `git log origin/<branch>..HEAD --oneline` — commits ahead of remote; detect branch name

Sonnet Reviewer — verdict on repo state (clean / has uncommitted / ahead by N). If detached HEAD or no remote configured → halt with reason.

### Step 1b — Tool detection

Two Workers in parallel:

- Worker A — Read `.hyperflow/profile.md` for package manager and project type; fallback: inspect `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`
- Worker B — Check `.hyperflow/testing.md` for test runner; fallback: detect from `package.json` devDependencies (`vitest`, `jest`, `playwright`, `pytest`, etc.)

Sonnet Reviewer — produce a single tool manifest (package manager, test runner, typed-project flag, build script presence). Used by Step 2 gates.

## Step 2 — Quality Gates

Step 2 runs in parallel with Step 3 (Security Sweep) at the orchestrator level — both are pre-build, read-only checks. Both must reach `PASS` before Step 4 (Commit) may proceed. Within Step 2, sub-phases 2a → 2b → 2c run sequentially (2b depends on 2a PASS; 2c depends on 2b PASS). Halt at the first `NEEDS_REVISION` verdict.

Wall-clock note: default flow runs 3 gates simultaneously (lint + security + typecheck in parallel), then build, then tests — roughly max(lint, security, typecheck) + build + max(unit, integration), versus the old 4× sequential gate duration. Typical saving: ~40% wall-clock reduction. Under `--thorough`, intra-sub-phase Workers serialize (DOCTRINE §12.2/clarification), so the full saving collapses to 2c's unit + integration pair only.

Print `Gate <letter> — <name>` before each sub-phase.

### Step 2a — Lint + typecheck (parallel; no build artifact required)

Three Workers in parallel (P1). None depend on build output — safe to run alongside Step 3.

- Worker A — Detect and run primary linter: `npm run lint` / `pnpm lint` / `bun run lint` / `eslint .`. On failure: auto-fix via `--fix`, re-run once; report final error count.
- Worker B — Detect and run formatter check: `prettier --check .` / `biome check .` / equivalent. Report diff count.
- Worker C — Root typecheck: `tsc --noEmit` / `npm run typecheck`. Skip if not a typed project (per Step 1b tool manifest). Also run per-package typecheck if workspace detected (pnpm/yarn workspaces): iterate packages with `tsc --noEmit` in each.

Sonnet Reviewer — aggregate verdict across all three Workers:
- `PASS` — all clean (or absent/untyped)
- `NEEDS_REVISION` — any gate fails → halt before 2b. Report which specific gate(s) failed and why. Do NOT proceed to build.
- `ESCALATE` — config errors preventing execution of any gate

### Step 2b — Build gate (sequential; depends on 2a PASS)

Two Workers in parallel:

- Worker A — Production build: `npm run build` / `pnpm build` / `bun run build`. Capture output; report size or artifact path if printed.
- Worker B — Dev/preview build if a separate script exists (`npm run build:dev`, `vite build --mode development`, etc.). Skip if no separate dev-build script.

Sonnet Reviewer — verdict:
- `PASS` — production build succeeds
- `NEEDS_REVISION` — production build fails → halt with output
- `ESCALATE` — build tool absent or script missing (skip silently, not failure)

### Step 2c — Test gate (parallel; depends on 2b PASS)

Two Workers in parallel (P1):

- Worker A — Unit tests: run full unit suite per runner from Step 1b (vitest, jest, pytest, cargo test, etc.). Full suite — not just affected. Report count.
- Worker B — Integration / E2E tests if runner detected separately (playwright, cypress, etc.). Skip if no integration runner found.

Sonnet Reviewer — verdict:
- `PASS` — all tests pass (or integration absent)
- `NEEDS_REVISION` — failing tests → halt with failing test names. Do NOT skip. Do NOT increase timeout.
- `ESCALATE` — runner misconfigured or no tests found and test runner is declared

See [quality-gates.md](references/quality-gates.md) for gate details.

## Step 3 — Security Sweep

Runs in parallel with Step 2 at the orchestrator level (P3 — concurrent independent pre-conditions; DOCTRINE §12.2). Both Step 2 and Step 3 are pre-build, read-only checks with no shared state. Both must reach `PASS` before Step 4 (Commit) may proceed. Halt on `SECURITY_VIOLATION` immediately — no retry, no 2a must also complete first.

Sub-phases 3a and 3b run in parallel (P1).

### Step 3a — Secrets and keys scan

Two Workers in parallel:

- Worker A — Pattern scan staged + recent diff for hardcoded secrets: API keys, private keys, connection strings, tokens. Use `git diff HEAD~1..HEAD` as scan surface.
- Worker B — File-level scan of files modified in this changeset for common secret patterns (SG., sk-, ghp_, AKIA, BEGIN RSA PRIVATE KEY, etc.).

**Reviewer** — Opus security sweep — aggregate findings from 3a Workers. If any secret found → halt immediately with `SECURITY_VIOLATION: <file>:<line> — <pattern>`. No auto-remediation — user must rotate + remove.

### Step 3b — Dependency audit

Two Workers in parallel:

- Worker A — `npm audit --audit-level=high` / `pnpm audit` / `pip-audit` / `cargo audit`. Report critical and high CVEs only.
- Worker B — License check: scan new dependencies added in this changeset for prohibited licenses (GPL in a proprietary project, etc.) if `.hyperflow/profile.md` declares a license policy.

Sonnet Reviewer — verdict:
- `PASS` — no critical/high CVEs; no license violations
- `NEEDS_REVISION` — critical CVE found → halt and surface CVE IDs
- `ESCALATE` — audit tool absent → skip silently (not a failure); missing license policy → skip

## Step 4 — Commit

Atomic — single Worker → Reviewer pair with no parallel angles. Exempt from sub-phase decomposition per DOCTRINE 12.2 atomic exemption.

- Worker-introduced fixes from Step 2 → commit automatically with a conventional commit message.
- Pre-existing user-owned uncommitted changes → use `AskUserQuestion` to confirm inclusion. Per DOCTRINE rule 8, this is a binary action gate — no recommendation marker:

  ```
  Include uncommitted user changes in this commit?
    Include — your local work + the pre-push fixes ship together
    Exclude — commit only the worker fixes; user changes stay local
  ```

  If the popup UI is unavailable in Codex, print the same inclusion gate as a `Hyperflow Question` chat block and wait for the user's answer.

- **Never** add `Co-Authored-By: Claude` in commit messages — see [git-workflow.md](references/git-workflow.md).

## Step 5 — Release

Sub-phases run sequentially (5b depends on 5a output).

### Step 5a — Release script execution

Single Worker (no parallel angle — single mechanical action):

- Worker — `scripts/release.sh` exists → run it. `release-please` / `changesets` detected → use it. "Nothing to release" or no releasable commits → skip and record `Release: skipped`.

Sonnet Reviewer — capture output: new version string (if bumped) or skip reason. Feed version to Step 5b.

### Step 5b — Version sync verification

Two Workers in parallel (only runs if 5a produced a new version):

- Worker A — Verify version appears consistently across all manifests: `package.json`, `plugin.json`, `marketplace.json`, any other version-bearing files identified in Step 1b.
- Worker B — Verify CHANGELOG was updated by the release script: check that the new version header exists in `CHANGELOG.md` (or equivalent). Skip if no changelog file.

Sonnet Reviewer — verdict:
- `PASS` — all manifests in sync; changelog updated
- `NEEDS_REVISION` — version mismatch or changelog missing entry → halt
- (Skip entirely if Step 5a returned `Release: skipped`)

## Step 6 — Push (honors `push` pre-election from Scope Step 2.6 · STRUCTURAL GATE when `push=ask`)

Read the `push` arg from chain args (propagated from Scope Step 2.6 when `chain-mode=auto`). Three paths:

**`push=auto`** — push immediately without asking. Print `Push: pre-elected (auto) — pushing branch + tags…`. Run `git push`, then `git push --tags` if release created tags. Skip the `AskUserQuestion` call. Per DOCTRINE rule 8, this is NOT an invented skip — the user already gave consent at Scope Step 2.6.

**`push=never`** — skip the push step entirely. Print `Push: pre-elected (never) — branch held local. Run \`git push\` manually when ready.` Do not call `git push`.

**`push=ask`** (default; also fires when no operational pre-election was made — e.g. deploy invoked standalone) — fire the structural-gate `AskUserQuestion`. Per DOCTRINE rule 8, this is a binary action gate — no recommendation marker on either option.

```
Push to origin/<branch>?
  Push — all gates pass · safe to ship
  Hold — keep local; you can push later
```

- **Never force-push to main or master**, regardless of `push` value. `push=auto` is a plain `git push`; if the remote rejects it (non-fast-forward), surface the error and stop — do NOT add `--force`.
- On yes (or `push=auto`) — `git push`, then `git push --tags` if release created tags.
- If the popup UI is unavailable in Codex for `push=ask`, print the push gate as a `Hyperflow Question` chat block and wait for the user's answer. If no interactive channel is available at all, hold the push and print `Push: held — interactive confirmation required`.

## Step 7 — Output

```
── Ship Result ───────────────────
Branch: <name>
Gates: lint pass · typecheck pass · build pass · tests pass (<n> passed)
Security: pass
Commit: <sha> <message>
Release: v<x.y.z> (or skipped)
Push: confirmed (or held)
──────────────────────────────────
```

On gate failure:

```
── Ship Result ───────────────────
Branch: <name>
Gates: lint pass · typecheck fail · build skipped · tests skipped
  typecheck: 3 errors in src/auth/middleware.ts
Halted at Step 2a
──────────────────────────────────
```

Use `pass` / `fail` / `skipped` as plain words — no `✓` / `✗` / `—` symbols.

## Anti-patterns

- `--no-verify`, `--no-gpg-sign`, bypassing hooks
- Ignoring failing tests
- Force-pushing to main
- Auto-pushing without explicit confirmation
- Committing `Co-Authored-By: Claude`

## Memory

After successful ship, append to `.hyperflow/memory/patterns.md` if any new pattern was confirmed during gates. Skip if nothing new.

## Doctrine

Full rules in [DOCTRINE.md](references/DOCTRINE.md). Output style in [output-style.md](references/output-style.md).

## Overview

`/hyperflow:deploy` runs the pre-push gates (lint + typecheck + security sweep in parallel, then build, then tests), composes any worker-introduced fixes into a clean commit, runs the release script if present, and asks before pushing. Standalone — never auto-invoked from the chain. Push always requires an explicit `AskUserQuestion` confirmation. Never bypasses hooks, never force-pushes to main, never adds AI attribution to commits.

## Prerequisites

- Git repository with a remote configured (for the push step).
- Lint / typecheck / build / test scripts detectable in `package.json` or via `.hyperflow/testing.md`. Missing scripts are skipped silently (not failed).
- `scripts/release.sh` (or `release-please` / `changesets`) optional — if present, runs at Step 5; otherwise release is user-managed.
- For security sweep: a thinking-tier model (Opus 4.8) available. Sweep is mandatory; missing model = halt.

## Instructions

The 7 numbered steps live in [Step 1 — Survey State](#step-1--survey-state) through [Step 7 — Output](#step-7--output) above. Summary:

1. Survey state — two sub-phases in parallel: 1a repo-state scan (git status + ahead count), 1b tool detection (package manager, test runner, typed-project flag).
2. Quality gates — three sequential sub-phases: 2a lint+typecheck (3-wide parallel Workers, no build artifact needed), 2b build (depends on 2a PASS), 2c tests (2-wide parallel, depends on 2b PASS). Runs in parallel with Step 3 at orchestrator level. Halt at first `NEEDS_REVISION`.
3. Security sweep — runs in parallel with Step 2 (P3, pre-build read-only). Two sub-phases in parallel: 3a secrets/keys scan (Opus Reviewer), 3b dependency audit. Halt on `SECURITY_VIOLATION` or critical CVE. Both Step 2 and Step 3 must PASS before Step 4.
4. Commit — atomic. Worker fixes auto-committed; `AskUserQuestion` for pre-existing uncommitted user changes.
5. Release — two sequential sub-phases: 5a run release script, 5b verify version sync across manifests.
6. Push gate — atomic structural gate. Honors `push` pre-election (auto/never/ask). `push=ask` fires `AskUserQuestion`. Never force-push to main.
7. Print structured ship result.

## Output

See the ship result block in [Step 7 — Output](#step-7--output) above. Two formats: success (all gates pass, listed inline) and failure (halt at first failing gate, listed in order). Always uses plain words (`pass` / `fail` / `skipped`) — no decorative symbols.

## Error Handling

| Failure | Behavior |
|---|---|
| Step 2a — lint fails | Auto-retry once with `--fix`. Still failing → halt with error count. Do NOT proceed to 2b. |
| Step 2a — typecheck fails | Halt at 2a. No auto-fix — typecheck errors require human eyes. |
| Step 2b — build fails | Halt with build output. Pre-existing build issues likely pre-date the change set. |
| Step 2c — tests fail | Halt with failing test names. Do NOT skip failing tests. Do NOT increase timeout. |
| Security sweep finds secrets | Halt with `SECURITY_VIOLATION:` marker and the file:line. User decides remediation (revert the secret + rotate the credential). |
| `scripts/release.sh` says "nothing to release" | Skip release; print `Release: skipped (nothing to release)`. Push step still fires for non-release commits. |
| Push rejected (non-fast-forward) | Refuse to force-push. Print: `Push rejected — branch is behind origin. Pull/rebase first.` |
| `AskUserQuestion` popup unavailable in Codex | Print the push or commit-inclusion gate as a `Hyperflow Question` chat block and wait for the user's answer. |
| Headless / non-interactive | Refuse push step entirely. Print structured result with `Push: held — interactive confirmation required`. |
| Pre-existing uncommitted user changes | Use `AskUserQuestion` to ask whether to include or exclude from the commit. Default: include. |

## Examples

### Clean release path

```
/hyperflow:deploy

Step 2a — Lint + typecheck (parallel with Step 3 security sweep)
Worker A — running lint
Worker B — running formatter check
Worker C — running tsc
Step 3a/3b — security sweep (parallel)
Step 2a Reviewer — all clean
Step 3 Reviewer — no secrets found
Step 2b — Build
Step 2c — Tests (parallel)

? Push to origin/main?
   Push — all gates pass · safe to ship
   Hold — keep local; you can push later

[user picks Push]

── Ship Result ───────────────────
Branch: main
Gates: lint pass · typecheck pass · build pass · tests pass (147 passed)
Security: pass
Commit: dc38564 fix(skills): marketplace validator compliance
Release: v3.1.2
Push: confirmed
──────────────────────────────────
```

### Gate failure halts the pipeline

```
/hyperflow:deploy

Step 2a — Lint + typecheck (parallel with Step 3 security sweep)
Worker A — running lint
Lint failed: 3 errors in src/auth/middleware.ts
Auto-fix attempted... still failing.
Step 2a Reviewer — NEEDS_REVISION: lint gate failed (3 errors in src/auth/middleware.ts)
Halted at Step 2a. Build and tests skipped.

── Ship Result ───────────────────
Branch: main
Gates: lint fail · typecheck skipped · build skipped · tests skipped
  lint: 3 errors in src/auth/middleware.ts (unused vars, missing return type)
Halted at Step 2a
──────────────────────────────────
```

### Security violation

```
/hyperflow:deploy

Gates pass: lint · typecheck · build · tests
**Reviewer** — security sweep
SECURITY_VIOLATION: src/config/email.ts:12 — hardcoded SendGrid API key (SG.xxx...)

Halted before commit. Rotate the credential and remove the literal from source before retrying.
```

## Resources

- [DOCTRINE.md](references/DOCTRINE.md) — orchestration rules (especially #8 push confirmation gate).
- [quality-gates.md](references/quality-gates.md) — full lint/typecheck/build/test policy.
- [security.md](references/security.md) — security sweep policy and blocklists.
- [git-workflow.md](references/git-workflow.md) — branch/commit conventions, no AI attribution rule.
- [output-style.md](references/output-style.md) — ship result formatting.
