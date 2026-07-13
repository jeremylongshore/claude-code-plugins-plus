---
name: contribute
description: |
  Local-only OSS contribution command center. Auto-refreshes the user's
  in-flight PR and issue state on invoke so conversations start with full
  context — no need to brief Claude on what's in flight. Helps the user
  find issues to contribute to on GitHub, builds per-repo dossiers of what
  each upstream expects (CLA, DCO, branch convention, AI policy, draft-first,
  review bots, issue templates), runs deterministic gates before any
  external action so AI-assisted contributions don't reach maintainers as
  slop. State is markdown-only: candidate files at
  ~/.contribute-system/candidates/, repo dossiers at
  ~/.contribute-system/research/, append-only event log at
  ~/.contribute-system/log.jsonl. No database, no cloud calls.
  Use when the user asks about their PRs / issues / contributions, wants to
  find new work to take on, claim an issue, build/refresh a repo's dossier,
  or draft a Design Issue or PR. Trigger with "/contribute", "what's my PR
  status", "find a contribution", "claim issue X", "draft a Design Issue
  for Y", "refresh dossier for Z".
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
  - Task
  - Bash(gh:*)
  - Bash(git:*)
  - Bash(node:*)
  - Bash(pnpm:*)
  - Bash(yarn:*)
  - Bash(npm:*)
  - Bash(cargo:*)
  - Bash(pytest:*)
  - Bash(python:*)
  - Bash(python3:*)
  - Bash(bash:*)
  - Bash(jq:*)
  - Bash(base64:*)
version: "4.0.0"
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
license: "MIT"
compatibility: "Designed for Claude Code; requires gh CLI and jq on PATH"
tags: [oss, contributions, github, contributing-clanker, ai-slop-prevention]
---

# Contribute Command Center

## Overview

Local-only OSS contribution workflow. The skill itself is the system — there is no separate CLI binary, dashboard, or cloud backend. State lives in three places:

1. **GitHub itself** — fetched live via `gh` for any PR/issue state question. Never cached long-term.
2. **Markdown candidate files** at `~/.contribute-system/candidates/<owner>__<repo>__issue<N>.md` — one per issue we're tracking. Frontmatter is the queryable layer (status, scout_score, repo, research_path, overrides). Body holds claim drafts, PR drafts, scope notes.
3. **Markdown repo dossiers** at `~/.contribute-system/research/<owner>__<repo>.md` — one per upstream repo we contribute to. Built by the `@researcher` subagent. Frontmatter is canonical for every gate (CLA, DCO, branch convention, AI policy, draft-first, review bots, issue templates). Body holds curated knowledge: pet peeves, failure log, free-form notes that survive refresh.
4. **Append-only event log** at `~/.contribute-system/log.jsonl` — every gate run, transition attempt, override, scout/researcher invocation lands here with a UTC timestamp. Filterable via `jq`.

Use this skill when the user wants to:

- Know what's in flight (open PRs, claimed issues, candidate queue)
- Find a new issue to contribute to on GitHub
- Build or refresh a per-repo dossier (delegates to `@researcher`)
- Run gate-checked transitions (claim, work, submit) — every external action passes through `transition.sh` first
- Draft a claim comment, Design Issue, or PR description (default: Design Issue, NOT a PR)
- Run an upstream repo's test suite

The pre-2026-04-30 version of the skill used a SQLite tracker (`~/.contribute-system/contribute.db`, 32 tables) plus a separate `contribute-system/` monorepo (Next.js dashboard, TS CLI, Cloud Functions). Both were deleted because they were never used in practice. The skill now reads markdown directly. That tradeoff is deliberate: human-readable, greppable, git-trackable, survives any tool, no daemon process.

## Prerequisites

- **`gh` CLI**, authenticated as the user (`gh auth status` should show "Logged in")
- **`jq`** on PATH (used by gates + log filtering)
- **Workspace** at `~/000-projects/contributing-clanker/` containing upstream clones (each clone has its own `CLAUDE.md` for project conventions)
- **Runtime state dir** at `~/.contribute-system/` — created on first scout/researcher run if missing

