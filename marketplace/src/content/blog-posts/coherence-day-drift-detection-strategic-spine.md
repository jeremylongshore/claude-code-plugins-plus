---
title: "Coherence as a Deliverable: How a Multi-Surface Engagement Stays Sane"
description: "Why scattered Plane issues, beads, docs, and partner portals silently diverge — and four structural patterns that catch drift before it compounds."
date: "2026-05-08"
tags: ["claude-code", "architecture", "ai-agents", "release-engineering"]
featured: false
---
A sprawling multi-surface engagement (Kobiton partner pilot, 4 months, three deliverable rounds) exposed a silent failure mode: drift doesn't announce itself. A title rename on Plane goes unnoticed when the canonical source doc still has the old framing. A partner-portal deliverable gets updated before the source file does, leaving future sessions reading stale context from what should be source-of-truth.

On 2026-05-08, one session caught two separate drift instances and shipped four structural patterns to make drift cheaper to find next time. None of the drifts were bugs. Both were coherence gaps — places where a single idea lived in multiple surfaces (Plane, beads, local docs, partner portal) with different currency.

The fix wasn't "use one surface." It was: **detect drift early, make the boundaries between surfaces explicit, give pre-committed thinking a home, and grow scope through buckets instead of through accretion.**

## Drift Caught in Two Directions

A May 4 session had renamed a Plane content issue from "Text-first AI triage on session logs (refined per F30)" to "AI-vision testing." The local draft file (`000-docs/020-DR-BLOG-...md`), the partner portal copy (`m2-blog-3.md`), and the CLAUDE.md history were all on the canonical thesis: text-first triage. Plane was the only surface out of sync.

Caught by reading CLAUDE.md cold. A session with no prior context opened the resume-from-cold doc and noticed the contradiction. The fix: revert Plane back to canonical, log the vision-testing angle as a separate evergreen idea in a new file (`034-RR-OPEN`), mark it explicitly as deferred.

The reverse-drift happened the same day. An R2 fork-staging update went to the partner portal first (because the client reads that surface), but the source doc (`021-AA-AACR-r2-...md`) was now stale. Sync brought source up to portal. Header table updated with new snapshot tag, new "Staged audit slate" metadata row. Reverse-drift is the silent kind: the deliverable surface looks current, the source looks wrong, and a future session reading source will replay outdated thinking.

Two drifts in one day on the same engagement. The pattern: without explicit boundaries and a promotions log, every surface drifts toward stale.

## A Current-Focus Block at the Top of CLAUDE.md

Added to `kobiton/CLAUDE.md`: a "Current focus" block at the very top. Three rows. Each row names a live workstream (M2 blog cadence, M3+R3 final review, hooks-as-deterministic thesis), owns it to a bead, and defines what "done" looks like.

Below that: an explicit "what NOT to start" list. New evergreen blogs, project-shipping blogs, site infra, channel work — all queued but explicitly deferred until M2/M3/R3 close.

Why not a checklist or a TODO list? Because a TODO is committed work. A Current-focus block is a *priority map* for cold-starting future sessions. A TODO says "do this." The block says "this is load-bearing now; everything else queues below the line." Future sessions landing cold should know what's live without reading a month of history.

```markdown
## Current focus (2026-05-08) — read this first

| Workstream | Owner | "Done" looks like |
|---|---|---|
| M2 Blog series delivery | kobiton-z3y | Blog 1 published May 11, Blog 2 May 18, Blog 3 May 25 |
| M3 Featured Placement + R3 close | kobiton-9z0.7, kobiton-bmj | R3 deliverable filed and reviewed by May 25 |
| Hooks-as-deterministic layer thesis | kobiton-5cj | Prototype → multi-reviewer pre-flight → R3 above-spec landing |

**What NOT to start until M2/M3/R3 close:** new evergreen blog drafts, new project-shipping blogs, site-refresh work, channel infra.
```

## A Strategic Spine for the 19-Issue Backlog

Same day, a separate consolidation: 19+ scattered Plane content issues organized into a 6-post evergreen series in publication order, with adjacent clusters (B/C/D/E) listed so unfiled ideas have homes too. This is the antidote to backlog rot. Without a spine, every new idea fights every other idea for next session's attention. With a spine, ideas cluster, and new sessions land oriented — they read the spine, see what's live in cluster A, and know that clusters B-E are queued but real.

## RR-OPEN: The Pre-Committed Layer

A new file: `034-RR-OPEN-things-to-think-about.md`. Single surface for engagement-adjacent open questions, loose threads, refinement ideas, and deferred decisions that aren't yet committed work. Not a TODO. Not a backlog. A *pre-committed thinking* surface.

Six categories. Initial seed: 10 bullets. Crucially, it includes a "Promotions log" — when a bullet matures and graduates (to Plane CONTENT, beads, KOB issues, email, or CLAUDE.md), the commit message records where it went:

```markdown
### Promotions log

- 2026-05-08 — "Per-harness spec audit scope (decide before May 14)"
  RESOLVED as out-of-scope. Spec audit stays narrowly scoped to
  code.claude.com/docs/en/mcp per existing contract. The "10-12
  harness reach" framing migrates to OPS-28, not engagement scope.
```

Why not just a TODO list or a scattered Slack thread? Because ideas that live nowhere searchable get re-invented. RR-OPEN is a single backlog-rot antidote: ideas can live here, mature visibly, and graduate with an audit trail of where they went.

## Scope Discipline Through Bucket Boundaries

R3 scope expanded from one bucket to three in a single session. Normally that's a red flag. The discipline that kept it coherent: each bucket got its own bead with explicit deliverable boundaries.

- Standard re-validation (existing bead, no boundary change)
- Spec-conformance audit (new bead, separate surface, distinct findings)
- Hooks bundle (conditional on multi-reviewer pre-flight before May 23)

The empirical findings catalog (F11-F35) and the spec-conformance candidates (F36-F43) live in separate subsections. Scope can grow without losing shape if the boundaries between buckets are explicit and defensible.

## Pre-Flight Catches the Signal-Type Misses

A technical comment for a partner GitHub PR went through multi-reviewer pre-flight before posting. The catch: three signal-type mislabelings in a single comment. The same three mislabelings had propagated back into Plane CONTENT issues that referenced the same source material.

Mistakes don't live in single surfaces. A mislabeling on a public comment is also on the issues that referenced the same source. Catching it pre-flight means one fix in three places. Catching it after publish means a correction comment, three issue edits, and a stale public comment that future readers will trust.

## Also Shipped

R2 follow-up email sent (closing the credibility gap from a May 5 commitment). One beads epic created, one stale bead closed. Three companion commits to `partner-portals/` for the reverse-drift fix.

## Related Posts

- [Enforcement travels with the code: audit-harness v0.1.0](/posts/audit-harness-v010-enforcement-travels-with-code/)
- [Building an AI-friendly codebase: real-time CLAUDE.md creation](/posts/building-ai-friendly-codebase-documentation-real-time-claude-md-creation-journey/)
- [Wild deep dive #2: CLAUDE.md as a resume-from-cold tool](/posts/wild-deep-dive-2-claude-md/)
