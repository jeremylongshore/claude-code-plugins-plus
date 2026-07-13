# Workflow Guide — long-form

## Table of Contents

1. [Daily rhythm](#daily-rhythm)
2. [The 5-step workflow in depth](#the-5-step-workflow-in-depth)
3. [Project-specific gotchas](#project-specific-gotchas)
4. [Tracker hygiene](#tracker-hygiene)
5. [Money & payment programs](#money--payment-programs)

---

## Daily rhythm

The first thing the skill does on invoke is Step 0 (refresh state). After that, the natural conversation follows whatever the user is actually trying to do — review status, scout new work, qualify a candidate, draft a submission. The 5-step DISCOVER → QUALIFY → CLAIM → WORK → SUBMIT framing is the long form; most days touch only one or two steps.

| Time of day | Typical action |
|-------------|----------------|
| Morning | Step 0 (state summary) → reconcile any drift |
| Mid-morning | Step 1 (discover) if queue is thin |
| Workblocks | Step 4 (work) on whatever's claimed |
| End of day | Step 5 (draft submission) for tomorrow's review |

## The 5-step workflow in depth

### 1. DISCOVER — finding paid issues

Three sources, in priority order:

**Tracker (already-curated)** — `bounties` table rows where status is `open`, `qualified`, or `drafting`. These have already passed a competition / staleness check and represent the user's vetted queue.

**Live GitHub label search** — anything labeled `bounty`, `💰 Bounty`, or repo-specific bounty labels in the tracked orgs. New every day; needs qualifying before it's actionable.

**Algora boards** — browse-only via web. Their public API needs auth and the rate limits make it not worth scripting. The boards to know:

| Org | Stack | Reward range |
|-----|-------|--------------|
| mediar-ai (screenpipe) | Rust + TS/Bun | $25–500 |
| tscircuit | React/PCB | $25–150 |
| golemcloud | Rust/WASM | up to $3.5K |
| calcom | TS/Next.js | $20–500 |
| twentyhq | TS | varies |
| formbricks | TS | varies |
| trigger-dev | TS | varies |

**Gumroad** — single tracking issue at `antiwork/gumroad#1055`. Lists all active SCSS-to-Tailwind file conversions. $1.5K per file.

### 2. QUALIFY — eligibility + competition + responsiveness

Three things to check, fast:

**Competition** — `gh pr list --repo <owner>/<repo> --search "<issue#>" --state=all`. If 2+ open PRs already, skip. If one open PR is stale (>14 days no activity), the issue may free up — note and revisit.

**Maintainer responsiveness** — `gh api repos/<owner>/<repo>/commits` for recent activity dates. No commit in 60 days = likely abandoned. Avg PR merge lag from `gh pr list --state=closed --limit 10 --json mergedAt,createdAt` gives a sense of how long submissions sit.

**Friction** — does the repo require a CLA? Does CONTRIBUTING.md ask for design docs / RFCs before code? Is there a PR template that asks for AI disclosure? All of these are fine, but they affect the time-to-merge math.

### 3. CLAIM — staking the work

Most upstreams accept a plain comment ("hey, I'd like to take this on, plan is X, ETA Y"). Algora-managed issues use Algora's `/bounty` slash command on the issue itself. Some programs (Cortex specifically) require an AI disclosure phrase in the first comment.

After posting, update the tracker so Step 0 reflects the claim. Forgetting this is the #1 source of tracker drift.

### 4. WORK — actually doing the thing

Work happens in the upstream clone under `~/000-projects/contributing-clanker/<repo>/`. Each clone has its own `CLAUDE.md` with stack-specific commands and conventions.

The two non-obvious rules:

- **Don't push to forks until tests pass locally.** Pushing then force-pushing is noisy and wastes CI cycles.
- **Match the upstream's tone.** screenpipe is lowercase; calcom is sentence case; PostHog is sentence case ("Product analytics" not "Product Analytics"). The maintainer notices.

### 5. SUBMIT — design issue first, PR after approval

The repo's `CLAUDE.md` says it explicitly: auto-opening PRs creates whack-a-mole slopfests. Open a Design Issue with diff preview + test results, wait for the maintainer to approve the approach, *then* open a PR.

The exception: if the upstream's CONTRIBUTING.md explicitly asks for direct PRs (some repos prefer this for small fixes), follow their convention.

## Project-specific gotchas

### screenpipe

- Two test suites: `cargo test` for the Rust core, `bun test` for the Tauri app. Both must pass.
- Lowercase logging and UI text — match the existing codebase tone.
- No toast errors — use empty states / skeletons / inline errors instead.
- `@ts-ignore` comments are intentional; don't remove them.
- Escape HTML properly in JSX (`&apos;` etc. inside string attributes).

### cortex

- CLA required before first PR — sign at the link in `cortex/CLA.md`.
- Demo video required (before/after for bugs, feature demo for new work).
- AI disclosure phrase required in the PR body.
- Tests with >80% coverage (their bar, not optional).
- No force-push — merge commits only.

### posthog

- ALWAYS wrap commands in `flox activate -- bash -c "..."`. Running pytest directly will fail.
- Type hints required in Python.
- No mypy (they ditched it for being too slow).
- Tailwind preferred over inline styles.
- Avoid direct `dayjs` imports — use `lib/dayjs`.
- Conventional commits: `feat(scope):`, `fix(scope):`, lowercase, no period.

### calcom / cal-com

- Two clones in the workspace. Prefer `calcom/` (newer).
- yarn workspaces — run from the monorepo root, not subpackage.

### vertex-ai-samples (Google)

- CLA required at https://cla.developers.google.com/
- One notebook per PR.
- Lint via Docker: `docker run -v ${PWD}:/setup/app gcr.io/cloud-devrel-public-resources/notebook_linter:latest <notebook>.ipynb`

### zio-blocks

- Scala 3, pure FP, sbt.
- `sbt scalafmtCheckAll` is part of the gate.
- Schema migrations have $2-4K rewards — biggest individual paydays in the workspace.

### feishin

- Electron + React + pnpm.
- ESLint + Stylelint both run.

### gumroad

- $1,500 per SCSS file converted to Tailwind.
- Email `bounties@antiwork.com` with PR link + payment email after merge.
- Stripe payout (bank, PayPal, crypto).
- Issue `#1055` is the index of available files.

## Tracker hygiene

The tracker only stays useful if its status reflects reality. Two operations keep it honest:

**Reconcile** — for every row with a `pr_number`, check the live PR state via `gh pr view`. Update the row's `status` to `completed` (merged), `cancelled` (closed-not-merged), or `submitted` (open). Do this at least weekly, or after any "mass push" day.

**Re-import from CSV** — the canonical CSV at `~/000-projects/contributing-clanker/000-docs/002-PM-BKLG-contribution-tracker.csv` is the human-edited backlog. If the CSV gets new rows (manual additions), re-run the importer to land them in SQLite. Idempotent — existing IDs are skipped.

## Money & payment programs

| Program | Payment mechanism | Speed |
|---------|------------------|-------|
| Algora | Platform handles automatically (120+ countries) | Days |
| Gumroad | Email `bounties@antiwork.com` post-merge, Stripe payout | ~1 week |
| Cortex | Bitcoin (preferred), USDC, or PayPal | <48 hours |
| Tscircuit / Golem / others on Algora | Same as Algora | Days |
| Ad-hoc GitHub bounty (no platform) | Negotiated case-by-case | Variable |

The local `001-BL-TRCK-payment-tracker.md` doc tracks paid vs pending across all programs. After a payment lands, update both that doc AND the `bounties.payment_status` column.
