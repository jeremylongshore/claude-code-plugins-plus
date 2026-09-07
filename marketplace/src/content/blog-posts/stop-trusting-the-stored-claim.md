---
title: "When a Gate Should Re-Run the Step Instead of Trusting Its Receipt"
description: "Have the gate re-run a deterministic step instead of trusting its receipt. Why the lander heals the record itself, and why uncommitted makes it safe."
date: "2026-09-03"
tags: ["testing", "ci-cd", "architecture", "debugging", "verification"]
featured: false
canonical: "https://startaitools.com/posts/stop-trusting-the-stored-claim/"
---
## The blog pipeline receipt bug

The blog pipeline splits into two pieces: a producer and a lander. The producer runs the `/blog-backfill` skill, classifies the day's work into a tier (1: Field Note, 2: Deep-Dive, 3: Case Study), and writes a classification record to `decisions.jsonl`. Between producer and publisher sits a deterministic pattern engine. Step 2b of the producer runs the classifier's JSON through a learned-pattern applier that can cap the tier based on calibration rules learned from prior feedback. The engine stamps a receipt on the record proving it ran. This receipt is proof that step 2b executed and actually applied its logic.

The producer, being an LLM, sometimes just skipped step 2b. The lander then found a decision record with no pattern-engine receipt and quarantined the post. A post would sit uncommitted and unpublished, the pipeline unblocked for tomorrow but today's work lost. It was not even a failed build or a lint error. It was a silent discarding of work because a claim on the record (the engine ran and stamped a receipt) turned out to be false. Two manual recoveries had already cost time and frustration. At 18:49, the operator's course-correction was blunt: fix the receipt bug at the root, not the symptom. Do not ask the producer to promise harder. Make the lander not trust the promise.

The fix was not to re-prompt harder or add another layer of validation. The lander now self-heals. When it finds a record with no receipt, it runs the pattern engine itself over the uncommitted record, stamps the receipt, and proceeds. The gate then verifies the healed record the same way as any other. Why this is the root fix: the engine is deterministic, so there was never anything to trust the LLM about in the first place. Prompts drift. Code does not. The pattern engine will always produce the same result given the same input. The producer never needed to run it. The lander needed the receipt to know that it ran, but the lander can produce its own receipt.

The safety argument held in testing. The line the producer appends is still uncommitted at land time, so the lander can heal it in place without violating the append-only guarantee on `decisions.jsonl`. A scratch git repo proved both directions: an uncommitted receipt-less record heals, and the engine correctly downgraded a flat-threes test record from tier 2 to tier 1, proving the engine enforces rather than just stamps. An already-committed record is never rewritten (that would violate append-only) and still falls through to quarantine as before. That dual-direction proof mattered because it meant the fix was safe in both the happy path (heal and proceed) and the failure path (do not corrupt history).

First regression test failed with `AssertionError: embedded heal script not found`. The regex extraction missed the heredoc opener because that line carries `>> "$LOG" 2>&1` after it. Fixed the extraction regex to account for the redirect, then 165 tests passed. The same session purged DeepSeek and the Anthropic API key from the pipeline in favor of MiniMax M3, which the operator had already paid for a year of access. A j-rig evaluation then ran against M3 through j-rig's OpenAI-compatible escape hatch. The `pnpm build` for it failed once and was fixed with a frozen-lockfile install. Shipped as v1.17.6.

## Intent-longbox: three workstreams

Three distinct pieces landed in intent-longbox, across 36 commits.

The bead graph came first. A v2.0.0 blueprint specified 1 master initiative, 20 epics (E00 through E19), 202 executable beads and roughly 664 dependency edges with 7 release gates. The blueprint said materialize it in one graph-only pull request. The standing house rule says one epic at a time. That conflict got raised rather than guessed at, and the operator settled it: one epic at a time. No graph-only PR. Built that way, epic then children then edges then flush then verify, 223 mapped records total, with a validation pass afterward for counts, alias uniqueness, parent integrity, edge count, cycles and duplicates. Filed as docs 014 and 015. Pull request 9, checks green.

