---
name: audit
description: |
  Use when the user wants a code review on recent changes — quality, spec, security, or performance feedback. Triggers a multi-level (L1-L5) review with a thinking-tier reviewer; on NEEDS_FIX, offers to apply findings via /hyperflow:scope.
  Trigger with /hyperflow:audit, "review this change", "review my PR", "audit the diff", "code review".
allowed-tools: Read, Bash(git:*), Glob, Grep, Agent, AskUserQuestion
argument-hint: "[target] [--level 1-5]"
version: 3.1.2
license: MIT
compatibility: Designed for Claude Code
tags: [code-review, quality, multi-level, multi-agent]
---

# Audit

Multi-level code review. Dispatcher — Opus 4.8 (thinking-tier). Workers — Sonnet 4.6.

This skill exercises **Layer 3 (Orchestrator)** and **Layer 9 (Security)**. After the review prints, a **fix gate** asks the user whether to apply the findings — on `Yes`, audit auto-invokes `/hyperflow:scope` with the findings as the spec, which then chains to `/hyperflow:dispatch`.

## Iron Rules

**Failure recovery (DOCTRINE rule 14).** Worker errors, malformed output, NEEDS_REVISION verdicts, and gate failures in every Step follow the canonical policy in [`skills/hyperflow/failure-recovery.md`](../hyperflow/failure-recovery.md). Audit-specific exception: a failed Reviewer at L1/L2 escalates to an L3+ Reviewer at the same severity level rather than aborting — audit exists to catch issues, so a Reviewer failure is best resolved by a more thorough Reviewer, not by stopping the chain.

## Per-Step Agent Map (DOCTRINE rule 12)

| Step | Sub-phase | Worker tier | Thinking tier | Notes |
|---|---|---|---|---|
| 1 — Resolve scope | — | — | — | Mechanical decision (exempt) |
| 2 — Gather context | 2a — Surface mapping | Searcher × 2 (glob + import-graph) | Sonnet Reviewer | Parallel |
| 2 — Gather context | 2b — Semantic indexing | Searcher × 2 (type-system + symbol-graph) | Sonnet Reviewer | Parallel |
| 2 — Gather context | 2c — Convention scan | Searcher × 1 (test patterns + lint config) | Sonnet Reviewer | Justified single-angle |
| 2 — Gather context | 2d — Aggregate coverage gate | — | **Reviewer** (Opus) verifies aggregate coverage | Thinking-tier coverage gate |
| 3 — Review | 3a — L1+L2 (syntax/format/naming) | — | **Reviewer** (Opus) × 2 (different file groups) + Sonnet Reviewer aggregates verdicts | Parallel Opus pair; justified single-tier (Opus are the workers at L1-L2) |
| 3 — Review | 3b — L3 (integration/security) | — | **Reviewer** (Opus) × 2 (integration + security) + Sonnet Reviewer aggregates verdicts | Parallel Opus pair; justified single-tier (L3 requires thinking-tier) |
| 3 — Review | 3c — L4+L5 (perf/scale/a11y/UX) | — | **Reviewer** (Opus) × 2 (perf/scale + a11y/UX) + Sonnet Reviewer aggregates verdicts | Parallel Opus pair; justified single-tier (L4-L5 requires thinking-tier) |
| 4 — Findings synthesis | 4a — Critical findings | Writer × 2 (evidence probe + impact analysis) | Sonnet Reviewer | Parallel |
| 4 — Findings synthesis | 4b — Important findings | Writer × 2 (root-cause probe + fix-path analysis) | Sonnet Reviewer | Parallel |
| 4 — Findings synthesis | 4c — Suggestions + observations | Writer × 2 (pattern analysis + praise identification) | Sonnet Reviewer | Parallel |
| 4 — Findings synthesis | 4d — Memory feedback | Writer × 1 (anti-pattern curation) | Sonnet Reviewer (dedup + compaction validation) | Atomic Worker→Reviewer; runs after 4a/4b/4c complete; with compaction pass when triggered |
| 5 — Severity reconciliation | — | — | Sonnet Reviewer reconciles severity labels from Step 3 sub-phases | Atomic-exempt per DOCTRINE 12.2.8 — reads existing Step 3 labels; no Workers needed |
| 6 — Fix gate | — | — | — | `AskUserQuestion` only (exempt — structural gate) |

## Approval Gates

