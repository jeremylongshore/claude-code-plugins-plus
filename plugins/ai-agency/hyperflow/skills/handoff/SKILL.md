---
name: handoff
description: |
  Use when managing a two-session handoff — inspecting, picking up, or reviewing a committed handoff package produced by a session=two scope run. The operator interface over the cross-environment handoff lifecycle (plan in one session, build in another, review back in the first).
  Trigger with /hyperflow:handoff, "list handoffs", "pick up the handoff", "review the handoff build".
allowed-tools: Read, Write, Edit, Bash(git:*), Bash(mv:*), Glob, Grep, AskUserQuestion, Skill
argument-hint: "<list | status [slug] | pickup <slug> | review <slug> | complete <slug>>"
version: 1.0.1
license: MIT
compatibility: Designed for Claude Code; portable to Codex/OpenCode/Antigravity
tags: [handoff, two-session, cross-environment, orchestration]
---

# Handoff

Operator interface for **two-session execution**: one session plans (`session=two` at the Step 0 gate), a second
session in another environment builds, and the first session reviews. The lifecycle and package format are defined
in [`../hyperflow/session-handoff.md`](../hyperflow/session-handoff.md); this skill is the thin set of verbs over it
(mirrors how `/hyperflow:flush` fronts the deferred-commit machinery).

Packages live at `.hyperflow-handoff/<slug>/` (committed, so they travel via git). `STATUS` (`planned → built →
reviewed`) is the single source of truth and decides which side of the handoff you are on.

## Subcommands

### `list`
Read-only. List every `.hyperflow-handoff/*/` (excluding `.archive/`): slug · `STATUS` · `on_complete` · age. Group
by status so the user sees what is awaiting build vs awaiting review.

### `status [<slug>]`
Show the `HANDOFF.md` manifest + `STATUS` for one package (or all). When `STATUS=built`, also print the
`COMPLETION.md` diff range and commit count. Read-only.

### `pickup <slug>` — build side
Thin alias for starting the second-session build: invoke `Skill` with `skill: dispatch` and `args: "<slug>"`.
Dispatch's Step 1.0 rehydrates `artefact/` into `.hyperflow/`, runs `/hyperflow:scaffold` if the cache is missing,
builds the batches, writes `COMPLETION.md` + `STATUS=built`, and then deploys or stops per `on_complete`.

### `review <slug>` — planning side
1. Require `STATUS=built` (else: "handoff `<slug>` is `<status>` — nothing to review yet").
2. Read `COMPLETION.md` → extract `Diff range = <base>..<head>`.
3. Invoke `Skill` with `skill: audit` and `args: "<base>..<head> level=3"` (`level=5` when the originating triage
   flow in `HANDOFF.md` was `scientific` or `security`). The audit dispatches the matching domain specialist
   reviewers over the second session's diff.
4. On audit clean pass → fire the deploy gate (`AskUserQuestion` — `Run /hyperflow:deploy? Yes / No`, binary, no
   marker). On `NEEDS_FIX` → the audit fix-gate (`Yes` → `/hyperflow:plan` → `/hyperflow:dispatch`) handles it.
5. Set `STATUS=reviewed` once the review is accepted.

### `complete <slug>`
Mark the lifecycle done: set `STATUS=reviewed` (if not already) and archive the package to
`.hyperflow-handoff/.archive/<slug>/`. Commit `chore(handoff): archive <slug>`.

## Resolution

- Default `<slug>` = the most-recently-modified package when omitted from `status`/`pickup`/`review`.
- A package whose `STATUS=planned` is a **build-side** task (run `pickup`); `built` is a **review-side** task (run
  `review`). The session-start hook surfaces the right verb automatically.

## Iron rules

- **Never edit the build's commits.** `review` is read-only over the diff range; fixes flow through the audit
  fix-gate → scope → dispatch, never by amending the second session's commits.
- **Never force-push; never `--no-verify`.** Auto-push failures surface the exact `git push -u origin <branch>`.
- **No AI attribution** in any commit or package file.
- Honors `handoff.*` config (`autoPush`, `remote`, `packageDir`).

## Doctrine

Shared rules in [`../hyperflow/DOCTRINE.md`](../hyperflow/DOCTRINE.md). Package contract + templates in
[`../hyperflow/session-handoff.md`](../hyperflow/session-handoff.md).