Run this DCI check at activation (output is auto-injected into the prompt):

```!
gh auth status >/dev/null 2>&1 && echo "gh: ok" || echo "gh: NOT logged in"
[ -d ~/.contribute-system/gates ] && echo "gates: $(ls ~/.contribute-system/gates/*.sh 2>/dev/null | wc -l) installed" || echo "gates: not yet installed"
[ -d ~/.contribute-system/candidates ] && echo "candidates: $(ls ~/.contribute-system/candidates/*.md 2>/dev/null | wc -l) tracked" || echo "candidates: empty"
[ -d ~/.contribute-system/research ] && echo "dossiers: $(ls ~/.contribute-system/research/*.md 2>/dev/null | wc -l) built" || echo "dossiers: empty"
[ -f ~/.contribute-system/profile.md ] && echo "profile: ok" || echo "profile: missing — edit ~/.contribute-system/profile.md"
[ -f ~/.contribute-system/log.jsonl ] && echo "log: $(wc -l < ~/.contribute-system/log.jsonl) events" || echo "log: empty"
```

## Instructions

### Step 0 — Refresh state (run first, every time)

Before answering anything contribution-related, surface current state. Run these in **parallel** with the Bash tool:

```bash
# Upstream PRs in flight (filtered to outside-org repos only —
# the system tracks contributions INTO repos the user does not own;
# own-repo PRs are out of scope and must be excluded).
#
# OWN_ORGS is the prefix list of repos to exclude. Update if the user
# adds a new org. (Discoverable via `gh api user/orgs --jq '.[].login'`
# plus the user's own login from `gh api user --jq '.login'`.)
OWN_ORGS='jeremylongshore/ intent-solutions-io/'
gh search prs --author=@me --state=open --limit=50 \
  --json number,title,url,repository,isDraft,createdAt | \
  jq --arg own "$OWN_ORGS" '
    ($own | split(" ")) as $excl |
    map(select(.repository.nameWithOwner as $r |
               ($excl | map(. as $p | $r | startswith($p)) | any) | not))
  '

# Recently-merged + closed upstream PRs (last 30, same scope filter)
gh search prs --author=@me --state=closed --limit=30 \
  --json number,title,url,repository,closedAt,createdAt | \
  jq --arg own "$OWN_ORGS" '
    ($own | split(" ")) as $excl |
    map(select(.repository.nameWithOwner as $r |
               ($excl | map(. as $p | $r | startswith($p)) | any) | not))
  '

# Local candidate tracker — markdown frontmatter is the queryable layer.
# Candidates are upstream-only by construction (scout never enqueues
# own-repo issues), so no scope filter needed here.
for f in ~/.contribute-system/candidates/*.md; do
  awk -v f="$(basename "$f" .md)" '
    /^---$/ { fm = !fm ? 1 : 2; next }
    fm == 1 && /^(repo|issue_number|status|scout_score|research_path|pr_number):/ { print f, $0 }
  ' "$f"
done 2>/dev/null

# Recent activity from the event log
tail -50 ~/.contribute-system/log.jsonl 2>/dev/null \
  | jq -c "select(.event | test(\"transition_|gate_|researcher_|scout_\"))" 2>/dev/null
```

**Scope rule (non-negotiable)**: this skill applies *only* to contributions made INTO repos the user does not own. Own-org PRs (`jeremylongshore/*`, `intent-solutions-io/*`) are out of scope — they are personal-project work, not anti-slop OSS contributions. The whole architecture (gates, dossiers, lifecycle) exists because upstream maintainers need protection from low-quality AI work; that concern doesn't apply to the user's own repos. If a candidate file ever references an own-org repo, it's a scout bug — flag it.

Then summarize for the user:

- N open / draft PRs (and any blocked on review)
- N candidates in `claimed` or `working` status but not yet `submitted`
- N candidates in `open` / `shortlist` status (sorted by `scout_score` desc)
- Any contradictions between `gh` (PR state) and the candidate's `status:` field (e.g., PR merged but candidate still says `submitted`) — flag for cleanup
- N candidates whose `research_path:` is empty or stale (>14d) — flag for `@researcher` build/refresh
- Recent events worth surfacing (gate BLOCKs, overrides, dossier refreshes)

Skip Step 0 only when the user asks about something unrelated to their own contributions.

### Step 0.5 — Ensure dossier exists for any repo we'll touch

Every repo we contribute to needs a dossier at
`~/.contribute-system/research/<owner>__<repo>.md` — that's where every gate
in `~/.contribute-system/gates/` reads its rules from (branch convention,
CLA/DCO, AI policy, draft-first preference, review bots, etc.).

Before any lifecycle transition (claim, work, submit) for a candidate at
repo `<owner>/<repo>`:

```bash
DOSSIER=~/.contribute-system/research/$(echo <owner>/<repo> | tr '/' '_').md
DOSSIER=${DOSSIER/__/__}    # ensure double underscore
if [[ ! -f "$DOSSIER" ]]; then
  echo "no dossier — invoking @researcher"
  # delegate to the researcher subagent
fi
# Also check staleness — refresh if >14 days old
LAST=$(awk '/^last_refreshed:/{print $2; exit}' "$DOSSIER")
if [[ -n "$LAST" ]]; then
  AGE_DAYS=$(( ( $(date +%s) - $(date -d "$LAST" +%s) ) / 86400 ))
  [[ "$AGE_DAYS" -gt 14 ]] && echo "stale ($AGE_DAYS d) — invoking @researcher refresh"
fi
```

Delegate dossier build/refresh to the **`@researcher`** subagent (defined
at `${CLAUDE_SKILL_DIR}/agents/researcher.md`). It runs in its own context window so
the verbose CONTRIBUTING.md fetch + depth-1 link follows stay out of your
main conversation. It writes the dossier to disk and reports back a
one-paragraph summary.

If the user already invoked `@researcher` earlier in the session for this
repo, skip — don't re-build.

### Step 1 — Discover

Find issues worth contributing to. Sources, in priority order:

- **Existing candidates** with `status: open` or `status: shortlist` already in `~/.contribute-system/candidates/` — already discovered + vetted, ranked by `scout_score:` frontmatter field
- **Fresh GitHub label searches** scoped to repos / languages in `~/.contribute-system/profile.md`: `gh search issues "label:'good first issue' state:open language:<lang>" --limit 50`

Delegate discovery to the **`@scout`** subagent (defined at `${CLAUDE_SKILL_DIR}/agents/scout.md`). It runs in its own context window so the verbose `gh search` output stays out of your main conversation. Pass it a mode: `baseline` (full per-tier sweep), `refresh` (re-evaluate existing candidates for momentum), or an ad-hoc query like "TypeScript repos at mainstream tier with no competing PRs." Scout writes ranked candidate markdown files to `~/.contribute-system/candidates/` and appends events to `~/.contribute-system/log.jsonl`. Summarize the top picks for the user from those files; do not re-run the search yourself.

### Step 2 — Qualify

Before claiming any issue, run these in parallel against the target repo:

```bash
gh pr list --repo <owner>/<repo> --search "<issue#>" --state=all
gh api repos/<owner>/<repo>/commits --jq '.[0:3] | map({date: .commit.author.date, msg: .commit.message[0:60]})'
gh api repos/<owner>/<repo>/contents/CONTRIBUTING.md --jq '.content' | base64 -d 2>/dev/null
```

Quick-reject signals:

- 2+ active PRs already on the issue
- Issue >90 days old with maintainer silence
- CLA required for trivial work
- Stack mismatch with the user's strengths

Use the bundled `agents/repo-analyzer.md` for the structured eligibility / CLA / rules check.

### Step 3 — Claim

Draft a claim comment from `assets/claim-template.md`. Adapt to the upstream's tone (lowercase if they use lowercase). Show the draft to the user for approval. Never `gh issue comment` autonomously.

