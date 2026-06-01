---
title: "Ninety Skills, Three Packs, One Day"
description: "Building three complete 30-skill SaaS integration packs — Sentry, Notion, and Supabase — in a single day. Plus cad-dxf-agent v0.11.0 with architectural drift detection as a CI gate."
date: "2026-03-22"
tags: ["claude-code", "automation", "architecture", "release-engineering", "ai-agents"]
featured: false
---
One hundred commits. Three complete SaaS packs. Ninety skills from zero to shipped.

March 22nd was the day the pack factory proved it works. Not a prototype. Not a concept. Three production-ready integration packs — Sentry, Notion, and Supabase — each containing 30 skills, all built and scored in a single session.

The claude-code-plugins marketplace gained 90 new skills in a day. Meanwhile, cad-dxf-agent quietly shipped v0.11.0 with a CI gate that detects when your architecture drifts from your design documents.

## The 30-Skill Curriculum

Every SaaS pack follows the same curriculum. Thirty skills, in order, each building on the last. The sequence isn't random. It's the path a developer actually walks when adopting a platform.

Here's the full curriculum:

| # | Skill | Purpose |
|---|-------|---------|
| 1 | install-auth | Get authenticated and running |
| 2 | hello-world | First working integration |
| 3 | local-dev-loop | Fast feedback cycle |
| 4 | sdk-patterns | Idiomatic usage |
| 5 | error-capture | Know when things break |
| 6 | performance-tracing | Know why things are slow |
| 7 | common-errors | Fix the ones everyone hits |
| 8 | debug-bundle | Systematic troubleshooting |
| 9 | rate-limits | Stay under the ceiling |
| 10 | security-basics | Don't ship credentials |
| 11 | prod-checklist | Readiness gate |
| 12 | upgrade-migration | Version transitions |
| 13 | ci-integration | Automated pipelines |
| 14 | deploy-integration | Ship to production |
| 15 | release-management | Coordinate releases |
| 16 | performance-tuning | Optimize hot paths |
| 17 | cost-tuning | Spend less money |
| 18 | reference-architecture | The recommended shape |
| 19 | multi-env-setup | Dev/staging/prod parity |
| 20 | observability | See what's happening |
| 21 | incident-runbook | Respond when it breaks |
| 22 | data-handling | ETL, retention, compliance |
| 23 | enterprise-rbac | Teams and permissions |
| 24 | migration-deep-dive | Complex version jumps |
| 25 | advanced-troubleshooting | The hard debugging |
| 26 | load-scale | Handle real traffic |
| 27 | reliability-patterns | Stay up |
| 28 | policy-guardrails | Enforce org rules |
| 29 | architecture-variants | Adapt to different shapes |
| 30 | known-pitfalls | Avoid the traps |

Skills 1-10 get a developer productive. Skills 11-20 get them to production. Skills 21-30 keep them there. The curriculum mirrors the adoption curve of any SaaS platform — authentication, basic usage, error handling, deployment, operations, and finally the hard enterprise stuff.

This ordering matters. A developer shouldn't encounter `enterprise-rbac` before `install-auth`. A skill about `reliability-patterns` makes no sense if you haven't covered `observability` first. The curriculum is a dependency graph disguised as a numbered list.

The three tiers map to three audiences. An individual developer working through a weekend integration needs skills 1-10. A team shipping to production needs 11-20. A platform team operating at scale needs 21-30. Each tier assumes mastery of the previous one.

## Pack #1: Sentry

Sentry was the first pack built on March 22nd. Thirty skills, starting with SDK installation and authentication, ending with known pitfalls like oversized breadcrumb payloads and transaction name cardinality explosions.

The Sentry pack leans heavily on error capture and performance tracing. Those are Sentry's core competencies, so skills 5 and 6 got extra depth. The `debug-bundle` skill teaches you to generate a self-contained diagnostic artifact — Sentry event JSON, breadcrumb trail, environment snapshot — that you can hand to another developer without them needing access to your Sentry dashboard.

The `ci-integration` skill (13) covers Sentry's release association workflow: tagging commits, uploading source maps in the build pipeline, and linking deploys to release objects so that Sentry can correlate errors to specific deployments. Most teams skip the source map step and then wonder why their production stack traces are minified garbage.

The operations skills (21-30) cover Sentry-specific operational reality: quota management, data scrubbing for GDPR, relay configuration for on-premise deployments, and the common pitfall of accidentally indexing high-cardinality tags that blow up your Discover queries.

## Pack #2: Notion

Same curriculum, completely different platform. Notion's API is page-and-database-centric, not event-centric like Sentry. The skill implementations are fundamentally different even though the skill names are identical.

`install-auth` for Notion means OAuth 2.0 with workspace-level permissions. `error-capture` means handling 409 conflicts when two integrations write to the same page. `rate-limits` means the 3-requests-per-second API throttle and the strategies for batching property updates.

