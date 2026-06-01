---
title: "February 2026 State of Affairs: 255 Commits, 12 Projects, and What I Shipped"
description: "A candid look at 18 days of engineering output: 255+ commits across 12 projects, from blockchain infrastructure to CAD agents to auth debugging."
date: "2026-02-22"
tags: ["retrospective", "portfolio", "engineering-velocity", "startup"]
featured: false
---
## The Numbers

Between February 4 and February 22, 2026: **255+ commits across 12 projects**. Zero blog posts. This is the catch-up.

Not every commit was a feature. Plenty were CI fixes, lint cleanup, documentation rewrites, and the kind of infrastructure work that doesn't demo well but keeps everything running. But the output was real, and it shipped to production.

## Project-by-Project

### Moat — Policy-Enforced Execution for AI Agents

Moat went from a skeleton to a functioning execution layer with HTTP proxy domain allowlists, IRSB on-chain receipt integration, a 5-rule default-deny policy engine, and 117 integration tests. The CI saga — 6 commits to fix a pytest namespace package conflict in a Python monorepo — was a reminder that getting CI green after the code works locally is its own project.

**Read more:** [Building Moat: Auth, On-Chain Receipts, and 117 Integration Tests in One Week](/blog/building-moat-auth-persistence-onchain-receipts-117-tests/)

### Hustle — Youth Sports Platform Auth Overhaul

Hustle's auth system got a complete rework. Raw ID tokens replaced with proper Firebase session cookies. A 504 timeout on forgot-password traced to dynamic imports on cold starts. And 17 commits stabilizing a Playwright E2E test suite that was failing randomly — loose URL regexes, false positive error detection, and dev server timeouts that didn't match production.

**Read more:** [Session Cookie Auth, Forgot-Password Timeouts, and Killing Flaky E2E Tests](/blog/session-cookies-forgot-password-flaky-e2e-tests/)

### IRSB — Monorepo v1.0.0

The blockchain protocol platform consolidated into a single monorepo. Two shared packages extracted (`@irsb/kms-signer` and `@irsb/types`), all packages renamed to the `@irsb/*` scope, Envio HyperIndex integration for real-time event indexing across 8 contracts, and CI split into 4 parallel pipelines — cutting build times from 45 to 15 minutes. Plus a README overhaul positioning IRSB as "On-Chain Guardrails for AI Agents."

**Read more:** [IRSB Monorepo v1.0.0: Extracting Shared Packages and Unifying a Blockchain Platform](/blog/irsb-monorepo-v1-extracting-shared-packages/)

### git-with-intent — Two Releases in Two Days

v0.9.0 (security hardening) and v0.10.0 (scale and ops maturity) shipped back-to-back. Docker images upgraded from Node 20 to 22 LTS across 7 services. Circuit breakers added for LLM providers. Step storage migrated to Firestore. The README went from 870 lines to 227 with an interactive HTML overview. Five strategic research documents explored Automaton integration.

**Read more:** [git-with-intent v0.9 to v0.10: Docker Upgrades, README Rewrites, and Strategic Research](/blog/git-with-intent-v090-v0100-docker-upgrades/)

### git-with-intent — Provider Registry Fix

A mutable global registry was causing shared state corruption across tenants. The fix: instance-only storage with a lookup fallback chain. Same release added sandbox deny-by-default permissions and Zod validation for LLM response parsing in the CoderAgent.

**Read more:** [Fixing Provider Registry Mutations and Sandbox Permissions in git-with-intent](/blog/fixing-provider-registry-mutations-sandbox-permissions/)

### CAD DXF Agent — From Zero to v0.1.0

Built a desktop application for a structural engineer to edit 2D DXF drawings with natural language prompts. The planner provider interface abstracts the LLM backend (mock, Gemini, proxy). A validator enforces protected layers. The edit engine applies operations to in-memory copies — original files never get modified. Shipped with 222 tests, PySide6 desktop UI with per-operation approve/reject, and CI/CD including Windows installer packaging.

