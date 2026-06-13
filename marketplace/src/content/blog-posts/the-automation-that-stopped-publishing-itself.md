---
title: "Nine Days Silent: When the Blog's Own Pipeline Stopped Publishing Itself"
description: "A 9-day publishing blackout went unnoticed because monitoring reported success while producing nothing. Git worktrees + orphan branches + timeout logs = silent failure at scale."
date: "2026-06-06"
tags: ["automation", "cron", "debugging", "ci-cd", "devops", "monitoring"]
featured: false
---
The blog you're reading publishes itself. Every morning at 7am, a local cron runs `claude -p /blog-backfill` on yesterday's work, classifies it into a content tier, writes the post, runs quality gates, and pushes to live. Monthly retrospectives and calibration reports run on the 1st. On 2026-06-06, the owner noticed posts missing from both startaitools.com and the syndicated copy on tonsofskills.com and asked: "why is the cross-posting not working?"

The answer was a compounding silent-failure chain that went undetected for nine days.

## The Immediate Trigger

That morning's 7am cron FATAL'd with a failure mode the previous hardening hadn't anticipated:

```
fatal: 'master' is already used by worktree at '.git/beads-worktrees/master'
```

The pre-flight normalized state by running `git checkout master`. But `master` was already checked out in a sibling git worktree (a beads worktree). You cannot check out the same branch in two worktrees at once. The checkout failed, the entire run died—before `claude -p` was ever invoked. No post got written. The LLM never even ran.

## The Root Poison

The real blockage started days earlier. The monthly retrospective cron TIMED OUT on 2026-06-01 (exit 124, wall-clock 1800 seconds). It wrote the retro file at 09:54, then died ~6 minutes later before committing and pushing. That left behind an orphan branch, `post/may-2026-monthly-retro`, gumming up every subsequent run. The monthly script had never received the pty-wrap treatment the daily script got, so the timeout log was opaque—no breadcrumbs.

Forensic accounting confirmed the damage:

- **Daily 7am:** FAILED 9 mornings straight (5/29 → 6/05). Pre-flight FATAL'd before the LLM ran.
- **Monthly retro (6/01):** TIMED OUT at exactly 1800s.
- **Monthly calibrate (6/01):** Non-zero exit, 0-byte report—AND it fired a "calibration done" notification at normal priority. False success: the monitor reported victory while producing nothing.

The meta-irony stung: the automation whose entire job is to publish blog posts silently failed to publish blog posts for nine days. The monitoring that should have screamed was quietly reporting success.

## The Fix

One PR landed it: "Worktree-aware cron pre-flight + pty wrap on monthly + consecutive-failure escalation" (287 insertions / 73 deletions, 4 files). The root insight: the bug was almost secondary. Nine days of breakage made no noise. So the fix is mostly about making failure loud.

A shared cron library (`lib-cron-common.sh`) sourced by all three wrappers. Previously each had independently-drifting pre-flight logic—only the daily ever got hardened. Now all three are unified.

Worktree-aware pre-flight: when `git checkout master` fails, it checks whether a sibling worktree holds `master` and pivots the cron into that worktree instead of dying.

```bash
if [ "$current_branch" != "$default_branch" ]; then
  if ! git checkout "$default_branch" >> "$log_file" 2>&1; then
    other_path=$(git worktree list --porcelain 2>/dev/null | awk -v b="refs/heads/$default_branch" '
      /^worktree / { wt=$2 }
      $0=="branch "b { print wt; exit }
    ')
    if [ -n "$other_path" ]; then
      cd "$other_path" && BLOG_DIR="$other_path"
    fi
  fi
fi
```

pty-wrap on the monthly scripts so a future timeout produces diagnosable logs. Timeout bumps where the old ceilings were too tight: the monthly retro from 1800s to a 60-minute (3600s) ceiling—it had hit the 1800s wall exactly—and calibrate from 300s to 900s. Fixed the false-success bug in calibrate: a near-zero-byte report alongside a zero exit is now treated as failure.

```bash
size=$(wc -c < "$REPORT" 2>/dev/null || echo 0)
if [ "$STATUS" = "OK" ] && [ "$size" -lt 100 ]; then
  STATUS="FAILED (empty report despite zero exit)"
fi
```

Consecutive-failure escalation: walks per-run logs and counts how many in a row failed. Raises alert priority once a streak forms. The smoke test returned 8/1/0—matching the forensic accounting exactly.

A dormant `slack_fail()` helper will post to `#cron-failures` once a webhook exists. Ship dormant, wire later.

Verification: shellcheck clean, `bash -n` passed 6/6, synthetic worktree-conflict correctly pivoted, CI green on 7 checks.

## Side Work

Merged a PR into agent-governance-plane, cut release v0.1.44, landed docs. Seeded three mental-model notes in learn-intentsolutions (Claude API, Bedrock, enterprise). A teammate got onboarded to production VPS. Routine sweep on intent-eval-platform.

The real lesson: monitoring silence is worse than monitoring noise. Nine days of breakage went dark because the signal path wasn't loud enough. Once you fix the code, fix the signal path. Then the next failure announces itself on day one.

## Related Posts

- [Five Tags, Zero Ships: How an Auto-Release Workflow Lied for a Whole Day](/posts/five-tags-zero-ships/)
- [Five Silent Failures in One Day](/posts/five-silent-failures-one-day/)
- [Ship Dormant, Wire Later — A Multi-Agent Slack Production Day](/posts/ship-dormant-wire-later-multi-agent-slack/)