The `reference-architecture` skill maps out the recommended shape for Notion integrations: a sync layer that mirrors Notion databases to a local data store, an event handler for webhook-driven updates, and a reconciliation job that catches drift. This pattern shows up in every serious Notion integration. Nobody writes it down.

`known-pitfalls` covers the things Notion's documentation doesn't warn you about. Rich text block limits. The 100-item cap on relation property rollups. The fact that `archived: true` doesn't mean deleted — it means invisible to the API unless you explicitly ask for archived pages. And the pagination trap: Notion returns a maximum of 100 results per query, with a `has_more` flag and `next_cursor`. Every integration that doesn't paginate works perfectly in development and silently drops data in production when a database exceeds 100 rows.

The `observability` skill is Notion-specific in a way that surprises people. Notion doesn't have a metrics dashboard. There's no built-in way to see API latency trends, error rates, or quota consumption over time. The skill teaches you to build your own: structured logging on every API call, latency histograms pushed to your monitoring stack, and alert thresholds for the rate limit approaching.

## Pack #3: Supabase

Supabase rounds out the day. Postgres under the hood, so the curriculum adapts around relational semantics. `install-auth` covers both the client library and direct Postgres connections. `security-basics` is Row Level Security — the feature that makes or breaks every Supabase project.

The `performance-tuning` skill is where Supabase diverges most from the generic curriculum. You're tuning Postgres, not an API. That means `EXPLAIN ANALYZE`, index selection, connection pooling through pgBouncer, and the specific footguns in Supabase's realtime engine when you subscribe to tables with millions of rows.

`enterprise-rbac` covers custom claims in JWT tokens, organization-scoped RLS policies, and the service role key that bypasses all security — the key that must never reach a client bundle but ends up there in roughly 40% of Supabase tutorials on the internet.

The `load-scale` skill addresses Supabase's connection limits head-on. The free tier caps at 60 concurrent connections. The Pro tier gives you 200. Either way, a serverless function that opens a direct connection per invocation will exhaust the pool during any real traffic spike. The skill walks through pgBouncer's transaction mode, connection pooling via Supabase's built-in pooler, and the edge cases where prepared statements break under transaction-mode pooling.

## The Rewrite Cycle

Not everything scored well on the first pass. Several skills across all three packs came back with evaluation scores in the low 60s. That's failing. The marketplace's quality rubric requires scores above 85 for verified status.

The rewrites targeted specific weaknesses:

- **Generic content.** Skills that described the concept without showing the platform-specific implementation. A `rate-limits` skill that explains rate limiting in general terms instead of showing Sentry's `429` response headers and retry-after behavior. Rewritten with concrete API responses and code.
- **Missing error handling.** Skills that showed the happy path and stopped. The `deploy-integration` skill for Notion originally didn't cover partial deployment failures — what happens when your Notion sync deploys but the webhook registration fails. Added failure modes and recovery steps.
- **Shallow operations content.** The enterprise-tier skills (23-30) were especially prone to this. `policy-guardrails` for Supabase initially described the concept of org-level policies without showing actual RLS policy SQL. Rewritten with production policy examples.

After rewrites, average scores climbed from 61 to 91+. That's verified territory across all three packs.

The rewrite cycle is built into the process, not treated as failure. First-pass content establishes structure and coverage. The scoring rubric identifies weaknesses. Rewrites fix them. Three passes is typical. The 61-to-91 jump happens because the first pass gets the "what" right and the rewrite gets the "how" right. Showing the Supabase RLS policy SQL instead of describing the concept of row-level security — that's the difference between a 61 and a 91.

## The Claude API Pack

Separate from the SaaS curriculum packs, a hand-written Claude API skill pack also shipped. This one wasn't generated from a template. Each skill was authored individually, covering Claude's SDK patterns, streaming responses, tool use, and prompt engineering patterns specific to the Anthropic API.

Scored 95.3 out of 100. The highest-scoring pack in the marketplace. Hand-written content with domain expertise still beats templated generation when the author actually knows the platform. The gap between 91 (rewritten template) and 95.3 (hand-authored) is the gap between competent and excellent. Both pass. One teaches better.

## Gold Standard and Compliance

Two more pieces shipped alongside the packs. A Killer Skill nomination form — the mechanism for surfacing exceptional skills on the marketplace homepage — and a fix for broken Firebase deploy forms that had been silently failing since the last hosting configuration change.

The nomination form feeds the editorial curation pipeline. Instead of algorithmic ranking (which rewards volume over quality), the marketplace uses human curation backed by the 100-point scoring rubric. The form collects nominations. The rubric evaluates them. The best ones get featured.

