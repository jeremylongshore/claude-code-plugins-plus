---
title: "git-with-intent v0.9 to v0.10: Docker Upgrades, README Rewrites, and Strategic Research"
description: "Two releases in one week: Docker Node 22 LTS upgrades across 7 services, an interactive README overhaul, and strategic research on Automaton integration."
date: "2026-02-19"
tags: ["release-engineering", "docker", "node-22", "documentation", "developer-experience", "git-with-intent"]
featured: false
---
## Two Releases in a Week

git-with-intent shipped v0.9.0 on February 17 and v0.10.0 on February 19. Two days apart. The first release was a pre-GA security hardening pass. The second was a scale and operations maturity push. Together they closed the gap between "runs on my machine" and "can handle real tenants."

## v0.9.0: Pre-GA Security Hardening

The v0.9.0 release focused on making the platform secure enough to run multi-tenant workloads.

**GitHub Actions pinned to SHA digests** across 17 workflow files. Every third-party action now references a specific commit hash instead of a version tag. Standard supply chain hygiene — a compromised action tag could inject malicious code into CI.

**Sandbox autopilot integration** wired the sandbox into the file-write critical path. When an agent generates code, it executes in an isolated sandbox before any file system writes happen. The sandbox enforces deny-by-default network access, destructive operation checks, and per-agent permission profiles.

**onBeforeStep hook** added pre-operation risk enforcement. Before an agent executes any step, the hook evaluates the operation against safety rules. Risky operations (large file deletions, production branch commits, elevated API calls) get blocked before they execute, not caught after the damage is done.

**Provider registry fix** stopped mutable global state from leaking across tenants. Custom provider registrations now live in instance storage instead of module-level maps. This was a concurrency and test-isolation bug that affected every multi-tenant scenario. (Covered in detail in [Fixing Provider Registry Mutations and Sandbox Permissions](/blog/fixing-provider-registry-mutations-sandbox-permissions/).)

## v0.10.0: Scale and Operations Maturity

v0.10.0 added the infrastructure needed to operate the platform at scale.

### Circuit Breakers and Provider Health

LLM providers go down, rate limits hit, and network partitions happen. The platform now has a `CircuitBreaker` with exponential backoff retry for every LLM provider. A `ProviderHealthRegistry` singleton tracks circuit states, and the selection policy auto-skips providers with open circuits.

A new `GET /health/providers` endpoint exposes circuit breaker visibility, so operators can see which providers are healthy, degraded, or tripped.

### Step Storage in Firestore

Agent run steps migrated from in-memory storage to a Firestore subcollection with cursor-based pagination. New API endpoints:

- `GET /tenants/:tenantId/runs/:runId/steps` — paginated step listing
- `GET /tenants/:tenantId/runs/:runId/steps/:stepId` — individual step detail

This means agent execution history survives process restarts, and operators can audit exactly what an agent did during a run.

### Budget and Quota Endpoints

Two new endpoints for cost visibility:

- `GET /tenants/:tenantId/budget` — agent-queryable budget status with GCP billing alert integration
- `GET /tenants/:tenantId/quota` — per-action rate limit status

The budget endpoint connects to GCP billing budget alerts via Pub/Sub notification channels. When a tenant approaches their spending limit, the endpoint reports it — and the agent can check before initiating expensive operations.

### Harness Engineering Hooks

Five new hooks for agent lifecycle management:

- **Budget management** — enforce cost control per agent per run
- **Environment onboarding** — initialize new tenant environments
- **Loop detection** — prevent infinite agent cycles (agent A calls agent B calls agent A)
- **Self-test** — agent health verification on startup
- **Trace analysis** — debugging hook for agent behavior analysis

### License Change

The license moved from MIT to BSL 1.1. Commercial use requires a license during the restriction period (4 years). After that, it converts to Apache 2.0 automatically. Personal use, non-commercial use, and evaluation are unrestricted.

## Docker: Node 20 to Node 22 LTS

Dependabot opened PRs suggesting Node 25 — a non-LTS version. Those got closed. Instead, all 7 Dockerfiles were manually upgraded to Node 22 LTS (the current Active LTS release):

- `apps/api/Dockerfile` — 2-stage build (build + production)
- `apps/cli/Dockerfile` — 2-stage build
- `apps/gateway/Dockerfile` — 2-stage build
- `apps/github-webhook/Dockerfile` — 2-stage build
- `apps/mcp-server/Dockerfile` — single-stage (slim base)
- `apps/webhook-receiver/Dockerfile` — 2-stage build
- `apps/worker/Dockerfile` — 2-stage build

Every service updated consistently. The upgrade from `node:20-alpine` to `node:22-alpine` picks up V8 improvements and npm 10.x. Build and production stages both use the same base image version to avoid runtime behavior differences between build and deploy.

Why not Node 25? LTS releases get 30 months of support. Current (non-LTS) releases get roughly 6 months before the next version supersedes them. For production infrastructure, LTS is the only reasonable choice.

## README Rewrite: From 870 Lines to 227

The README was 870 lines of accumulated documentation. The rewrite cut it to 227 lines — a 74% reduction — while adding an interactive HTML overview.

The new README has clean tables, GitHub-native Mermaid diagrams (sequence flow, architecture flowchart, roadmap Gantt), and links to the interactive overview at `docs/overview.html`.

### The Interactive Overview

The HTML overview page got several usability improvements:

**Hero CTA bar** with a quick-start code snippet, GitHub button, and docs link. A developer landing on the page knows what to do in 5 seconds.

**Comparison table** showing how git-with-intent differs from GitHub Copilot, Cursor/Windsurf, Linear/Jira, SonarQube, and Dependabot. Each row highlights the specific gap git-with-intent fills.

**Accessibility improvements**: skip-link for keyboard navigation, `aria-labels` on buttons, `:focus-visible` outlines, and Unicode badge icons that work without image loading.

**Visual polish**: glass morphism on the hero section (`backdrop-filter: blur(12px)`), dot grid background pattern, expanded collapsible monorepo section, and a footer with license and navigation links.

I spent more time on the README and overview than I expected. But a clear README pays off every time someone new opens the repo.

## Strategic Research: Automaton Integration

Five research documents (PP-RMAP 241-245) explored integrating git-with-intent with the broader Automaton agent ecosystem:

- **Agent ecosystem inventory** — mapping the current landscape
- **Integration strategy** — how git-with-intent fits as a code-execution backend
- **Engineering risks and mitigations** — what breaks when you wire autonomous agents into CI/CD
- **Bob refactor analysis** — adapting the Bob's Brain architecture for the git-with-intent runtime
- **Agent network vision** — multi-agent coordination across repositories

This research doesn't ship code. But before committing engineering effort to an integration, the strategy documents answer: is this integration worth building, what are the hard problems, and what's the migration path from where we are to where we need to be?

## In Retrospect

Splitting v0.9.0 and v0.10.0 into two releases was the right call. Each release had a clear narrative and a focused changelog. One combined release would have been 40+ commits with no coherent story and a review surface too large to reason about.

The Dependabot Node 25 situation reinforced something I keep re-learning: automated dependency tools suggest the newest version, but production systems need the most stable version. Those are different things, and the tooling doesn't distinguish between them for you.
