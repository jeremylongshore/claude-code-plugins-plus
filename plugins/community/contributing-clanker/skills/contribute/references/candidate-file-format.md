# Candidate file format

Canonical specification for the markdown candidate files at
`~/.contribute-system/candidates/<owner>__<repo>__issue<N>.md`.

Each candidate file is the per-issue tracker. The frontmatter is the queryable
layer; the body holds drafts and structured sections that gates read at
transition time. **Manual edits in the body survive refresh** — only the
frontmatter is auto-managed.

---

## Filename

```
~/.contribute-system/candidates/<owner>__<repo>__issue<N>.md
```

- `<owner>` and `<repo>` are joined by **double** underscore (`__`)
- `<N>` is the upstream issue number (or PR number for backfilled candidates that have no linked issue)
- One file per upstream issue; never multiple files for the same issue

---

## Frontmatter (YAML, between two `---` lines)

The frontmatter is canonical state. Every gate reads from it. `transition.sh`
writes to it atomically when state moves.

| Field | Required | Type | Read by | Notes |
|---|---|---|---|---|
| `discovered_at` | yes | ISO8601 UTC | scout/researcher | when scout first wrote the candidate |
| `repo` | yes | `<owner>/<repo>` | every gate | upstream repo |
| `issue_number` | yes | int | A-phase gates | upstream issue # |
| `issue_url` | yes | URL | (info) | direct link |
| `star_tier` | yes | `niche` / `emerging` / `established` / `mainstream` | scout ranking | from `star_count` |
| `star_count` | yes | int | scout ranking | |
| `repo_lang` | yes | string | scout filter | primary language |
| `competing_prs` | yes | int | A02 gate | scout-detected open PRs claiming this issue |
| `primary_label` | yes | string | scout heuristic | upstream's primary label |
| `scout_score` | yes | float (0–1) | scout ranking | momentum signal |
| `status` | yes | enum (see below) | every gate + transition.sh | lifecycle state |
| `last_refreshed` | yes | ISO8601 UTC | researcher | when scout/researcher last touched |
| `merge_probability_pct` | optional | int (0–100) | scout ranking | empirical merge rate at this repo |
| `research_path` | optional | absolute path | every gate that reads dossier | path to per-repo dossier; auto-resolved if empty |
| `pr_number` | optional | int | reconciliation | set after PR opens |
| `pr_url` | optional | URL | reconciliation | set after PR opens |
| `branch` | optional | string | B/C-phase gates | local feature branch name |
| `disabled_gates` | optional | array of gate IDs | gate-runner | per-candidate gate disables (escape hatch) |

### `status` enum

```
open       → discovered, not yet vetted
shortlist  → vetted, queued for next claim
claimed    → posted claim comment, waiting for "go ahead" / no objection
working    → actively coding (local clone exists, diff in progress)
submitted  → PR or Design Issue opened upstream
merged    → upstream merged the PR
dropped    → closed without merge (failure log entry created in dossier)
```

`transition.sh` enforces the legal transitions and atomically updates the
field on success.

---

## Body sections

The body holds drafts + evidence. Sections are populated at different lifecycle
stages by different agents. Manual edits survive refresh.

### Section inventory

Order, owner, and which gates read each section:

| Section | Populated at | Owner | Read by gates |
|---|---|---|---|
| `# <repo>#<N> — <title>` | discovery | scout | (display only) |
| `## Why scout flagged this` | discovery | scout | (info; helps reviewer) |
| `## Scope` | qualification | user / @repo-analyzer | B07 (must enumerate planned scope) |
| `## Files to touch` | qualification | user / @repo-analyzer | B07 (must list specific files) |
| `## Claim comment draft` | claim | @draft-writer | A06 (etiquette comment must reference dossier excerpts) |
| `## Issue body draft` | submit (Design Issue path) | @draft-writer | C03, C09 (issue body sections + issue link) |
| `## PR title` | submit | @draft-writer | C02 (regex match against `pr_title_regex` in dossier) |
| `## PR body` | submit | @draft-writer | C03, C05, C09, C19 (body sections + test evidence + issue link + claim-vs-diff) |
| `## Test results` | working | @test-runner | C05 (concrete evidence required pre-submit) |
| `## Review draft` | review (post-merge sometimes) | @draft-writer | D02, D03 (no-AI-reviews-without-disclosure) |
| `## Safety override disclosure` | submit | user (only if --override-gate used) | F04 (mandatory if any gate was overridden) |

### Required sections by lifecycle stage

| Status | Sections that MUST exist | Sections that MAY exist |
|---|---|---|
| `open` | none beyond H1 | `## Why scout flagged this` |
| `shortlist` | `## Scope`, `## Files to touch` | `## Claim comment draft` |
| `claimed` | `## Claim comment draft` | `## Scope`, `## Files to touch` |
| `working` | scope + files + claim draft | `## Test results` (early evidence) |
| `submitted` | `## PR title`, `## PR body`, `## Test results` | `## Issue body draft` (if Design Issue path), `## Safety override disclosure` (if any overrides) |
| `merged` | everything from `submitted` | none added |
| `dropped` | everything that existed | (failure-log entry in dossier referenced here) |

