---
title: "Six Systems Reporting Nothing"
description: "When the reporter cannot report. A health check that lied, a ledger with no writer, and a lint gate that ran on nothing. Six systems, same defect class."
date: "2026-08-12"
tags: ["debugging", "monitoring", "testing", "architecture"]
featured: false
canonical: "https://startaitools.com/posts/the-status-nothing-could-write-to/"
---
Spent the day fixing six systems where the instrumentation meant to report trouble had no way to report it.

## braves: the wedged poller behind a blind health check

A single-flight latch gates the MLB stats poller. If a poll request hangs inside the statsapi proxy tunnel, the latch stays held. Every 5-second tick logs "skipped, previous poll in flight". For 6.2 hours, that was all it did. scorecardecho.com served stale innings the entire time.

The health check computed status from a consecutive-failure counter. That counter only increments when a poll actually runs. A wedged poller froze the counter at zero. So health reported fully green through the entire outage because nobody was watching the latch itself, only the count.

This was not the first swing at this problem. Commit 837939c raised the request timeout. Commit 881ac0d corrected the failure accounting (it was firing 8 times a minute behind a green check). Both missed.

Production was actually restored ahead of any code change by restarting the wedged container, because the latch is in-memory and a restart is the only clearing action. Health went degraded to ok, consecutive failures 5 to 0.

Fixed it by adding a wall-clock watchdog. If the latch is held past MAX_POLL_LIFETIME_MS (3x the request timeout, so only a poll that has stopped being a poll can trip it), force-release it, count the release, and poll again. Also put `stuckLatchReleases` and `pollLatchHeldMs` on the liveness payload, since a self-healing poller that heals silently is its own kind of blind spot.

The alternative was bounding the body read inside fetchJson, which is closer to the actual bug. Went with the watchdog in the poller instead, because the poller has to survive any dependency that never settles, and a fix at the HTTP layer only covers the one path I happen to know about. `reset()` did not clear the new state, and the tests caught the leak.

Health now asserts the latch state directly instead of trusting a counter that can't run. Four new tests: one reproduces the wedge, one proves the force-release, one proves health reads unhealthy while wedged with zero recorded failures, one proves a merely slow poll is left alone. Backend suite was 363 passed and 2 skipped. All green.

## blog-startaitools: 195 records nobody could write to

Every syndication surface row (39 posts times 5 surfaces) read `status: "pending"`. Not one had ever been flipped. Ezekiel posts manually from an email packet. No path reports the result back. "Pending" never meant "he didn't post." It meant nobody had ever written to the field.

The weekly team rollup handed that file to the model as context on what was posted. The model counted 195 pendings and correctly reported a backlog to the whole team. The model did its job. The input lied.

Built syndication-reconcile.py to age those records to `assumed_posted` with the standing instruction recorded as provenance. Deliberately NOT `posted` with invented timestamps, because that is fabricating receipts. Also stopped the rollup from asserting a work gap from a data gap.

Same morning, separate arc: four consecutive lint failures, each time reading as "I keep running the wrong subset of commands." The actual root cause was that `ruff` was not installed on this box at all. Whole class of check was invisible locally. Installed it through uv. Built lint-all.sh so "run exactly what CI runs" is one command.

## intent-os: health that cannot lie about stopped containers

Shipped B4.4 and B4.6 projections to the health schema. "Where a stopped container can never render healthy" and "where an absent or stale source can never render healthy." The schema now enforces both halves of the rollup: non-running implies never healthy AND mapped-alarm implies never healthy. Two new negative fixture witnesses (51 invalid fixtures, up from 50). Counts-sum check stays a renderer refusal; draft-07 JSON Schema cannot do cross-field arithmetic.

Also fixed findings from an independent code review. The file's docstring promised "never a crash", but os.path.isdir() returning true does not mean the directory is READABLE. A permission-denied registry raised PermissionError and produced zero bytes of JSON, the exact opposite of the structured refusal the file advertises to its agent consumers. Both listings are now guarded. Worth naming why it shipped: the existing failure drill was titled "an unreadable registry" but tested an absent path, and the docs-versus-reality walk took the title at face value. A drill's name is a claim like any other.

Two more findings from that same fix-up pass. The placeholder set matched "na", so an owner named "Na", a real given name, got reported as an unassigned-primary gap. A false gap is as bad as a false coverage number. And a validator verdict was reduced because without `--history-base` it silently skips its append-only-history rules, so `ok: true` meant less than the file claimed. It was a reduced verdict presented as a full one.