The Firebase fix was more annoying than complex. The nomination form and a contact form had both stopped submitting silently after a hosting config change broke the function endpoints. No error in the browser console. No failed network request visible to the user. The forms just ate the input and did nothing. The kind of bug that erodes trust — users assume the form worked, never hear back, and don't return.

## Why a Pack Factory Matters

Building one 30-skill pack is a project. Building three in a day is a system.

The curriculum template is the system. Every SaaS platform has authentication. Every platform has rate limits. Every platform has deployment concerns, observability gaps, and enterprise access control patterns. The 30-skill curriculum captures the universal adoption path. Each pack fills in the platform-specific details.

This means new packs are predictable. Want a Stripe pack? The curriculum already exists. Skills 1-10 cover Stripe's API keys, test mode, webhook signatures, and idempotency keys. Skills 11-20 cover CI integration with Stripe's test clocks, deployment strategies for webhook endpoint updates, and subscription lifecycle management. Skills 21-30 cover PCI compliance, dispute handling automation, and the known pitfall of relying on `customer.subscription.updated` events without checking for backdated changes.

I haven't built the Stripe pack yet. But I could describe all 30 skills right now because the curriculum makes the structure predictable. The platform-specific knowledge is the variable. The structure is the constant.

Three packs in one day also stress-tests the curriculum itself. If a skill position doesn't make sense for a platform, that's a signal. All three packs on March 22nd slotted naturally into all 30 positions. The curriculum held. That's 90 data points confirming the ordering works across fundamentally different platform types: an error-monitoring service, a productivity API, and a database platform.

## cad-dxf-agent v0.11.0

While the pack factory was running, cad-dxf-agent shipped its eleventh minor release.

The headline feature: architectural drift detection as a CI gate. This is a system design pattern from EPIC-CAD-31 that compares the actual codebase against its architectural design documents. If the code drifts from the documented architecture — a new module that isn't reflected in the system design, a dependency that violates the documented boundaries — CI fails.

Most teams write architecture documents once and never update them. The documents describe what the system looked like six months ago. Drift detection inverts this: the documents are the source of truth, and the code must conform to them. If they disagree, the code is wrong until the architecture document is deliberately updated.

This is a strong opinion. Most CI gates check code quality — linting, tests, type safety. Checking architectural conformance is rare outside of enterprise monorepos with dedicated platform teams. But for an agent-based system where the LLM planner makes tool selection decisions based on the documented architecture, drift is a correctness bug, not a style issue.

The implementation uses ADK (Agent Development Kit) foundations and Shapely for geometric analysis. The `EntityIndex` got a caching layer for faster lookups, and contextual tool narrowing reduces the number of tools exposed to the LLM planner based on the current operation context. Fewer tools means fewer hallucinated tool calls.

The performance improvements compound. The cached `EntityIndex` avoids re-parsing the DXF entity tree on every tool invocation. For a drawing with 10,000 entities, that's the difference between a 200ms lookup and a 15ms lookup. Multiply by the dozen tool calls in a typical edit session and the agent feels responsive instead of sluggish.

Contextual tool narrowing is subtler. When the user says "move this column," the planner doesn't need access to text-editing tools or block-insertion tools. The narrowing system filters the tool set based on the classified intent, presenting the LLM with 4-5 relevant tools instead of 20+. Smaller tool menus produce better tool selection. This is documented in the EPIC-CAD-31 system design and now enforced by the drift detection gate.

Twelve commits. Clean release. The kind of focused engineering day that happens when you're not context-switching between five different projects.

## The Numbers

| Project | Commits | What shipped |
|---------|---------|-------------|
| claude-code-plugins | ~100 | 3 SaaS packs (90 skills), Claude API pack, gold standard tools |
| cad-dxf-agent | 12 | v0.11.0, drift detection CI gate, perf improvements |
| **Total** | **~112** | **90+ new skills, 1 release** |

Ninety skills in a day sounds absurd until you see the system behind it. A fixed curriculum. A scoring rubric that rejects low-quality output. A rewrite cycle that upgrades failures. And a pack factory that applies the same structure to any SaaS platform.

The marketplace didn't just get bigger. It got systematically bigger. And the next pack is already outlined.

---

### Related Posts

- [Content Quality War: 7-Check Audit Across 340 Plugins](/blog/content-quality-war-7-check-audit-across-340-plugins/) — the quality rubric that these packs were scored against
- [Shipping a CAD Agent from Zero: DXF Parsing, Edit Engines, and LLM Planner Interfaces](/blog/building-cad-dxf-agent-from-zero-to-v010/) — the cad-dxf-agent origin story, from empty repo to v0.1.0
- [Marketplace Quality Blitz: 130 Stubs, 4300 Warnings, Zero Excuses](/blog/marketplace-quality-blitz-130-stubs-4300-warnings/) — the stub replacement and validator cleanup that preceded this pack-building sprint