| Gate | When | Format |
|---|---|---|
| Fix gate | Step 6, after NEEDS_FIX or PASS-with-suggestions | `AskUserQuestion` — fix all / criticals only / no |
| Hard halt | Any `SECURITY_VIOLATION` from the reviewer | Stop, surface the finding; no fix gate |

## Inputs

- **Target** — file path, line range, commit SHA, branch, or PR number provided by the user
- **Default (no target)** — `git diff HEAD` + `git diff --staged`
- **Level flag** — `--level 1` through `--level 5` (default — L2)

## Review Levels

Adapted from [review-levels.md](references/review-levels.md):

| L | Name | Checks |
|---|------|--------|
| 1 | Quick | Syntax, obvious bugs, formatting |
| 2 | Standard | L1 + spec compliance, naming, edge cases |
| 3 | Thorough | L2 + cross-file consistency, integration risks, security |
| 4 | Deep | L3 + architecture, scalability, accessibility |
| 5 | Exhaustive | L4 + adversarial probing, perf profiling, alternatives |

Security scan (hardcoded secrets, injection, path traversal, XSS, missing validation) is mandatory at L3+. See [security.md](references/security.md).

## Flow

### Step 1 — Resolve scope

Use the provided target or run `git diff HEAD` + `git diff --staged`. No agent dispatched (read-only git).

### Step 2 — Gather context

Sub-phases 2a, 2b, 2c run in parallel (P1). Step 2 output is the union of their worker outputs plus three sub-phase Reviewer verdicts, handed to an Opus aggregate coverage gate.

#### Step 2a — Surface mapping

Dispatch two Searcher agents in parallel:
- Searcher — glob discovery (file extensions, directory tree, entry points)
- Searcher — import-graph traversal (follow `import`/`require`/`use` chains from touched files)

Then dispatch `Sonnet Reviewer — 2a surface mapping coverage check`. Verdict ∈ {`PASS`, `NEEDS_REVISION`, `ESCALATE`}. On `NEEDS_REVISION`, re-dispatch only 2a.

#### Step 2b — Semantic indexing

Dispatch two Searcher agents in parallel:
- Searcher — type-system probe (interface/schema definitions relevant to changed symbols)
- Searcher — symbol-graph probe (callsites, usages, exported references of changed symbols)

Then dispatch `Sonnet Reviewer — 2b semantic indexing coverage check`. Verdict as above.

#### Step 2c — Convention scan

Dispatch one Searcher agent (single-angle justified — test patterns and lint config are a single orthogonal corpus with no independent axis to fan out across):
- Searcher — convention scan (existing test patterns, lint rules, naming conventions, code-style config)

Then dispatch `Sonnet Reviewer — 2c convention scan coverage check`. Verdict as above.

#### Step 2d — Aggregate coverage gate

After 2a + 2b + 2c complete, dispatch `**Reviewer** (Opus) — verifying aggregate context coverage` to confirm the combined surface covers all subsystems relevant to the diff. On coverage gap: re-dispatch the affected sub-phase (max 2 retries); surface gap to user if retries exhausted.

### Step 3 — Review

Sub-phases 3a, 3b, 3c run in parallel (P1) — each ends with a Sonnet sub-phase aggregator before the next batch fires. Active sub-phases scale with `--level`: L1-L2 runs only 3a; L3 adds 3b; L4-L5 add 3c.

#### Step 3a — L1+L2: syntax, formatting, naming

Dispatch two Reviewer agents in parallel over different file groups (split by directory or feature boundary):
- **Reviewer** (Opus) — L1+L2 review, file group A (syntax errors, obvious bugs, formatting, naming conventions)
- **Reviewer** (Opus) — L1+L2 review, file group B (same checklist, different file group)

Then dispatch `Sonnet Reviewer — 3a aggregation` to union the two verdicts and deduplicate overlapping findings. Verdict ∈ {`PASS`, `NEEDS_REVISION`, `ESCALATE`}. On `NEEDS_REVISION`, re-dispatch only 3a.

#### Step 3b — L3: integration, security (L3+ only)

Dispatch two Reviewer agents in parallel over different concern dimensions:
- **Reviewer** (Opus) — L3 integration risks (cross-file consistency, API contract mismatches, race conditions, edge cases)
- **Reviewer** (Opus) — L3 security scan (hardcoded secrets, injection, path traversal, XSS, missing validation — per [security.md](references/security.md))