## intent-os decision-log/059: settling conflicted work-state

Adjudicated 29 standing work-state conflicts. All 29 carried the identical mechanical verdict, and that uniformity was the finding. It tells you which system to believe and nothing about what happened. Clustered into 3 root causes instead of 29 judgment calls. One epic worth recording: it was first sorted as settled on subtree evidence (7 children closed, 0 open), then moved on title-versus-scope. A fully closed subtree does not mean a finished epic. It can equally mean the remaining work has not been filed yet. Sorting on the subtree alone would have closed a live epic.

## claude-code-plugins: governance baseline drift

The Mission 01 baseline turned up that 200 of 343 files under 000-docs are ignored or untracked. That is a P1 governance finding that nobody could see because there was no baseline to compare against. Two false claims in CLAUDE.md were corrected against a measured baseline. The citation gate was fixed to key on the citer-citation pair rather than the target alone, and to stop scanning its own baseline and fixture strings as if they were errors.

Separately, a `workspace/` directory-level gitignore was hiding `workspace/lab/`, which is published teaching material linked from the root README and four Learning Lab pages on the marketplace site. Losing it 404s public links, and it had already been wiped once and needed a recovery in December 2025. The 18 tracked files survived only because git ignores ignore-rules for files that are already tracked, so any new lab file was being silently dropped. The fix is `workspace/*` plus the two negations. The `workspace/*` form rather than `workspace/` is load-bearing: a directory-level exclusion stops git descending, so no negation inside it can ever fire. That is the exact trap the same .gitignore already documents in its own 000-docs rules, and the first attempt at the fix walked straight into it.

## now-lms: upstream security commits with no tests

All four assigned upstream commits were already present in this fork, but none shipped with tests. The fork is 659 commits divergent, so every guarantee was enforced by nothing. Built nine new tests. Mutation-checked each one: revert the corresponding fix, re-run the suite, confirm the test actually fails. All four mutants were caught. Honest caveat, recorded in the commit: under the repo's current default fixtures those tests error at setup on a pre-existing `sqlite3.OperationalError`, the same way 32 of 32 related files do at baseline. They were verified against a file-backed database instead, and that harness was deliberately not committed.

A separate commit from the same pass fixed a path-traversal flaw by removing a duplicated `_validate_course_code` block. Two identical definitions meant only the second was ever live, so any edit to the first alone would have been dead code. The dedupe was a prerequisite for the new guard to run at all. The fork's stricter allowlist regex beat upstream on path separators but accepted "." and ".." because dots are inside the allowed character class, dropping half of upstream's intent. Impact was bounded because the realpath containment check still held, but it is the exact case upstream sanitized.

## intent-solutions-landing and intent-os volume

One commit to intent-solutions-landing: the previous day's field note dual-published into the field-notes section, which the land step does automatically.

Merged 15 PRs to intent-os in one day. The reason that was possible is worth naming: long-lived Monitor tasks watched the PR check lanes and merged on green across three review rounds, so the waiting was not mine to do.

## the collaboration shape and honest question

Claude Opus 5, Claude Sonnet 5, and Claude Fable 5 across six repos: intent-os (387 turns, 513 tool calls, 28 errors hit), claude-code-plugins (64 turns, 184 tool calls), blog-startaitools (56 turns, 146 tool calls). 47 failure-to-fix arcs across the day.

The honest arc was the ruff discovery. Four failures read as carelessness about which commands to run. The actual answer was that the tool was not installed at all, so that whole class of check could not run locally. Once installed through uv, the lint gate became a real gate. Then it caught the next defect before CI did.

That arc has the same shape as most of the rest of the day, which is either the finding or the problem. This frame keeps showing up here: four of the last two weeks' posts are some version of it, including yesterday's. At some point the honest question is whether it keeps recurring because it is a real defect class or because it is now the first thing I look for, and a day of six unrelated repos is exactly the sort of evidence that would look convincing either way. I do not have a way to tell yet.

## Related Posts

- [Every Fix Failed In The Shape Of The Bug](https://startaitools.com/posts/every-fix-failed-in-the-shape-of-the-bug/)
- [A Dead Socket Is Not A Dead Host](https://startaitools.com/posts/a-dead-socket-is-not-a-dead-host/)
- [Nothing Read It So Nothing Failed](https://startaitools.com/posts/nothing-read-it-so-nothing-failed/)