**Gate-checked transitions** — before showing the claim draft to the user,
run the gate-runner via `transition.sh` to catch traps (already-assigned,
already-shipped, stale labels, AI-policy strikes, etc.):

```bash
~/.contribute-system/bin/transition.sh shortlist→claimed \
  ~/.contribute-system/candidates/<owner>__<repo>__issue<N>.md
```

If gates BLOCK, surface the blockers + fix hints to the user. They can fix
the underlying issue, pick a different candidate, or use
`--override-gate <ID> "reason"` if they have a specific justification (the
reason is logged to `~/.contribute-system/log.jsonl`).

After the user posts the claim and gates pass, the candidate's `status:`
field is bumped automatically by `transition.sh` (atomic write). No manual
SQLite update needed — the markdown candidate file IS the tracker.

### Step 4 — Work

Each clone in `~/000-projects/contributing-clanker/` has its own `CLAUDE.md`. Read it first. Run the project's native test suite — common patterns:

| Stack | Run |
|-------|-----|
| Node + pnpm | `pnpm install && pnpm test && pnpm typecheck && pnpm lint` |
| Node + yarn | `yarn install && yarn test` |
| Python | `pytest -v` (or `flox activate -- bash -c "pytest -v"` for posthog) |
| Rust | `cargo build && cargo test && cargo clippy --all-targets` |
| Scala | `sbt compile && sbt test && sbt scalafmtCheckAll` |

Use `agents/test-runner.md` for the structured runner that tees output to `~/.contribute-system/test-logs/`.

### Step 5 — Submit