If the security Reviewer emits `SECURITY_VIOLATION:` → halt immediately; skip the fix gate; surface the finding inline; user decides remediation.

Then dispatch `Sonnet Reviewer — 3b aggregation` to union the two verdicts. Verdict as above.

#### Step 3c — L4+L5: performance, scalability, accessibility, UX (L4+ only)

Dispatch two Reviewer agents in parallel:
- **Reviewer** (Opus) — L4+L5 performance and scalability (algorithmic complexity, memory, bundle size, adversarial load)
- **Reviewer** (Opus) — L4+L5 accessibility and UX (WCAG compliance, keyboard nav, screen-reader semantics, interaction design)

Then dispatch `Sonnet Reviewer — 3c aggregation` to union the two verdicts. Verdict as above.

The Reviewer uses the [reviewer-prompt.md](references/reviewer-prompt.md) template with the diff, level definition, and any applicable spec. Each sub-phase produces structured `[Critical] / [Important] / [Suggestions] / [Praise]` findings that feed into Step 4.

### Step 4 — Findings synthesis

Write the full structured audit to `.hyperflow/audits/<YYYY-MM-DD-HHmm>-<scope-slug>.md`. Sub-phases 4a, 4b, 4c run in parallel (P1), each authoring a section of the audit file. The audit file also receives a memory-append section per [memory-system.md](references/memory-system.md).

#### Step 4a — Critical findings

Dispatch two Writer agents in parallel:
- Writer — evidence probe (trace each Critical finding back to the diff line; confirm reproducibility)
- Writer — impact analysis (articulate user-visible / system-level consequence for each Critical finding)

Then dispatch `Sonnet Reviewer — 4a critical findings review` to verify each Critical entry has a confirmed fix path and no false positives. Verdict ∈ {`PASS`, `NEEDS_REVISION`, `ESCALATE`}.

#### Step 4b — Important findings

