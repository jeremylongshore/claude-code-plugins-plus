---
title: "Exit 0 Is Not Success: Automation Assurance That Verifies Outcomes"
description: "A green exit code can hide a dead job. Intent-OS automation assurance treats outcome verification as the success criterion, not exit 0."
date: "2026-07-14"
tags: ["automation", "devops", "observability", "ci-cd", "architecture", "testing"]
featured: false
---
A cron that exits zero and produces nothing is not healthy. It is a silent failure wearing a green badge.

That distinction drove most of 2026-07-14 on Intent-OS. Phase-2 landed a stack of fail-closed controls, and the load-bearing one for operations was **automation execution assurance**: a registry, an engine, and active drills that refuse to treat "process finished cleanly" as "the work got done."

## The lie exit codes tell

Schedulers are good at answering a narrow question: *did the process start and did it return 0?*

They are bad at the question operators actually care about:

- Did the backup finish with a restorable artifact?
- Did the heartbeat file get a fresh timestamp?
- Did the export write the expected tables, not an empty stub?
- Did the watchdog that was supposed to catch all of the above still run?

If your only gate is the process exit code, every one of those can fail while the dashboard stays green. We already ship that lesson in other forms ([empty data that passed as clean](/posts/empty-is-not-clean/), [liveness without health](/posts/liveness-without-health-is-theater/), [gates that fail open](/posts/every-safety-gate-has-a-failure-direction/)). Automation was the next place the same shape showed up.

## What we shipped: independent outcome verification

**PR I** on Intent-OS (`feat(automation): execution assurance`) makes the rule explicit:

> An exit code of 0 is **not** business success.

The design is deliberately boring and mechanical:

1. **`registry.json`** lists each automation's full lifecycle policy: schedule, lateness, max runtime, heartbeat, retry/backoff, catch-up, overlap, idempotency, expected output, **outcome verification**, owner, and runbook.
2. **`assure.py`** runs a fail-closed status ladder. A completed exit-0 run is classified `exit0-no-outcome` unless an independent check verifies the expected output.
3. **Watchdog + watchdog-of-watchdog**: catching dead jobs is not enough if the catcher itself dies. Escalation covers the uncovered gap.
4. **`drills.sh`** injects the minimum failure set on disposable/synthetic targets and asserts detect → receipt → recover.

The first-run scorecard for 2026-07-14 recorded **34 predicates, 0 failures**, including a real process kill (stuck heartbeat), a real exit-0 with no output (`exit0-no-outcome`), timer disabled, scheduler unavailable, credential missing, stale output, and watchdog failure. The scorecard field that matters for humans is simple: `no_false_green=True`. Exit-0 is healthy only with a verified outcome.

That is the same discipline as two-marker liveness on the blog fleet (`.beat` vs `.ok`): *ran* is not *succeeded*. The automation package just names the failure modes and drills them.

## Why not trust the job?

The tempting alternative is "the job already knows if it failed; just check its exit code harder." That collapses three different things into one bit:

| Signal | What it proves | What it hides |
|--------|----------------|---------------|
| Process started | Scheduler fired | Outcome quality |
| Exit 0 | No crash path | Empty success, skipped body, wrong target |
| Heartbeat fresh | Something is looping | Correct work product |
| Outcome check | Expected artifact exists and is plausible | (this is the bar) |

Independent verification is not cynicism about the job author. It is an admission that the success path is where silent failure hides. Crashes are loud. Empty green is quiet.

We also fixed a `kill 0` process-group hazard in the drill trap while we were there: drills that accidentally widen their blast radius are worse than no drills. Disposable targets only; no production automation was touched in the first-run pack.

## Fail-closed neighbors on the same day

Assurance did not land alone. The Phase-2 foundation batch on Intent-OS put the same fail-closed posture in several adjacent places:

- **Disclosure policy (PR A / C8):** canonical fail-closed enforcement at every sink. The irreversible control is the one that refuses to emit when the policy cannot be evaluated cleanly.
- **Observability failure-detection spine (PR H):** registry + engine + disposable drills for detection, not just dashboards.
- **Agent gateway (PR J):** narrow tools, default-deny, signed receipts. Governed agentic ops with an allowlist, not an open shell.
- **Alert floor (PR C):** one authoritative source plus drift enforcement so routing cannot silently rot.
- **Watchtower scan-gate (PR D):** resolve + scan + gate before promote.
- **Supply-chain CI baseline (PR G):** normalize + policy gate + schemas.

The audit trail for the day closed with a Phase-2 re-audit after D88 residuals: conformant with explicit gaps, not "green because we stopped looking."

## Also shipped

**claude-code-plugins / Freshie inventory.** Several production-truth fixes: refuse to export incomplete discovery runs to Dolt; gate public exports behind a table allowlist; stop `--fix-agents` from stripping required color; floor curated wipes; propagate `populate-db` failures; harden external-sync supply chain after an ops review. Incomplete data no longer pretends it is a finished inventory snapshot.

**DiagnosticPro.** Instrument-grade frontend redesign (less template, quieter nav), real Open Graph images, whiteglove PDF customer reports, and live e2e journeys with free-coupon seed cases. Public surface stopped looking like a stock SaaS shell.

**Bob's Big Brain rename.** Umbrella and plugin directories aligned to `bobs-big-brain-*` on disk and remote; skill docs tighten the search ladder (keywords first, then wider scope) and marketplace author schema so install stops failing on a CLI type check.

**Blog pipeline (this site).** Hard ban on em dashes and AI-slop phrases via `lint-post-voice.py`, skill write rules, and a land-step gate. Phrase checks mask fenced code and URLs so repo names do not false-positive. That work merged after the dirty-tree preflight story below, but the lesson matches the day: soft style guidance without a hard gate is theater.

## The dirty-tree lesson (same failure shape)

This post itself almost did not exist. The 04:00 backfill aborted because `.beads/interactions.jsonl` had one uncommitted line from a late bead close. Preflight correctly refused a dirty `master`. The content pipeline never ran.

That is `exit0-no-outcome` in human form: the machine "did something" (bd wrote a log line), then left the system in a state where the real job (publish a post) could not start. Fix was twofold: commit the audit line, and teach preflight to auto-commit **only** when interactions.jsonl is the sole tracked dirt. Any other dirt still fails closed.

## What is still honest ABSENT

Automation assurance is proven on disposable drills. Wiring live schedulers (systemd, cron, GitHub Actions receipts, borg/R2 lifecycle, the real `ops/verify` stream) as observation sources, and deploying the off-host watchdog-of-watchdog, is still change-control-gated production work. Shipping the engine without claiming the fleet is fully under it is part of the same honesty rule: do not paint partial coverage as complete.

## Takeaway

If your automation dashboard only counts exit codes, you are measuring crashes, not success. Put the success criterion in a separate check of the artifact you actually needed. Drill the failure modes on disposable targets until `no_false_green` is true. Then wire production under change control.

Exit 0 means the process finished. Outcome verification means the work finished. Only one of those is worth a green light.

## Related Posts

- [Empty Is Not Clean: Five Fail-Open Bugs in an AI Agent](/posts/empty-is-not-clean/)
- [Liveness Without Health Is Theater](/posts/liveness-without-health-is-theater/)
- [Every Safety Gate Has a Failure Direction](/posts/every-safety-gate-has-a-failure-direction/)
