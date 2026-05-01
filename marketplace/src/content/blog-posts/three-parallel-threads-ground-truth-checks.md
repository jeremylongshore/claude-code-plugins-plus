---
title: "Three Parallel Threads: Ground Truth Checks"
description: "Three projects, one principle: stop and verify the ground truth before you commit."
date: "2026-04-25"
tags: ["claude-code", "testing", "ci-cd", "automation"]
featured: false
---
Friday stacked three parallel threads across the Braves Booth, CAD agent, and Intent Solutions landing site — three different codebases, three different problems. They had nothing in common except one operating principle that caught them all: ground truth checks before committing.

## Braves Booth: Wiring in a Beat Reporter

Lindsay Crosby (@crosbybaseball) is the Managing Editor of Braves Today and host of Locked On Braves. User asked to wire her X handle into the beat-reporter feed. Obvious move — add to `beat-reporters.json`, push. But first: verify she's not already in the system. Checked the RSS feeds. She was already pulling two-thirds of the way in through Braves Today and Locked On Braves — articles and podcast episodes both flowing. Her "Today's Three Things" posts hit postgame routing correctly via regex. The missing piece was the X handle, and only the X handle. Ground truth = she's nearly wired already; the add was surgical. Branched per safety rail, added the handle, one clean commit. Done right because we checked first.

## CAD AI Agent: Full Testing Harness Install

Started with PR #161 to retrofit the full L0–L7 test stack via `/implement-tests`. The easy path: run the skill, commit everything, PR it. But the actual work was ground truth checking. The codebase already had CodeQL in place. It already had some layer 1 hooks. It had opinions on what could run at PR time vs what had to be manual (mutmut, cron jobs budgeted against GitHub Actions minutes). CTO-mode decision-making meant reading the existing `security.yml` comments ("schedule disabled"), understanding customer constraints, and aligning new gates to what already existed. The result: 28 files across four stacked commits, PR #161, none of it contradicting live policy. Ground truth = understand what's already there, don't blind-add.

```toml
# From tests/TESTING.md — capturing the policy before adding gates
coverage_floor = 78
mutation_kill_rate = 0.72  # Manual mutmut only — no cron
ci_gates = ["CodeQL", "Trivy", "ESLint", "import-linter"]
no_schedule_triggers = true
```

## Intent Solutions Landing: Catching a Stale Branch Before the Fix

The landing site had a stale `feat/field-notes` branch. It predated four recent merges from Ope (PRs #12–#15, including a homepage redesign). Instinct was to rebase and fix the files. Ground truth check: what's actually on main right now? Fetched, found the redesign had already shipped. The branch was now structurally incompatible — it would collide on shared files and lose Ope's recent work. Stale branch means stale understanding. Decision: don't rebase the wreck. Fresh branch off main, port the 15 unique field-note posts that weren't there yet, fix against the live code, clean PR, close #11 as superseded. Ground truth = the repo moved while I wasn't looking; verify before rebuilding on an old assumption.

## One Operating Principle

All three hit the same wall: assumption without verification. The Crosby add could have been redundant. The testing harness could have contradicted live policy. The field-notes port could have undone recent work. Ground truth checks caught all three. Cost: a few extra minutes reading configs, checking JSON, syncing branches. Payoff: no wasted commits, no downstream conflicts, no "why did we redo something that was already done." Senior move: stop and check before you commit.

## Related Posts

- [Intent Solutions Testing SOP](/posts/testing-sop-layer-by-layer/): The harness policy in detail
- [Braves Booth: Real-Time Sports Data Pipeline](/posts/braves-booth-realtime-pipeline/): Full beat-reporter architecture
- [Stale Branch Recovery: Fresh Port Strategy](/posts/fresh-branch-port-recovery/): How to handle diverged branches