Dispatch two Writer agents in parallel:
- Writer — root-cause probe (trace each Important finding to its origin; confirm it's not a symptom of a Critical)
- Writer — fix-path analysis (propose the recommended change per finding, with file:line anchors)

Then dispatch `Sonnet Reviewer — 4b important findings review`. Verdict as above.

#### Step 4c — Suggestions, observations, and memory append

Dispatch two Writer agents in parallel:
- Writer — pattern analysis (identify Suggestion-level improvements; extract reusable patterns for memory)
- Writer — praise identification (flag genuinely well-done decisions; append durable patterns to `.hyperflow/memory/learnings.md` per [memory-system.md](references/memory-system.md))

Then dispatch `Sonnet Reviewer — 4c suggestions + memory dedup check` to ensure no duplicate memory entries land and no Suggestions are mis-classified as Important. Verdict as above.

#### Step 4d — Memory feedback (runs after 4a/4b/4c complete)

After the audit file is written, curate recurring problem patterns into `.hyperflow/memory/anti-patterns.md` so future audit runs and workers benefit from accumulated findings. This is an atomic Worker→Reviewer pair.

Dispatch one Writer agent:
- Writer — anti-pattern curation (read `.hyperflow/memory/anti-patterns.md` if it exists; extract up to 3 new entries from the `[Critical]` and `[Important]` findings produced in 4a/4b; append or update the file)

**Curation rules the Writer must follow:**
- Only `[Critical]` and `[Important]` findings are eligible — Suggestions and Praise are excluded.
- Before writing, read the existing `anti-patterns.md`. If a matching pattern already exists, increment its `frequency` counter and update `last seen`. Do not create a duplicate entry.
- Limit: max 3 new pattern entries per audit run. When more than 3 eligible findings exist, prioritize by breadth — multi-file findings before single-file findings.
- Append entries in this format:

```markdown
## <pattern category> (e.g. Error handling, Naming, Dead code)
- <description> — first observed in audit <YYYY-MM-DD>, frequency: <count>, last seen: <YYYY-MM-DD>
  Recommendation: <what workers should do to avoid this>
```

- Tag `anti-patterns.md` as `#hot` in the session memory index so workers load it at session start alongside other hot-tier files.

**Compaction pass (runs after the Writer appends new entries, not before):**

New findings always land first. After the append, the Writer checks whether compaction is needed. Compaction is triggered when ANY of the following is true:

- Total entry count in `anti-patterns.md` exceeds 50.
- Any entry has `last seen` more than 6 months ago AND `frequency == 1` (stale singleton — never reinforced).
- File line count meets or exceeds the `memory.compactionThreshold` (default 300, from `~/.hyperflow/config.json`).

When triggered, the Writer runs these actions in order:

1. **Merge duplicates.** Entries in the same category with similar wording are merged into one. Combined `frequency` = sum of the merged entries; `last seen` = most recent of the merged entries. Wording is taken from the higher-frequency entry.
2. **Archive stale singletons.** Entries where `frequency == 1` AND `last seen` is older than 6 months move to `.hyperflow/memory/archive/YYYY-MM.md` (month derived from the entry's `last seen` date), tagged with their source so they remain retrievable. This is the same shared monthly archive convention used by `/hyperflow:cache compact` — see `skills/cache/references/compaction.md`.
3. **Cap at 50 entries.** If the file still exceeds 50 entries after merge and archive, evict the lowest-frequency entries. Tiebreak: oldest `last seen` is evicted first. **Never evict entries derived from `[Critical]` findings** — the highest-severity patterns are exactly the ones that must keep surfacing; if eviction is needed and only Critical-sourced entries remain over the cap, leave the file over-cap and note it for the next compaction. Evicted entries move to the same shared monthly archive.
4. **Hot-tier is already wired.** `anti-patterns.md` is permanently hot-tier (see `memory-system.md`). The post-compaction file is injected automatically at the next session start. No manual hot-tier refresh is needed.

If compaction was triggered but none of the three actions has anything eligible to do (e.g. the line-count threshold tripped on a verbose but already-deduped ≤50-entry file), the Writer skips the rewrite — no no-op compaction dispatch. If compaction was not triggered at all, the Writer skips this block entirely and proceeds to the Reviewer.

Then dispatch `Sonnet Reviewer — 4d anti-pattern dedup and compaction check` to verify: no duplicate entries landed, frequency counters are accurate, only Critical/Important findings were promoted, the new-entry count does not exceed 3, and — when compaction ran — no critical entries were dropped without archiving and the archive sidecar was written correctly. Verdict ∈ {`PASS`, `NEEDS_REVISION`}. On `NEEDS_REVISION`, the Writer re-reads the file and corrects the specific violation (max 1 retry before surfacing inline).

### Step 5 — Severity reconciliation (atomic-exempt per DOCTRINE 12.2.8)

Dispatch one `Sonnet Reviewer — severity reconciliation` to consolidate the `[Critical] / [Important] / [Suggestion] / [Praise]` labels already emitted by Step 3 sub-phases (3a/3b/3c). No Workers are dispatched: the Reviewer reads existing Step 3 labels and resolves any conflicts across sub-phases (e.g. a finding flagged `[Important]` in 3a and `[Critical]` in 3b resolves to `[Critical]`). Verdict ∈ {`PASS`, `NEEDS_REVISION`}. On `NEEDS_REVISION`, the Reviewer annotates the specific conflict; the orchestrator applies the resolution inline (no re-dispatch).

After Step 5 completes, the orchestrator writes the graded findings into the audit file (Step 4 section headers get severity labels applied) and prints the chat summary (file-first, DOCTRINE rule 8):

```
── Audit Result ──────────────────────
Scope:    main..HEAD (13 files)
Level:    L3
Verdict:  NEEDS_FIX
Findings: 0 Critical · 4 Important · 4 Suggestions · 5 Praise
Written:  .hyperflow/audits/2026-05-16-1730-memory-compaction.md
─────────────────────────────────────
```

No `[Critical]` / `[Important]` body lines in chat. The user opens the file (or the chat host previews it). For `PASS`-clean runs (no Critical/Important), print just the one-line `Audit clean — no fixes needed.` and still write the file with the praise + suggestions list (so the audit history is preserved). Skip the file write only on `SECURITY_VIOLATION` — those need immediate eye-level surfacing; print the finding inline and halt.

### Step 6 — Fix gate (STRUCTURAL GATE · DOCTRINE rule 8)

After the summary prints, the audit skill **MUST** ask the user via `AskUserQuestion` whether to apply the findings. Per DOCTRINE rule 8, this gate always fires when findings exist — autonomy directives do NOT skip it. Defaulting silently is a doctrine violation.

**Skip the gate only when:** verdict is `PASS` with no `[Critical]` or `[Important]` entries (Suggestions-only or Praise-only). Stop after the one-line `Audit clean — no fixes needed.` summary.

**Skip the gate also when:** verdict is `SECURITY_VIOLATION`. Halt and let the user decide.

**Otherwise**, ask:

```
?  Audit findings written to .hyperflow/audits/<timestamp>-<slug>.md — apply fixes?

   Fix all (Recommended)   — Critical + Important + Suggestions via /hyperflow:scope → /hyperflow:dispatch
   Critical + Important    — skip Suggestions, fix the rest
   Critical only           — fix the must-haves, defer the nice-to-haves
   No, leave as-is         — stop; you'll handle manually
```

Recommended option scales with finding mix:
- Any `[Critical]` present → `Fix all (Recommended)` — Critical items can't be deferred
- Only `[Important]` + `[Suggestions]` → `Critical + Important (Recommended)`
- Only `[Suggestions]` → `No, leave as-is (Recommended)` — Suggestions are optional by definition; the gate fires but recommends skipping

**On any "Fix …" choice:**

1. Build a spec file from the chosen findings at `.hyperflow/specs/audit-<YYYY-MM-DD>-<scope-slug>.md`. Each finding becomes a numbered fix section with: file:line, the issue, the reviewer's suggested fix (or "design needed" if no Fix: was provided), and the commit message stub. The spec file is the chain-driving artefact; do NOT paste fix bullets into chat.
2. Invoke `Skill` with `skill: scope` and `args: "chain-mode=auto spec=.hyperflow/specs/audit-<YYYY-MM-DD>-<scope-slug>.md"`.
3. `/hyperflow:scope` will decompose into batches; `/hyperflow:dispatch` will execute them — same per-sub-task commit cadence and per-batch L1–L<n> review as any other chain run.

**On "No":**

Print one line and stop:

```
Audit complete — N findings recorded, no fixes applied. Re-run /hyperflow:audit later or invoke /hyperflow:scope manually if you change your mind.
```

If `AskUserQuestion` cannot be presented as a popup, use the Codex fallback: print the fix gate as a `Hyperflow Question` chat block with numbered options, then stop and wait for the user's answer. If no interactive channel is available at all, print the findings and an error line — never silently auto-fix or silently exit.

## Output Format

Two outputs per audit run:

**1. The audit file** at `.hyperflow/audits/<YYYY-MM-DD-HHmm>-<scope-slug>.md` — full structured review, formatted per [`../hyperflow/artefact-format.md`](../hyperflow/artefact-format.md):

```markdown
# Audit — <scope description>

## Status

| Field    | Value                                                |
|----------|------------------------------------------------------|
| Verdict  | `<PASS \| NEEDS_FIX \| SECURITY_VIOLATION>`          |
| Scope    | `<files / range / commit>`                           |
| Level    | L<n>                                                 |
| Findings | N Critical · N Important · N Suggestions · N Praise  |
| Date     | <YYYY-MM-DD HH:mm>                                   |

## TL;DR

<2–3 sentences: the most important takeaway + the most important fix
to apply. The user reads this and decides whether to dig into the
findings list.>

## Findings

### [Critical] `<file>:<line>` — <one-line issue title>

**Issue:** <one paragraph: what's broken and why it's blocking>

**Fix:** <one paragraph: the recommended change, with the file:line
anchor and the suggested replacement>

**Why it matters:** <one sentence: the user-visible or system-level
consequence if shipped as-is>

### [Important] `<file>:<line>` — <one-line issue title>
...

### [Suggestion] `<file>:<line>` — <one-line improvement title>
...

### [Praise] `<file>:<line>` — <one-line note>
...

## Security scan (L3+ mandatory)

| Category          | Result                |
|-------------------|-----------------------|
| secrets           | pass                  |
| injection         | pass                  |
| path traversal    | pass                  |
| DoS               | pass | concerns       |
| missing validation| pass | concerns       |

## Cost

| Tier      | Agents | Tokens   |
|-----------|-------:|---------:|
| Worker    |      1 |     ~Nk  |
| Thinking  |      1 |     ~Nk  |
| **Total** |  **2** | **~Nk**  |
```

**2. The chat summary** — one short box that points at the file, NEVER the findings themselves:

```
── Audit Result ──────────────────────
Scope:    <files / range>
Level:    L<n>
Verdict:  <PASS | NEEDS_FIX | SECURITY_VIOLATION>
Findings: 0 Critical · 4 Important · 4 Suggestions · 5 Praise
Written:  .hyperflow/audits/<YYYY-MM-DD-HHmm>-<scope>.md
──────────────────────────────────────
```

## Hand-off

- **PASS** (no findings worth fixing) — print `Audit clean`. Suggest `/hyperflow:deploy` if the user is ready to release. Do not auto-ship.
- **NEEDS_FIX** — fix gate fires (Step 6). On `Yes …` → auto-chain to `/hyperflow:scope`. On `No` → stop with findings printed.
- **SECURITY_VIOLATION** — halt. Skip the fix gate. User decides remediation path.

## Doctrine

Full rules in [DOCTRINE.md](references/DOCTRINE.md). Output style in [output-style.md](references/output-style.md). Per-step agent dispatching follows rule 12.

## Overview

`/hyperflow:audit` runs a multi-level code review against uncommitted changes, a specific commit, branch, or PR. A Sonnet searcher gathers context; an Opus reviewer produces verdicts at the chosen level (L1 quick scan to L5 exhaustive). On `NEEDS_FIX`, a structural gate asks the user whether to apply findings — `Yes` auto-chains to `/hyperflow:scope` → `/hyperflow:dispatch`; `No` leaves the diff alone.

## Prerequisites

- Git repository with the change(s) to review present in the working tree, staged, or in history.
- `.hyperflow/` cache optional but recommended (Layer 0 analysis improves reviewer context). Run `/hyperflow:scaffold` first if missing.
- Model routing config supports a thinking tier (default: Opus 4.8). Without it, the reviewer downgrades to the worker tier and emits a warning.

## Instructions

See [Flow](#flow) above — Steps 1-6 are the operational instructions. Summary:

1. Resolve scope (target arg or `git diff HEAD`).
2. Surface mapping + semantic indexing + convention scan (2a/2b/2c in parallel); Opus aggregate coverage gate (2d).
3. L1+L2 syntax/naming (3a) + L3 integration/security (3b) + L4+L5 perf/a11y (3c); each sub-phase Opus pair → Sonnet aggregator.
4. Findings synthesis: Critical (4a) + Important (4b) + Suggestions/memory (4c) — each sub-phase Writer pair → Sonnet reviewer.
5. Severity reconciliation (atomic-exempt — single Sonnet Reviewer consolidates Step 3 labels); print chat summary pointing at audit file.
6. Fix gate fires on `NEEDS_FIX` with critical/important findings.

## Output

See [Output Format](#output-format) above for the exact block. Single review block per invocation; agent count line at the bottom shows the model/role split.

## Error Handling

| Failure | Behavior |
|---|---|
| No diff to review (clean working tree, no target) | Print `Nothing to review — clean working tree. Pass an explicit target.` and stop. |
| Searcher returns no context (file gone, bad path) | Reviewer flags `[Critical] — target unreachable` and halts at Step 3. |
| Reviewer emits `SECURITY_VIOLATION` (L3+ only) | Skip Step 4 onward. Print finding. Do not fire fix gate. User decides remediation. |
| `AskUserQuestion` popup unavailable in Codex | Print the fix gate as a `Hyperflow Question` chat block and wait for the user's answer. |
| No interactive channel at all | Print findings + an error line stating the fix gate could not fire. Never silently auto-fix or silently exit. |
| Reviewer disagrees with worker context (NEEDS_FIX on Step 2 coverage check) | Re-dispatch Searcher with the reviewer's gap list. Max 2 retries before surfacing the gap to user. |

## Examples

Worked transcripts moved to [examples.md](references/examples.md) so the SKILL body stays lean. The examples are illustrative — not load-bearing for behaviour. Read the companion file when you want to see end-to-end transcripts.

## Resources

- [DOCTRINE.md](references/DOCTRINE.md) — orchestration rules (especially #8 structural gates, #12 per-step agents).
- [review-levels.md](references/review-levels.md) — full checklist for L1-L5.
- [reviewer-prompt.md](references/reviewer-prompt.md) — Opus reviewer template.
- [security.md](references/security.md) — security scan policy (mandatory at L3+).
- [memory-system.md](references/memory-system.md) — how patterns are persisted.
- [output-style.md](references/output-style.md) — label and table conventions.
