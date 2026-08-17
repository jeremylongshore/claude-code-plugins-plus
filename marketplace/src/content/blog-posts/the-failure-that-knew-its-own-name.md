---
title: "Exit Zero Can Lie; Stdout Holds the Answer"
description: "A CLI can print its diagnosis to stdout and still exit 0, where a handler watching stderr never sees it. Three days of cron packets said nothing about why."
date: "2026-08-16"
tags: ["debugging", "ci-cd", "automation", "claude-code", "devops"]
featured: false
canonical: "https://startaitools.com/posts/the-failure-that-knew-its-own-name/"
---
Three days. August 14, 15, 16. The 05:00 cron that builds Ezekiel's posting packet logged the same line: `voice-gen failed -> degraded packet`. Three consecutive days. Ezekiel got three packets with placeholders and no diagnosis. Nobody downstream knew why.

That packet is the whole handoff. It carries three independently voiced pieces for each published post, one for X, one for LinkedIn personal, one for LinkedIn company, and Ezekiel posts them by hand. A degraded packet is not a broken build. It is a person opening an email and finding placeholders where the copy should be.

The diagnosis was sitting in stdout the whole time. But the failure path was reading stderr, and stderr was empty.

## The Wrong Paths

Three hypotheses, in order, before the real one.

A code change broke it. Rejected: git log showed the script unchanged since August 13.

Claude CLI version 2.1.232 landed at 21:12 on August 13, exactly between the last success and the first failure. That looked clean. Reproduced the prompt interactively, though, and it worked fine. So the failure was cron-environment-specific, not a version regression.

Cron PATH must be the issue. Simulated it with `env -i ... PATH=/usr/bin:/bin` and got "timeout: failed to run command 'claude': No such file or directory" immediately. Convincing. Wrong. The binary resolves through a symlink that cron does see.

## The Real One

The answer was not in the packet log at all. It was in the session transcript the 04:00 and 05:00 cron runs write for themselves, which nothing in the pipeline reads.

The transcript had it: `Not logged in - Please run /login`. Printed as ASSISTANT text on STDOUT, with exit code 0. The headless CLI session had died. 8-hour OAuth tokens expire, and only an interactive login refreshes them. Checking the credentials file confirmed the window.

The cron script captured only stderr (which was empty), got no JSON from what it captured, and logged a bare `voice-gen failed`. The diagnosis was printed right there and got thrown away on the failure path. The person who could act on "NOT AUTHENTICATED" never saw it.

The fix, commit 15212612: make the failure path name its own cause.

Three changes:

1. `generate_voice` now captures the exit code and classifies failures into named branches: timeout at 124, NOT AUTHENTICATED matched by regex against that banner, empty stdout, non-zero exit with no JSON, exit 0 with no JSON object. Each branch logs the reason plus the first 500 bytes of raw stdout.
2. That reason rides into the degraded packet's own note AND into the email, so the person on the CC line who can act on it sees it.
3. A CI test (test_no_vibe_derived_text_in_the_repo) flagging vendored product names in published copy went red. Reworded the affected post; the claim still holds.

One implementation detail worth showing: `VOICE_FAIL_FILE="${TMPDIR:-/tmp}/blog-packet-voice-fail.$$"` carries the reason through a temp file, not a shell variable, because `generate_voice` runs inside `$(...)` and variables die with the subshell. It clears at the top of every call so a stale reason cannot be attributed to the wrong post.

Verification: all four failure branches reproduced with a fake CLI shim that prints the real auth banner. Every branch classified correctly. Happy path re-run against the live CLI unchanged. The suite went from 132 passed / 1 failed to 133 passed, 1 skipped, 0 failed.

## The Honest Limit

This makes the outage loud. It does not prevent it. The 8-hour OAuth expiry is still there. The real fix needs `claude setup-token` run interactively and `CLAUDE_CODE_OAUTH_TOKEN` exported from the cron wrappers. That is tracked in bead startaitools-58x, still open on exactly that.

Worth naming the blast radius: the 04:00 producer job runs through the same headless CLI, so this expiry sits under post generation too, not just the packet. Posts did land on all three days, so the producer held. Nothing structural guarantees it will.

Also that day: the 10:00 weekly deterministic feedback sweep ran. Releases v1.11.6, v1.11.7, v1.11.8 shipped. The 04:04 auto-landed post for August 15 went out on one of the degraded packets.

## Elsewhere in the Estate

intent-os closed the B5 "Portfolio Risk and Business Visibility" epic (122 commits, PRs #491 to #513): risk signal sweep, supply-chain posture projection, declared internal business flags, deterministic prioritized risk queue, independent settlement audits, and epic exit-criteria reconciliation. Then opened B6 agent-ops with fail-closed work discovery, repository and tool authority projection, canonical action receipts, dependency-safe work recommendation, rejection of stale authorization replay, and upstream receipt freshness enforcement. Named review subagents: Huygens on code review, Volta on final evidence audit, Herschel guarding B5.1.

claude-code-plugins closed Epic 1 documentation-governance gates (93 commits, PRs #1198 to #1217): a measurement harness, a shared corpus resolver that rejects symlinked ancestors, a single README count writer so two writers cannot disagree, required supersession records, magic-byte asset content-type enforcement distinguishing TrueType from legacy sfnt, retired-domain governance failing closed on provenance races, and rejection of malformed tool allowlists in the validator schema. Five AARs filed alongside the code.

bobs-big-brain-umbrella completed a stack-wide evidence standard document (25 commits) that took six follow-up commits to state its own evidence correctly: qualified the Compiler's tamper controls, disambiguated proof bead lineage, cited the configured review workflow, aligned canonical stack names, and bound Tier-A claims to peer identity. Also added a daily team-tailnet canary and a backup fix preserving eval reproducibility roots.

agent-governance-plane clarified cross-chain proof semantics (6 commits), added an ADR naming Bob's Big Brain as the GSB compose target, and released v0.1.103.

bobs-big-brain-registrar delivered a governance receipt tip API and restart-safe brain releases (4 commits).

bobs-big-brain-compiler receipted ICO maintenance and released v1.23.0 (3 commits).

buzz restored production migration compatibility (10 commits), serialized invite default-channel activation, and declared its fork gates.

## The Work

Claude Opus 5 and Claude Sonnet 5 drove 3 blog-repo debugging sessions (74 turns, 124 tool calls, 14 errors hit, 683 minutes). GPT-5.6 Sol ran the two big autonomous pushes: intent-os (4 sessions, 292 turns, 1001 minutes, low collaboration signal, meaning long execution against pre-planned epics) and claude-code-plugins (5 sessions, 2860 turns, moderate signal). Across 8 repos: 293 commits total.

## Related Posts

[Five Silent Failures in One Day](https://startaitools.com/posts/five-silent-failures-one-day/)

[The Silent Killer in Your Web App: How Bare catch {} Blocks Hide Failures from Everyone](https://startaitools.com/posts/silent-killer-bare-catch-blocks-hide-failures/)

[Liveness Without Health Is Theater](https://startaitools.com/posts/liveness-without-health-is-theater/)