Backfilled candidates (created retroactively for already-open PRs) may
legitimately skip the early-stage sections — their gates will SKIP rather
than BLOCK, which is correct behavior.

---

## Worked example (a `submitted`-state candidate)

```markdown
---
discovered_at: 2026-04-15T09:00:00Z
repo: example-org/example-repo
issue_number: 42
issue_url: https://github.com/example-org/example-repo/issues/42
star_tier: mainstream
star_count: 15000
repo_lang: TypeScript
competing_prs: 0
primary_label: bug
scout_score: 0.82
status: submitted
pr_number: 137
pr_url: https://github.com/example-org/example-repo/pull/137
branch: fix/42-null-deref
research_path: /home/jeremy/.contribute-system/research/example-org__example-repo.md
last_refreshed: 2026-04-20T14:30:00Z
---

# example-org/example-repo #42 — null deref in formatter

## Why scout flagged this

Open >7d, primary_label=bug, momentum_score: 0.82 (3 maintainer comments
in last week, no competing PRs).

## Scope

Replace the unchecked `.format()` call in `src/format.ts` with a guarded
variant that returns `null` instead of throwing.

## Files to touch

- `src/format.ts` (1-2 lines)
- `src/__tests__/format.test.ts` (add 2 cases for null + undefined)

## Claim comment draft

Hi! I'd like to take this. Plan: replace `.format()` with a guarded
variant that returns `null` for nullish input, mirroring the pattern in
`src/parse.ts`. ETA: end of week. Will open a Design Issue first per your
CONTRIBUTING.md.

## PR title

fix: guard against null input in formatter (#42)

## PR body

## Problem

`format()` throws on `null` / `undefined` input where callers expect a
nullish-passthrough.

## Proposed solution

Add a guard at the top: if input is nullish, return `null`. Matches the
pattern already used in `src/parse.ts`.

## Test results

Added 2 unit tests covering null + undefined input. Full suite green.

Closes #42.

## Test results

```
PASS  src/__tests__/format.test.ts (2 added)
Tests: 78 passed, 78 total
Duration: 1.2s
```
```

---

## How agents populate sections

| Agent | Populates | When |
|---|---|---|
| `@scout` | `discovered_at`, frontmatter, `# <title>`, `## Why scout flagged this` | first discovery |
| `@researcher` | `research_path` link only — body untouched | when building/refreshing the dossier |
| `@repo-analyzer` | `## Scope`, `## Files to touch` | qualification |
| `@draft-writer` | `## Claim comment draft`, `## PR title`, `## PR body`, `## Issue body draft`, `## Review draft` | claim / submit / review |
| `@test-runner` | `## Test results` | working |
| user | any section | any time — manual edits survive refresh |

`transition.sh` updates frontmatter only (status, pr_number, last_refreshed).
It never writes to the body.

---

## What backfilling looks like

When a PR exists upstream but no candidate file ever tracked it, you can
backfill one with frontmatter + minimal body. Most B/C-phase gates will
SKIP rather than BLOCK because the body sections aren't present — that's
correct behavior. Once the PR merges, the candidate becomes a `merged`
record for the failure log / institutional memory.

A backfill template:

```markdown
---
discovered_at: <PR createdAt>
repo: <owner>/<repo>
issue_number: <linked issue # or PR #>
issue_url: <PR url>
star_tier: <derived from star_count>
star_count: <gh repo view ... .stargazerCount>
repo_lang: <gh repo view ... .primaryLanguage.name>
competing_prs: 0
primary_label: backfill
scout_score: 0.7
status: submitted
pr_number: <PR #>
pr_url: <PR url>
branch: <gh pr view ... .headRefName>
research_path: <absolute dossier path>
backfilled_at: <now ISO8601>
last_refreshed: <now ISO8601>
---

# <repo> #<PR#> — <title>

## Why this candidate exists

Backfilled into the lifecycle workflow on <date>. Pre-dates the candidate
system being wired up; created so reconciliation can pick up state changes
when the PR merges or closes.

## Source

- PR: <url>
- Branch: `<branch>`
- Linked issue: <issue # or "(none)">
```

---

## Cross-references

- Lifecycle workflow: `000-docs/006-AT-SPEC-lifecycle-workflow.md`
- Gate inventory: `000-docs/005-AT-SPEC-gate-inventory.md`
- `agents/draft-writer.md` — agent that populates `## PR body` etc.
- `agents/test-runner.md` — agent that populates `## Test results`
- `scripts/transition.sh` — updates frontmatter atomically
- `scripts/gates/lib/preamble.sh` — gates' shared helpers for reading sections
