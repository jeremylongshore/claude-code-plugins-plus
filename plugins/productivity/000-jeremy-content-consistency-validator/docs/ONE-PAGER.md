# Content Consistency Validator

**Deterministic doc-drift detection — every fact read from its declared owner, every finding filed against the mirror that drifted, nothing modified.**

## Problem

Docs drift from reality: the README says v0.2.0 while the manifest says 0.3.1, CLAUDE.md
still says "scaffold only" over a working `lib/`, CI runs a different test command than
the README teaches. Worse, the previous tooling carried two contradicting truth axioms
under one command name — "code is truth" in the engine, "website is truth" in the
shadowed marketplace shell — so the same conflict could be arbitrated in opposite
directions depending on which copy ran.

## Solution

One canonical plugin skill (the global engine folded in, the shell deleted) runs 9
deterministic drift checks across docs, code, tests, and CI — versions, index integrity,
README-vs-CI commands, stale status language, cross-doc contradictions, broken
references, planning-vs-implementation. Authority is not ranked or guessed: each
fact-class has a declared owner in a checked-in registry (`sot-map.yaml`), mirrors are
diffed against it within a staleness bound, and a fact-class with no registry row is
reported as "unowned fact-class — human adjudication needed." Findings land in a
severity-grouped Markdown report. Read-only: the report is the only artifact.

## How to run

- `/validate-consistency` — explicit invocation against the working repo
- Natural language: "check consistency", "validate docs", "doc drift check"
- Automatic: invoked by `/release` Phase 1.6 before a release is cut

## W5

|           |                                                                                                                                                    |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Who**   | Maintainers, release engineers, and codebase onboarders — anyone who needs to know which of two disagreeing artifacts to trust                     |
| **What**  | Reads each fact from its registry-declared owner, diffs the mirrors, and reports drift grouped by category and severity, with file-level locations |
| **When**  | Pre-release (`/release` Phase 1.6), after major refactors, when onboarding to an unfamiliar repo, any time docs and code feel out of sync          |
| **Where** | Claude Code, locally against the working repo — no web surfaces, no credentials, no network readers in Phase 1                                     |
| **Why**   | Hand-diffing misses drift, and a global "X is truth" ranking arbitrates wrongly — the registry reads each fact from the surface that produces it   |

## Stack

| Layer          | Choice                                                                              |
| -------------- | ------------------------------------------------------------------------------------ |
| Skill runtime  | Claude Code SKILL.md — plugin-canonical, folded from the proven global engine       |
| Checks         | 9 deterministic drift checks via `Read`/`Glob`/`Grep`/`Bash` — no bundled scripts   |
| Authority      | `sot-map.yaml` per-fact-class registry (home: intent-os), declared as data          |
| Gate           | Golden fixture corpus with seeded drifts — required CI check, exactly-N/zero-invented |
| Output         | Severity-grouped Markdown report; read-only, the report is the only artifact        |
| External APIs  | None — no WebSearch, no WebFetch, no credentialed readers                           |

## What Phase 1 does NOT do

Per the issue #991 design-council cut list — these are scope law, not roadmap slippage:

- **No agents.** The multi-agent roster is cut for v1 (open decision 5, owner Jeremy).
- **No email, no CRM.** Out of v1 entirely; email is never an owner of anything.
- **No WebSearch, no web surfaces.** Repo-local only.
- **No auto-fix.** Read-only is the contract; it reports, you decide.
- **No guessed authority.** No registry row means an explicit adjudication ask — never a
  silent best-effort ranking.
- **No LLM-judged blocking findings.** Judged checks are deferred (Phase 3) and will be
  advisory-only when they arrive.
- **No scheduled or hook-driven runs, no persisted run history.** Deliberate opt-in runs
  only; the longitudinal log is Phase 2.

## Differentiators

1. **Authority is declared data, not a vibe.** A per-fact-class registry replaces the
   global "website is truth" / "code is truth" rankings that contradicted each other —
   and an unowned fact is an explicit human-adjudication ask, never a guess.
2. **Deterministic core, structurally separated judgment.** The drift checks are non-LLM
   value comparisons; anything LLM-judged is architecturally fenced to advisory-only and
   can never be Critical or block a release.
3. **Fixture-gated honesty.** A golden corpus with seeded drifts is the required CI
   check — the tool must find exactly those drifts and invent zero — before any feature
   claim is made.