**Read more:** [Shipping a CAD Agent from Zero: DXF Parsing, Edit Engines, and LLM Planner Interfaces](/blog/building-cad-dxf-agent-from-zero-to-v010/)

### Perception — Dashboard Goes Live

The media intelligence dashboard moved from mock data to real Firestore ingestion across 128 RSS feeds. Auto-ingestion fires on login. An interactive Topic Watchlist supports full CRUD with source search. Per-category trending scores combine relevance, recency, and Hacker News signals.

**Read more:** [Perception Dashboard: Wiring Real Triggers, Topic Watchlists, and the BSL-1.1 Decision](/blog/perception-dashboard-real-triggers-topic-watchlists/)

### Other Active Projects

**kilo** — 75 PR reviews completed on the 75/75 PR review challenge. Reviewing PRs for projects I've never worked on forced me to read unfamiliar codebases fast and articulate what I'd change and why — a different muscle than writing code from scratch.

**learn-with-jeremy** — Course content and infrastructure in development. Teaching Claude Code, agent development, and production deployment patterns to other developers.

**intent-mail** — Email application infrastructure work. Not ready to talk about publicly yet.

**products membership** — Whop marketplace integration for paid membership access to tools and content. Early stage.

## Cross-Project Patterns

Three patterns repeated across every project this month:

### BSL-1.1 Licensing Everywhere

Moat, IRSB, Perception, and git-with-intent all moved to Business Source License 1.1 this month. Source-available now, automatic conversion to Apache 2.0 or MIT in 3-4 years. The reasoning is the same across all four: a solo operator needs a commercial window before the code becomes fully open.

### CI and Testing Investment

Every project got significant testing infrastructure this month:

- **Moat**: 117 integration tests + 6-commit CI debugging saga
- **Hustle**: 17 commits stabilizing Playwright E2E tests
- **IRSB**: CI split into 4 parallel pipelines, 1,200+ total tests
- **git-with-intent**: Sandbox permission enforcement, Zod validation
- **CAD Agent**: 222 tests, live API tests with WIF, Windows installer smoke tests

The common thread: tests aren't just for catching bugs. They're for making it safe to ship fast. When you have 255 commits across 12 projects in 18 days, the only thing preventing regressions is a test suite you trust.

### Monorepo Extraction

Both IRSB and Moat dealt with monorepo growing pains. IRSB extracted shared packages and unified naming. Moat hit pytest namespace conflicts from its multi-service structure. The lesson in both cases: monorepo benefits (shared types, atomic changes, unified CI) come with monorepo costs (tooling conflicts, import path complexity, test isolation). The benefits win when the projects share enough code to justify co-location.

## The Honest Assessment

255 commits sounds impressive until you realize a significant chunk is infrastructure — CI fixes, lint cleanup, Docker upgrades, README rewrites. These are necessary but not customer-facing. The features that actually matter to users:

- Moat can enforce policies on AI agent execution
- Hustle's auth doesn't randomly log people out anymore
- IRSB has a unified monorepo that builds in 15 minutes instead of 45
- CAD Agent lets Tony edit drawings with natural language
- Perception shows trending articles from 128 feeds on login

Five real outcomes from 18 days of work across 12 projects. The rest is scaffolding — important scaffolding, but scaffolding nonetheless.

The 18-day gap between blog posts is also honest feedback. Publishing velocity doesn't match development velocity. I can commit 20 times a day. Writing about it requires a different kind of focus, one that competes for the same limited hours.

## What's Next

March priorities are shifting from infrastructure to product. The platforms are built. The auth works. The CI is green. The monorepos are organized. Now it's about getting users, validating pricing, and shipping the features that paying customers actually ask for.

Specific commitments:

- **learn-with-jeremy** course launch — first cohort
- **Moat** public documentation and developer onboarding guide
- **IRSB** mainnet deployment planning (currently Sepolia testnet only)
- **Hustle** early access beta for 10 families
- Close the content gap — publish within 48 hours of shipping, not 18 days later

---

*Next month: less infrastructure, more product. And posts within 48 hours of shipping, not 18 days later.*