**Default to a Design Issue, not a PR.** Auto-opening PRs creates "whack-a-mole slopfests" for maintainers (per the repo's `CLAUDE.md` philosophy).

Order:

1. Open a Design Issue using `assets/pr-template.md` reshaped for an issue body — include problem, proposed solution, diff preview, test results
2. Wait for maintainer approval of the approach
3. Open the PR using `assets/pr-template.md`

Use `agents/draft-writer.md` for the body drafter. Always show the draft to the user for approval before posting.

**Gate-checked submission** — before opening the PR / Design Issue, run:

```bash
~/.contribute-system/bin/transition.sh working→submitted \
  ~/.contribute-system/candidates/<owner>__<repo>__issue<N>.md
```

This runs phase B (pre-PR), C (PR submission), E (identity), F (legal),
and G (infrastructure) gates against the local diff + dossier rules. BLOCK
gates refuse the transition; WARN gates surface in the briefing for the
user to acknowledge before proceeding.

After successful submission, `transition.sh` bumps the candidate's
`status:` to `submitted` atomically. Manually add the PR number to the
candidate's frontmatter:

```bash
# After PR is opened
sed -i "s/^pr_number:.*/pr_number: <num>/; s|^pr_url:.*|pr_url: <url>|" \
  ~/.contribute-system/candidates/<owner>__<repo>__issue<N>.md
```

### Reconciliation

Periodically (or on user request "reconcile candidates"), check candidates with a `pr_number:` field against live GitHub state:

```bash
for f in ~/.contribute-system/candidates/*.md; do
  PR=$(awk '/^pr_number:/{print $2; exit}' "$f")
  REPO=$(awk '/^repo:/{print $2; exit}' "$f")
  [[ -z "$PR" || "$PR" == "null" ]] && continue
  gh pr view "$PR" --repo "$REPO" --json state,merged,closedAt
done
```

For each candidate whose actual PR state has moved on:

- PR merged → set `status: merged` in the candidate (atomic write)
- PR closed unmerged → set `status: dropped` and append a row to the dossier's `## Failure log` section so we learn from it
- PR still open → no change (`status: submitted`)

### Mandatory: human approval before external submission

Copied verbatim from the repo's `CLAUDE.md`:

> Before submitting ANYTHING to external repos:
>
> 1. Run all tests — ALL must pass
> 2. Run project-specific linters — no errors
> 3. ASK JEREMY FOR APPROVAL with test summary, file list, proposed body
> 4. Default to Design Issue, NOT a PR
>
> NEVER auto-submit PRs. NEVER bypass human approval. Design issues > PRs.

## Output

After Step 0, output a status block. After each subsequent step, output structured progress.

### State summary (after Step 0)

```
PRs in flight: <N> open, <M> draft
  - <repo>#<num>: <title> (state, age)
  ...

Claimed but not submitted: <N>
  - <id>: <repo>#<issue> ($value)
  ...

Tracked opportunities: <N> (top 5 by value)
  - <id>: <repo>#<issue> ($value, <competition flag>)
  ...

Drift: <N> rows where tracker disagrees with GitHub
  - <id>: tracker says <X>, gh says <Y> — suggest <Z>
```

### Per-step output

| Step | Output |
|------|--------|
| Discover | Three sections: Tracker queue / Fresh GitHub / Algora URLs. Top 3 picks highlighted. |
| Qualify | Verdict block: `claim` / `wait` / `skip` with one-sentence reason |
| Claim | Markdown draft of the comment, with placeholders filled. Awaits user approval. |
| Work | Test summary: pass/fail counts, duration, coverage %, log path |
| Submit | Markdown draft of the PR or Design Issue body. Awaits user approval. |

### Audit subcommands

When the user asks "what gates am I overriding most?" or "audit my contribution
history" or "show me override frequency":

```bash
${CLAUDE_SKILL_DIR}/scripts/audit-overrides.sh                       # all-time
${CLAUDE_SKILL_DIR}/scripts/audit-overrides.sh --since=30             # last 30 days
${CLAUDE_SKILL_DIR}/scripts/audit-overrides.sh --scope=org:posthog    # one org
${CLAUDE_SKILL_DIR}/scripts/audit-overrides.sh --gate=A05             # one gate
${CLAUDE_SKILL_DIR}/scripts/audit-overrides.sh --json                 # JSON
```

Output is a per-gate table with `[overrides, blocks, override_rate, top_reason]`,
sorted by override_rate desc. Gates overridden ≥50% of the time get flagged for
investigation — either the gate is too strict (false-positive heavy) or it's
catching real risk that's being consistently dismissed. Either way, surface it.

## Error Handling

| Symptom | Likely cause | Recovery |
|---------|--------------|----------|
| `gh: not logged in` | OAuth expired | Tell user to run `gh auth login` |
| `jq: command not found` | Missing on PATH | `apt-get install jq` (or equivalent) |
| `~/.contribute-system/` missing | First-time setup | `mkdir -p ~/.contribute-system/{candidates,research,gates,bin,check-runs}; touch ~/.contribute-system/log.jsonl` |
| `gh search` returns 0 results unexpectedly | Rate limit or wrong scope | Wait 60s and retry; check `gh auth status` token scopes |
| Candidate's `status: submitted` but PR is merged | Reconciliation drift | Run reconciliation step (above) |
| User asks to claim, but competing PR exists | Risk | Surface the competing PR explicitly; gate `A2 already-shipped` will BLOCK if it's a merged dupe |
| Test suite hangs (e.g., posthog without flox) | Wrong env | Wrap in `flox activate -- bash -c "..."` for flox-managed repos |
| `gh issue comment` permission denied | Repo private or token missing scope | Show the comment text to the user; they post manually |
| Gate run BLOCKs unexpectedly | Stale dossier or wrong rule | `@researcher refresh <owner>/<repo>`; if the rule itself is wrong, edit the dossier (manual sections survive refresh) or override with `transition.sh ... --override-gate <ID> "reason"` |
| Dossier missing for a candidate's repo | First time touching this repo | `@researcher build <owner>/<repo>` (auto-invoked by Step 0.5 anyway) |

If any external submission would happen without human approval, **stop and ask**. This is non-negotiable.

## Examples

### Example 1: "What's my PR status?"

User invokes `/contribute` or asks "what's in flight?"

1. Run Step 0 (parallel `gh pr list` + `gh issue list` + candidate-frontmatter scan + recent log events)
2. Output the State Summary block
3. Stop. The user can drill into any PR with a follow-up question.

### Example 2: "Find me a new contribution to work on"

User asks "what should I work on next?" or "scout opportunities."

1. Run Step 0 first (state summary)
2. Delegate to `@scout` (the user-scope subagent at `${CLAUDE_SKILL_DIR}/agents/scout.md`)
3. Output Tracker / Fresh GitHub / Algora sections, top 3 highlighted
4. Optional: per top pick, run Step 2 (Qualify) to surface CLA / competing-PR signals

### Example 3: "Draft a claim for screenpipe#1234"

User asks to claim a specific issue.

1. Run Step 2 (Qualify) on `mediar-ai/screenpipe#1234`
2. If verdict is `claim`, read `assets/claim-template.md`
3. Fill placeholders (approach in 1-2 bullets, ETA, CLA status)
4. Show draft to user
5. On user approval, post via `gh issue comment` AND update tracker (Step 3 SQL)

### Example 4: "Reconcile the tracker"

User asks to sync local state with GitHub.

1. Read all tracker rows where `pr_number IS NOT NULL`
2. For each, run `gh pr view <repo> <pr_number> --json state,merged`
3. Update tracker rows whose status disagrees with GitHub state
4. Output a diff summary: N rows updated, M unchanged

### Example 5: "Run tests on cortex"

User asks to verify a working branch.

1. Read `agents/test-runner.md`
2. Detect cortex stack (Python + pyproject.toml)
3. `cd ~/000-projects/contributing-clanker/cortex && pytest -v 2>&1 | tee ~/.contribute-system/test-logs/$(date +%Y%m%d-%H%M%S)-cortex.log`
4. Output test summary block (pass/fail counts, log path)

## Resources

### Bundled subagents (load with `Read agents/<name>.md`)

- `@scout` (user-scope subagent at `${CLAUDE_SKILL_DIR}/agents/scout.md`) — discovery sweep, GitHub-only, ranked by star-tier brackets. Each candidate it writes carries a `research_path:` frontmatter field pointing at the matching dossier (or empty if not yet built).
- `@researcher` (user-scope subagent at `${CLAUDE_SKILL_DIR}/agents/researcher.md`) — build / refresh the per-repo dossier at `~/.contribute-system/research/<owner>__<repo>.md`. Auto-invoked when a candidate's dossier is missing or older than 14 days.
- `agents/repo-analyzer.md` — DEPRECATED. Most of its function is now in the dossier system. Keep until Slice 3 retires it.
- `agents/draft-writer.md` — draft a Design Issue or PR body from a working branch's diff
- `agents/test-runner.md` — detect upstream stack and run the native test suite, log to disk

### Bundled templates (read for fill-in)

- `assets/claim-template.md` — issue claim comment
- `assets/pr-template.md` — PR description structure
- `assets/evidence-template.md` — test/lint evidence summary block

### References

- `references/workflow-guide.md` — long-form narrative of the 5-step workflow with project-specific gotchas

### External

- [Anthropic Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- The repo's own `CLAUDE.md` at `~/000-projects/contributing-clanker/CLAUDE.md` for project conventions and per-clone build commands

## Old patterns (deprecated, do not reintroduce)

- The pre-2026-04-30 skill referenced a `contribute` CLI binary, EV scoring, judge gates, slack notifications, asciinema work-session recording, evidence bundles, and competition risk scoring. The underlying `contribute-system/` monorepo was deleted because it was never used.
- The pre-2026-05-03 skill used a SQLite tracker at `~/.contribute-system/contribute.db` (32 tables, `bounties`-keyed schema) plus an Algora/Gumroad/Cortex bounty-board framing. That DB was wiped; the framing is gone. The system is now markdown-only: candidate files + dossiers + JSONL event log. **The skill is a contribution tool — not a tracker, not a payouts system, not a portfolio**.

If a feature from those eras is wanted back, recover code from `git log` in `~/000-projects/contributing-clanker/`. The bar to re-add is "Jeremy actually uses it daily."
