---
title: "X Bug Triage Plugin: Zero to v0.4.3 in One Day"
description: "A brand-new MCP plugin that triages X/Twitter bug reports shipped 10 epics, 13 releases, 89 tests, and 4 extracted sub-agent skills in a single day. Plus three more SaaS packs got quality-repaired."
date: "2026-03-23"
tags: ["ai-agents", "typescript", "testing", "architecture", "claude-code", "automation"]
featured: false
---
Thirteen releases. Ten epics. Eighty-nine tests. Four extracted sub-agent skills. One day.

The `x-bug-triage-plugin` didn't exist at midnight. By end of day it was at v0.4.3 with a full MCP tool surface, SQLite persistence, PII redaction, family-first bug clustering, and four standalone agent skills extracted from the monolith. Forty-plus commits across three repos. Here's how a plugin goes from `git init` to production-shaped in a single session.

## The Problem It Solves

Users report bugs on X/Twitter. Those reports are unstructured, often emotional, sometimes duplicates, and always missing context. The traditional workflow: scroll mentions, copy tweets into a spreadsheet, deduplicate manually, assign owners, create GitHub issues. Slow, lossy, and nobody wants the job.

The x-bug-triage-plugin automates the entire pipeline. Ingest tweets via MCP tools. Parse and classify. Redact PII. Score severity. Cluster related reports into bug families. Route to the right owner. Draft GitHub issues. Surface a Slack review queue for human approval before anything ships. Ten epics. Each one adds a layer.

## Epic-by-Epic: The Build Pattern

### EPIC-01: Foundation

Repo scaffolding, plugin skeleton, durable docs. CLAUDE.md, CHANGELOG, LICENSE, the package.json with correct entry points, the TypeScript config that won't need touching later.

This is the part most people skip. They write code first and reorganize later. That reorganization never happens.

### EPIC-02: Storage

SQLite schema, storage contracts, audit foundation. Every entity in the system gets a table. Tweets, classifications, clusters, routing decisions, issue drafts. The schema is the contract. If the storage layer can represent it, the rest of the system can process it.

Audit columns on every table: `created_at`, `updated_at`, `created_by`. Not because compliance requires it today. Because you'll need the paper trail when a misrouted bug causes an incident and someone asks "who approved that classification?"

### EPIC-03: X Intake Server

The MCP tool surface. Six tools exposed to Claude Code:

1. **ingest-tweet** — Accept raw tweet data, normalize, store
2. **search-tweets** — Query ingested tweets by keyword, date range, author
3. **get-tweet** — Retrieve a single tweet with full metadata
4. **bulk-ingest** — Batch import for backfill scenarios
5. **tweet-stats** — Aggregate counts by status, classification, date
6. **health-check** — Storage connectivity, schema version, uptime

Six tools is the right number for an intake layer. Enough to be useful. Not so many that the tool descriptions overflow the context window. Each tool has typed parameters and structured output — no string-in-string-out hacks.

### EPIC-04: Parsing and Classification

This is where raw tweets become structured data. The parser extracts:

- **Bug indicators** — crash reports, error messages, "doesn't work" patterns
- **Feature requests** — "it would be nice if", "please add", wish-list language
- **Questions** — support requests that aren't bugs
- **Noise** — spam, off-topic mentions, promotional content

PII redaction runs before classification. Email addresses, phone numbers, IP addresses, API keys — anything that looks like personal data gets masked before it hits the database.

Severity scoring uses a weighted model: crash keywords score higher than cosmetic complaints. Multiple reports boost severity. Recent reports weight more than old ones.

### EPIC-05: Family-First Clustering

This is the most interesting layer. Bug reports cluster into families. "App crashes on login" and "login screen goes white then closes" are the same bug. A human sees that instantly. An automated system needs a strategy.

Family-first clustering works in three passes:

1. **Signature extraction** — Reduce each report to a normalized signature: affected component, failure mode, trigger condition
2. **Similarity scoring** — Compare signatures pairwise. Exact component match plus fuzzy failure mode gets a high score. Different components with similar symptoms gets a low score.
3. **Family assignment** — Reports above the similarity threshold join an existing family. Below it, they start a new one.

Override memory handles the edge cases. When a human manually merges or splits families, the system remembers. Next time it sees a similar pair, it defers to the human decision instead of re-applying the algorithm. The system learns from corrections without retraining anything.

Lifecycle tracking means families have states: `new`, `confirmed`, `in-progress`, `resolved`, `wont-fix`. A family's state propagates to its member reports. Resolve the family, resolve all the reports.

### EPIC-06 through EPIC-09: The Pipeline Tail

Four epics that complete the workflow:

**Repo scan** (EPIC-06) maps bug families to source repositories. A repo registry maps components to repos as config, not hardcoded.

**Owner routing** (EPIC-07) goes one step further. Not just which repo, but which person. CODEOWNERS files, recent commit history, and explicit ownership declarations all feed the routing decision.

**Slack review** (EPIC-08) puts humans back in the loop. Triage summaries go to a Slack channel. A reviewer can approve, reject, reclassify, or merge families. Nothing ships to GitHub without a human thumbs-up.

**Issue drafting** (EPIC-09) generates the GitHub issue. Title from the family name. Body from clustered reports with PII stripped. Labels from classification. Assignee from routing. Original tweet links included so the fixer sees exactly what users reported.

### EPIC-10: Hardening