Two product fixes landed the same day. Truncated oversize photo uploads were being saved at 25 MiB and answered with HTTP 201. They now get rejected with 413, because accepting and silently truncating data is worse than refusing the request. The phone UI dropped confidence percentages in favor of the registered band words, with a follow-up that forces a pick when a high band arrives alongside a contradiction.

## The audit: four parallel agents

The `/audit-tests` skill ran first for diagnostics, then `/implement-tests` followed. Four agents went out in parallel, one each for taxonomy mapping, the requirements matrix, persona coverage and journey mapping. The integration lane scored 14 for 14 against a real postgres:16 container. The escape scan came back 0/0/0.

Requirements matrix landed at 16 MUST requirements: 12 covered, 1 partial, 2 pilot-manual, 1 uncovered. Zero orphans after an agent found and fixed one the previous matrix had missed. Personas came out shop-employee 3 of 3 and owner 1 of 3, a 33 percent score under the 60 percent threshold. Journeys were 6 of 7 on scan-to-draft, 2 of 3 on draft review, 3 of 4 on correction. The audit found gaps and mapped the gaps to beads that could close them. Fifteen release commits fired through the day as versions bumped from v0.3.2 through v0.4.0.

The main thread verified three of the taxonomy agent's claims before grading on them, and found one wrong on its face. It reported SECURITY.md absent. The file exists at the repository root. That is the reason the verification step was worth the minutes it cost.

Governance: A repository truth audit (doc 027) re-verified every claim marked REPORTED in docs 005, 006, 013 and 014 against the code at commit 46d9910. A G0 Truth Lock was signed and the baseline snapshotted. A seventh required CI check was added: a pull request must name its bead, with CODEOWNERS and a PR template alongside it. That check then had to be fixed because it was excluding Dependabot by the run actor instead of the PR author. Floating @v4 GitHub Action tags were pinned to SHAs and dependabot.yml was rewritten to avoid future major version surprises.

## Snowflake: operator claims re-derived

The Snowflake SaaS operator pack reached v2.2 with a commitment: every operator claim binds to current-state evidence, not a stored assertion. Ten pull requests spanned the changes across the claude-code-plugins repository. Each of these operator claims got rebound to fresh evidence: strong authentication, scoped access, cost attribution, trusted pipelines, data quality, failover, and deployment preflight. The pattern was identical to the blog lander: stop trusting the cached claim and re-derive it at the gate.

Collector parity was enforced across the pack, the Replit operator cohort was hardened, and Snowflake v2.2 operator parity was ratified against current-state evidence.

## Coastal-realty config

The coastal-realty-ops journal posting packet had a field pre-reserved for a CC recipient. One line of config added Mandy's address to the nightly send. The slot was already there, so this was a fill-in rather than a change.

## The collaboration

The collaboration beat: Claude Opus 5, Claude Sonnet 5, Claude Fable 5, GPT 5.6 Luna, Claude Opus 4.8 across 1409 minutes, 19 failure-to-fix moments scattered across independent sessions, 4 course-corrections. The receipt bug was the one arc worth telling because it surfaced the pattern that made the others make sense.

Four repos, four unrelated pieces of work, and the same small move in each one. A stored claim said something had happened. The cheaper fix was always to re-derive the thing at the gate rather than to make the claim more trustworthy. I would not call that a method yet. Nothing packageable came out of the day, and the four threads were running independently, so the resemblance may be as much about what I was already looking for as about the code.

## Related Posts

- [Bind the Receipt to the Commit It Installed](https://startaitools.com/posts/the-commit-the-test-actually-installed/)
- [A Closed Epic Is a Claim, Not a Fact](https://startaitools.com/posts/we-told-the-auditors-to-refute-us/)
- [Every Claim Needs a Shipped Source and an Executable Proof](https://startaitools.com/posts/working-is-not-proven/)
