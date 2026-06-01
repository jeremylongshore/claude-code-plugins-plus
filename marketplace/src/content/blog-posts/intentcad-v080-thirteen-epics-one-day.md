---
title: "IntentCAD v0.8.0 — Thirteen EPICs, One Day"
description: "Thirteen EPICs shipped in a single day. Drawing intelligence, compliance validation, material takeoffs, and a stateless agent API — how vertical slicing makes massive feature pushes possible."
date: "2026-03-08"
tags: ["ai-agents", "architecture", "python", "release-engineering"]
featured: false
---
Thirteen EPICs. One day. The largest single-day feature push in [IntentCAD](https://github.com/jeremylongshore/cad-dxf-agent) history, from EPIC-CAD-19 to EPIC-CAD-30.

This isn't a brag post. It's a process post. Thirteen features shipped because of how they were scoped, not because anyone typed faster. The total diff is large but any individual PR is reviewable in 15 minutes. That's the whole trick.

## The EPIC Convention

Every major feature gets a named EPIC: `EPIC-CAD-XX`. Each EPIC is a vertical slice — its own PR, its own tests, its own migration path. No EPIC depends on another EPIC landing first. They can merge in any order.

This convention makes prioritization explicit. When you open the project board and see EPIC-CAD-19 through EPIC-CAD-30 queued up, the scope is visible. You're not guessing what "improve drawing analysis" means. You're looking at thirteen discrete capabilities, each with a PR number and a one-line description.

The naming also makes sprint planning trivial. "Ship EPICs 19 through 30" is an unambiguous goal. Either they all merge green or they don't. If EPIC-CAD-22 has a failing test, you skip it and ship the other twelve. No blocked pipeline. No "well, the consistency checker is broken so we can't release the takeoff engine either."

Here's what shipped, grouped by theme.

## Drawing Intelligence

Four EPICs give the system the ability to *understand* what a drawing contains, not just parse its geometry. This is the layer that makes IntentCAD useful to people who aren't CAD operators.

**Drawing Health Report (EPIC-CAD-19, PR #99)** — automatic quality assessment of any drawing. Layer naming conventions, entity consistency, dimension completeness, orphaned references. Think of it as a linter for engineering drawings. Upload a DXF, get a report card. The health report is the "instant second opinion" — the kind of review that a senior drafter does in their head when they open someone else's file. Now it's automated and consistent.

**Plain-English Drawing Summary (EPIC-CAD-24, PR #105)** — "describe this drawing." The system reads entity types, layer structure, spatial distribution, and text content, then produces a natural language summary. A project manager who doesn't know what a reflected ceiling plan is can read the summary and understand the scope. Useful for submittals, client communication, and anyone who needs to understand what a drawing contains without opening CAD software.

**RFI Generator (EPIC-CAD-25, PR #104)** — detect what's missing. Scans for incomplete dimensions, unlabeled sections, ambiguous references, and generates a Request For Information document. This is the feature that saves the most time in practice. Writing RFIs is tedious. You open a drawing, squint at every dimension chain, cross-reference against the spec, and type up questions one by one. Miss something and it shows up as a change order six months later. The automated scanner doesn't get tired and doesn't miss the dimension that's only absent on sheet A-4.

**Revision Summary with Zone Deltas (EPIC-CAD-26, PR #106)** — zone-by-zone change analysis between drawing revisions. Not just "these entities changed" but "Zone A-3 gained 12 entities and lost 4, net area delta +2.3%." The comparison engine already diffs drawings at the entity level. This EPIC gives the diff spatial context — you can see that all the changes are concentrated in the northwest corner of the floor plan, which tells you the architect redesigned that wing.

## Measurement and Compliance

Three EPICs turn IntentCAD from a viewer into a validation tool. These are the features that justify the "agent" in the repo name — the system doesn't just read drawings, it checks them.

**Automated Takeoff Engine (EPIC-CAD-23, PR #103)** — count everything. Linear feet of pipe, square footage of drywall, number of fixtures by type. Material quantity extraction from drawing geometry. The takeoff results feed directly into estimating workflows. No more counting symbols by hand on a 36x48 sheet. The engine uses the R-tree spatial index to group entities by zone, so you get takeoffs per area, not just grand totals.

**Regulation-Aware Compliance Validation (EPIC-CAD-21, PR #102)** — check drawings against building codes. Egress widths, ADA clearances, fire separation distances, corridor widths. The engine carries a rule set and evaluates the drawing geometry against it. Failures get flagged with the specific code section reference. This is the EPIC that has the most obvious ROI — a missed egress width violation costs orders of magnitude more to fix in construction than in design. Catching it in the drawing review phase is the whole point.

**Cross-Drawing Consistency Checker (EPIC-CAD-22, PR #107)** — verify sheet-to-sheet consistency across a multi-sheet set. Does the reflected ceiling plan match the electrical plan? Do the column grids align between the structural and architectural sheets? These are the errors that survive individual sheet review because they only appear when you compare two sheets side by side. Every architect and engineer knows the pain of a column grid that shifted half an inch between disciplines.

## Infrastructure

The remaining EPICs are the foundation everything else runs on. None of these are user-facing features on their own, but without them the intelligence and measurement features would be demos, not products.

**Session Undo/Redo + Named Snapshots (EPIC-CAD-27, PR #109)** — full undo history with the ability to name checkpoints. You can branch your editing session, try something, and roll back to a named state. This is table stakes for any real editing tool but it had to be built from scratch because the system wasn't session-oriented before. The named snapshot feature is the interesting part — you label a state "before I moved the mechanical room" and you can always get back there.

**Intelligent Batch Operations (EPIC-CAD-20, PR #100)** — process multiple drawings at once. Run the health report across an entire drawing set. Generate takeoffs for every sheet in a package. Batch is the multiplier that makes the intelligence features useful at scale. A single drawing health report is nice. Health reports for all 47 sheets in a construction document set, with a summary of which sheets need attention — that's the product.

**User Accounts, Workspaces & Persistent State (EPIC-CAD-30, PR #113)** — multi-user with persistent work progress. Drawings, analysis results, and session state survive across logins. Allowed-emails configuration controls who can access the system. This is the EPIC that turns a tool into a product. Before this, every session started cold.

**Agent-Mode v1 API (EPIC-CAD-29, PR #110)** — stateless API for AI agents. Compliance checks, takeoffs, summaries, and RFI generation exposed as API endpoints. No session state, no UI, just POST a drawing and GET results. This is how IntentCAD plugs into agentic workflows — an orchestration agent can call the compliance endpoint, read the failures, call a drafting agent to fix them, then re-validate. The entire loop runs without human interaction. The v1 API covers the four highest-value operations. More endpoints will follow as usage patterns emerge.

**Phase 1 Foundations (PR #98)** — complete drafting vocabulary, R-tree spatial index, entity creation. The R-tree is what makes zone-based queries fast. Without spatial indexing, the compliance checker and takeoff engine would be scanning every entity in the drawing for every query. An engineering drawing can have tens of thousands of entities. Linear scan is O(n) per query. R-tree is O(log n). When you're running compliance checks that make hundreds of spatial queries, the difference is seconds vs. milliseconds. R-tree plus libspatialindex in the Docker image.

**Professional Precision Controls (PR #97)** — snap, grid, and measurement tools. The drafting tools that make manual interaction precise.

**Zone Inference + Document Persistence UX (PR #96)** — automatically detect zones from grid lines and column grids, then persist the document state across page reloads. Without persistence, every reload meant re-uploading the drawing and re-running analysis. Small thing. Big impact on usability.

Audit fixes, security hardening, and stability improvements landed in PR #111. A flaky auth test got fixed — it was a race condition in the test setup, not a real auth bug, but it was failing CI runs one out of every five times. The kind of thing that erodes trust in the test suite if you leave it.

## Why Vertical Slices Ship Fast

The question everyone asks: "how do you ship thirteen features in a day without breaking things?"

Every EPIC follows the same pattern: domain logic, API endpoint, tests. No EPIC touches shared infrastructure in a way that could break another EPIC. The R-tree index (PR #98) landed first specifically so that EPICs 21-26 could use spatial queries without coordinating merge order.

The dependency graph is intentionally flat. Drawing intelligence EPICs (19, 24, 25, 26) share the entity model but don't share code with each other. Measurement EPICs (21, 22, 23) share the R-tree but don't touch the intelligence layer. Infrastructure EPICs (20, 27, 29, 30) are completely independent of both.

This flat structure isn't an accident. It was the primary design constraint. When scoping the EPICs, the rule was: if two EPICs need to share new code, extract the shared code into a foundation PR that lands first. PR #98 (R-tree + entity model) exists because of this rule.

The test strategy is per-EPIC isolation. Each EPIC has its own test module. If the compliance validator breaks, the takeoff engine tests still pass. You get independent green/red signals for every feature.

This means code review is parallelizable too. Thirteen PRs, each self-contained. You can review PR #103 (takeoffs) without knowing anything about PR #109 (undo/redo). The review surface is small even though the total changeset is large.

The alternative — one giant PR with thirteen features interleaved — would have been unreviewable. Nobody reads a 3000-line diff and catches the bug in line 2,847. Thirteen focused PRs averaging 200 lines each? That's just a Tuesday. You read the PR title, scan the test file, skim the implementation, approve. Repeat twelve more times.

## Also Shipped

**Braves dashboard** got two PRs that round out the off-game experience. Baseball dashboards have a problem: what do you show when there's no game? A blank screen wastes the most valuable screen real estate in the broadcast booth.

PR #24 added an idle view — what the dashboard shows when no game is live. Last game box score with full recap, upcoming game preview with a clickable card that links to the next game's detail page, and current division standings.

The broadcaster opens the app at 3 PM for a 7 PM game and sees last night's final score, tonight's probable pitchers, and where the Braves sit in the NL East. No clicking around. One screen, all context.

The mobile layout got a batch of fixes in the same PR: horizontal scroll overflow from wide stat tables, TopNav items overflowing their container, and a QueryBar that was visible when it shouldn't be. The GameStateBar was redesigned with recap and preview tabs so you can toggle between what just happened and what's next.

PR #23 added post-game recaps. When all games go final, the dashboard transitions from live mode to recap mode automatically. No manual switch.

The `isPregame` logic was also fixed — it was incorrectly matching final games, which meant the pregame view would flash up momentarily after a game ended. One of those bugs you only catch by watching real games live.

**Beads deployment** — `bd init` across 20+ repositories. The beads task tracking system got deployed to every active project in the workspace. Task state, priorities, and sync across all repos. The timing wasn't coincidental — after a day of shipping thirteen EPICs, having a system that tracks what shipped and what didn't across every project becomes non-optional.

## The Pattern

Thirteen EPICs in one day works because each EPIC was already designed, already scoped, and already had its test plan written. The coding was the easy part. The hard work happened in the days before — defining vertical slices, writing test boundaries, identifying the shared dependencies (R-tree, entity model) that had to land first so everything else could build on them independently.

This is the same pattern as sweep days but inverted. Sweep days close loops on accumulated bugs. EPIC days close loops on accumulated designs. Both work because the work was understood before the clock started. The difference is emotional. Sweep days feel like paying debt. EPIC days feel like deploying an arsenal.

The EPIC naming convention is the underrated piece. `EPIC-CAD-23` is a handle you can use in commit messages, PR titles, Slack threads, and planning docs. Everyone knows what it refers to. No ambiguity, no "which takeoff feature are we talking about?" Just the number.

If you're building a system that needs to ship features fast, start with the naming convention. Name things before you build them. Give every feature a stable identifier that survives from design doc to merged PR to release notes. The rest of the process — independent testing, parallelizable review, flexible merge order — follows from there.

The next phase is integration testing across EPICs. Each feature works in isolation. The interesting bugs will be in the interactions — what happens when you run a compliance check on a batch of drawings that includes a revision with zone deltas? What does the agent API return when the health report finds critical issues mid-takeoff?

Those are v0.9.0 problems. Good problems to have.

v0.8.0 is live. Fifteen PRs merged. Zero reverts.

---

## Related Posts

- [Building a Deterministic DXF Comparison Engine in One Day](/blog/deterministic-dxf-comparison-engine-one-day-build/) — the comparison engine that the revision summary and consistency checker build on
- [Production Release Engineering: Shipping v4.5.0](/blog/production-release-engineering-v450/) — the release automation pattern applied to a different project
- [PDF Extraction Bugs and a 42-Commit Sweep Day](/blog/pdf-extraction-sweep-day-42-commits/) — the previous sweep day that set the stage for this EPIC push