Validation on every MCP tool input. Error boundaries around every async operation. An MVP readiness report that checks all 10 epics and reports what's complete, what's degraded, and what's missing.

This is the epic that separates a demo from a deployable tool. Input validation catches malformed data before it corrupts the database. Error boundaries prevent one failed classification from crashing the intake server. The readiness report tells you whether the plugin is actually ready for traffic.

## Thirteen Releases in One Day

The release cadence tells a story:

- **v0.1.0** — Foundation + storage (EPICs 01-02)
- **v0.1.1 through v0.1.4** — Intake server iterations, fixing edge cases in tweet normalization
- **v0.2.0** — Classification and PII redaction stable
- **v0.3.0 through v0.3.2** — Clustering algorithm tuned, override memory added
- **v0.4.0** — Full pipeline: ingest through issue draft
- **v0.4.1 through v0.4.3** — Hardening, CI pipelines, governance files

Thirteen tagged releases. Semantic versioning as communication: behavior changes get minor bumps, edge case fixes get patches. The version number tells downstream consumers what changed without reading the changelog.

## Agent Extraction: Four Skills From One Plugin

After v0.4.3 shipped, the monolith got decomposed. Four capabilities extracted into standalone agent skills:

1. **bug-clusterer** — The family-first clustering algorithm as an independent skill. Feed it a set of bug reports, get back clustered families with signatures and similarity scores.
2. **repo-scanner** — The repository mapping engine. Give it a component name, get back the repo, owner, and recent commit context.
3. **owner-router** — The routing decision engine. Takes a bug family and returns the recommended assignee with confidence scores.
4. **triage-summarizer** — Generates human-readable summaries of bug families for Slack review or standup reports.

Each extracted skill is independently installable. A team that already has their own intake pipeline but needs better deduplication can install just the bug-clusterer.

This is the pattern: build the monolith first, extract the skills after. You can't design the right boundaries until you've seen where the natural seams are. Premature decomposition creates chatty interfaces. Post-hoc extraction creates clean, self-contained skills.

## 89 Tests

The test suite landed alongside the code. Not after. Eighty-nine tests covering:

- MCP tool input validation (malformed tweets, missing fields, oversized payloads)
- Classification accuracy (known bug reports, known feature requests, known noise)
- PII redaction completeness (emails, phones, IPs, API keys, partial matches)
- Clustering correctness (known families, edge cases, override memory behavior)
- Storage round-trips (write, read, update, delete, concurrent access)
- Routing decisions (single owner, multiple candidates, no match)

CI pipelines run the full suite on every push. No merge without green.

## The Pack Factory Continues

While x-bug-triage-plugin consumed most of the day's energy, the SaaS pack quality repair work continued on the other track.

**OneNote pack**: 18 skills rewritten from stubs to production quality. Score jumped from 61.7 to 91.4. Every skill went from boilerplate placeholder to domain-specific implementation with proper error handling and real API endpoint references.

**Oracle Cloud pack**: 26 skills, same treatment. Score from 61.3 to 92.8. Oracle Cloud has a sprawling API surface — compute, networking, IAM, object storage, database, monitoring. Each skill needs correct OCI SDK methods and region-specific endpoint routing.

**Navan pack**: The highest final score at 93.0, up from 61.2. A Gemini review pass caught API URL inconsistencies — skills were pointing at different base URLs depending on which docs page the original author referenced. The fix unified everything against the Airbyte connector source, the canonical reference for Navan's API surface.

Three packs. Seventy skills total. All pushed from the low 60s into the 90s. Same pattern from [last week's quality war](/posts/content-quality-war-7-check-audit-across-340-plugins/) — systematic audit, batch repair, measurable improvement. The difference: these are full implementation rewrites, not documentation fixes.

The killer skill nomination form also shipped (PR #483), letting marketplace users nominate skills for the homepage spotlight. Plus a Firebase deploy fix that was blocking the form's backend.

## Hybrid AI Stack Gets a Plan

Two commits in hybrid-ai-stack rounded out the day. The v1.2.0 release and a five-phase product improvement plan (PR #3). Not code — strategy for the cost-optimization routing layer that reduces LLM spend by routing simpler requests to cheaper models.

## The Day in Numbers

| Metric | Count |
|--------|-------|
| Total commits | 40+ |
| Repos touched | 3 |
| New plugin (x-bug-triage) releases | 13 |
| Epics completed | 10 |
| Tests written | 89 |
| Sub-agent skills extracted | 4 |
| SaaS pack skills rewritten | 70 |
| Average quality score improvement | 61 to 92 |

The x-bug-triage-plugin is the headline. Zero to v0.4.3 with a full pipeline — tweet ingestion, PII redaction, classification, family clustering, repo routing, Slack review, issue drafting. But the quieter story is the pack factory. Seventy more skills rewritten. Three more packs crossing the 90-point threshold. The marketplace quality floor keeps rising.

---

**Related Posts:**

- [Content Quality War: 7-Check Audit Across 340 Plugins](/posts/content-quality-war-7-check-audit-across-340-plugins/) — The audit framework driving these pack quality repairs
- [Building a Meta-Agent System From Scratch in One Day](/posts/oss-agent-lab-meta-agent-system-one-day/) — Another zero-to-production build in a single session, with a similar epic-by-epic pattern
- [Mobile Fixes, Crypto Upgrades, and Killer Skills](/posts/mobile-fixes-crypto-upgrades-and-killer-skills/) — The Killer Skills spotlight that the nomination form now feeds into
