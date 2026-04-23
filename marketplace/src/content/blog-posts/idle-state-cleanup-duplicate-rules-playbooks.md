---
title: "Idle-State Polish, Duplicate-Rule Enforcement, and Marketplace Cleanup"
description: "Maintenance sweep across four repos: braves idle-state trim, claude-code-slack-channel pairing events + duplicate-rule-id enforcement, marketplace playbook layout, and a cad-ai-agent rename."
date: "2026-04-22"
tags: ["typescript", "python", "ci-cd", "claude-code", "devops", "full-stack"]
featured: false
---
A maintenance day across four repos — broadcast tooling, policy engine, marketplace, and a renamed agent. Each fix small, together readable in a minute.

## braves — idle-state trimmed, feeds added, error boundaries landed

The broadcast dashboard spends most of a Braves off-day in "idle" mode. Over the last two weeks idle has accumulated sections that made sense once and don't anymore. Cleanup day:

- **Remove Post-game Audio section** ([ad533bb](https://github.com/jeremylongshore/braves/commit/ad533bb)) — the audio embed was stale 90% of the time and the 10% it worked duplicated the on-page MLB postgame block. Gone.
- **Remove MLB postgame block, dedupe score header** ([426afa9](https://github.com/jeremylongshore/braves/commit/426afa9)) — the idle GameStateBar was rendering a second score header under the main one. Single source of truth for score data.
- **Restore TOP PLAYS, kill idle GameStateBar** ([36e2e57](https://github.com/jeremylongshore/braves/commit/36e2e57)) — TOP PLAYS had gotten dropped during an earlier refactor and nobody noticed. Back in, GameStateBar out. Net: fewer elements, more signal.
- **Add Just Baseball + Braves Journal feeds, fix header placement** ([cf842d8](https://github.com/jeremylongshore/braves/commit/cf842d8)) — two new article feeds slotted into the idle layout. Just Baseball for analytical coverage, Braves Journal for beat reporting. Header placement had been drifting below the feed cards on narrow viewports; anchored to top of column.

The more interesting commit was [cfb9f28](https://github.com/jeremylongshore/braves/commit/cfb9f28) — **root and per-panel error boundaries**. A single JS exception in any panel was blanking the whole dashboard. With per-panel boundaries, a broken podcast feed stays broken in its own card while the score, live narrative, Reddit hype, and article feeds keep rendering. Error boundaries are one of those React features you skip until the first time a panel crashes during a live broadcast. Then you add them on principle.

## claude-code-slack-channel — pairing events and duplicate-rule enforcement

Two journal-wiring PRs and one policy-engine correctness fix:

**[PR #150](https://github.com/jeremylongshore/claude-code-slack-channel/pull/150)** — wire `pairing.accepted` via `allowFrom` snapshot diff. When a human accepts a pairing request, the journal records it by diffing the before/after `allowFrom` snapshot. Before the PR, the journal recorded the fact of the pairing operation but not who got added. Now the journal entry names the user and the rule that authorized the acceptance.

**[PR #149](https://github.com/jeremylongshore/claude-code-slack-channel/pull/149)** — wire `pairing.expired` via `pruneExpired` return. Same shape: the prune sweep already knew which entries were expiring; now it returns them and the caller emits the journal events. No new code path, no polling — the existing sweep is the event source.

**[PR #146](https://github.com/jeremylongshore/claude-code-slack-channel/pull/146)** — enforce duplicate-rule-id rejection server-side. The client-side policy validator already rejected `access.json` with duplicate rule IDs, but the server trusted the file on load. An operator who edited `access.json` directly (bypassing `/slack-channel:policy`) could end up with two rules sharing an ID and the first one silently winning. Now the server refuses to start with a duplicate-rule-id file. Fail-fast at load, not silent-last-write-wins at evaluate time.

**[PR #148](https://github.com/jeremylongshore/claude-code-slack-channel/pull/148)** — journal reader refactor to reverse-chunk tail read + single file handle. For the common case of "show me the last N events," seeking from the end beats scanning from the head. Single handle beats open/close per read. Pure performance work, no behavior change.

**[PR #145](https://github.com/jeremylongshore/claude-code-slack-channel/pull/145)** refreshed CLAUDE.md's stale LoC counts, test counts, and the crap-score threshold (now `30` after yesterday's [ccsc-510](https://github.com/jeremylongshore/claude-code-slack-channel/commit/fa1fb60) tighten from `85 → 30`). Doc numbers drift fast in an active codebase; sweeping them quarterly is cheaper than fixing them after an onboarding reader points at a wrong one.

**[PR #147](https://github.com/jeremylongshore/claude-code-slack-channel/pull/147)** corrected a stale exit-code + stdout-shape comment in `policy-validate`. The comment said "exits 2 on malformed input"; the code exits 1. A wrong comment about a CLI contract is worse than no comment.

## claude-code-plugins — Gemini reviewer, playbook layout, freshie stamping

**[PR #602](https://github.com/jeremylongshore/claude-code-plugins/pull/602)** revived the Gemini PR reviewer and added a contributor philosophy section. The workflow had been silently failing on merged PRs for a few days. Fix plus the philosophy is the right shape: explain what the reviewer is and isn't allowed to block on, so contributors know what to expect when they see a Gemini comment.

**[PR #601](https://github.com/jeremylongshore/claude-code-plugins/pull/601)** — wrap playbooks in `BaseLayout`; retire the `/spotlight` page. Playbooks were rendering without the site chrome, which looked fine in isolation and terrible when linked from anywhere else. Wrapping them in the base layout unifies nav + footer + OG images. The `/spotlight` page had been replaced by the hero marquee and wasn't linked anywhere anymore — retired.

**[PR #593](https://github.com/jeremylongshore/claude-code-plugins/pull/593)** — stamp `run_id` + normalize paths in the freshie compliance populator. The freshie inventory CMDB needs every run's artifacts to be traceable back to the run that produced them; before the PR, two concurrent runs could overwrite each other's rows. `run_id` is the distinguishing key.

[0a4989d0b](https://github.com/jeremylongshore/claude-code-plugins/commit/0a4989d0b) corrected three pre-existing `allowed-tools` errors in plugin SKILL files that had been blocking the `ccpi validate` pipeline. Pre-existing errors that block a validator are a thing that accumulates silently — catching them in a sweep and fixing them in one commit is the cheap way through.

## cad-dxf-agent → cad-ai-agent

A single commit ([a40c620](https://github.com/jeremylongshore/cad-dxf-agent/commit/a40c620)) — the repo was renamed upstream, so all the internal URLs got rewritten. Readme links, contributing links, CI badges, changelog references. The rename reflects expanded scope: the agent started as a DXF-specific tool, grew to handle multi-format CAD, and the old name was narrower than the product. Better to rename once at v0.x than rename at v1.x.

## Nothing dramatic — and that's fine

No case study today. No big release. A policy engine got slightly more correct, a dashboard got slightly more resilient, a marketplace got slightly more consistent, and an agent got its name updated. The distribution over a quarter of "five days of cleanup per splashy feature" is not a failure mode — it's how the splashy features keep working six months later.

## Related posts

- [Five Releases in One Day — CCSC Security Sprint](/posts/ccsc-five-releases-one-day-security-sprint/) — three days ago, the epic this day cleans up after
- [Audit Harness v0.1.0 — Enforcement Travels With the Code](/posts/audit-harness-v010-enforcement-travels-with-code/) — yesterday's infrastructure release
- [Braves Postgame Expansion and Two AI Lessons](/posts/braves-postgame-expansion-and-two-ai-lessons/) — the broadcast tool whose idle state got trimmed today

---

Jeremy made me do it
-claude

