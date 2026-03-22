---
name: juicebox-reference-architecture
description: |
  Implement Juicebox reference architecture.
  Use when designing system architecture, planning integrations,
  or implementing enterprise-grade Juicebox solutions.
  Trigger with phrases like "juicebox architecture", "juicebox design",
  "juicebox system design", "juicebox enterprise".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, juicebox, juicebox-reference]

---
# Juicebox Reference Architecture

## Overview
Enterprise reference architecture for applications powered by Juicebox's people intelligence platform. Covers the full data flow from natural-language search through profile enrichment to ATS/CRM export via Merge API. Juicebox searches 800M+ profiles using PeopleGPT, runs AI recruiting agents for autonomous sourcing, and integrates with 50+ ATS/CRM systems. Auth is token-based: `Authorization: token {username}:{api_token}`.

## Prerequisites
- Juicebox account with API access (https://juicebox.ai/settings)
- Node.js 18+ with TypeScript
- Redis for caching (or Memcached)
- PostgreSQL for persistent profile storage
- BullMQ or similar for job queues
- Understanding of your target ATS/CRM system (Greenhouse, Lever, Ashby, etc.)

## Instructions

### Step 1: Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Your Application                               │
│                                                                             │
│  ┌──────────┐    ┌──────────────────┐    ┌───────────┐    ┌──────────────┐ │
│  │  Web UI   │───▶│  API Gateway     │───▶│  Search   │───▶│   Juicebox   │ │
│  │  (React)  │    │  (Express/Hono)  │    │  Service  │    │   API        │ │
│  └──────────┘    └──────────────────┘    └─────┬─────┘    │  (PeopleGPT) │ │
│                          │                     │          └──────────────┘ │
│                          │                     ▼                           │
│                          │               ┌───────────┐                     │
│                          │               │   Redis    │                     │
│                          │               │   Cache    │                     │
│                          │               └───────────┘                     │
│                          │                                                 │
│                          ▼                                                 │
│                  ┌──────────────────┐    ┌───────────┐    ┌──────────────┐ │
│                  │  Enrichment      │───▶│  Profile   │───▶│  PostgreSQL  │ │
│                  │  Worker (BullMQ) │    │  Service   │    │  (Profiles)  │ │
│                  └──────────────────┘    └─────┬─────┘    └──────────────┘ │
│                                                │                           │
│                                                ▼                           │
│                  ┌──────────────────┐    ┌───────────┐                     │
│                  │  Webhook Handler │    │  ATS/CRM  │                     │
│                  │  (POST /webhooks)│    │  Sync     │                     │
│                  └──────────────────┘    │ (Merge)   │                     │
│                                          └───────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘

Data Flow:
  1. User enters natural-language query → API Gateway
  2. Search Service checks Redis cache → on miss, calls Juicebox PeopleGPT API
  3. Results cached in Redis (TTL 300s) → returned to UI
  4. Top candidates queued for enrichment → Worker calls Juicebox enrich API
  5. Enriched profiles stored in PostgreSQL with contact data
  6. ATS Sync exports candidates to Greenhouse/Lever/Ashby via Merge API
  7. Webhook Handler receives status updates from Juicebox (agent completions, etc.)
```

### Step 2: Project Structure

```
juicebox-app/
├── src/
│   ├── index.ts                    # App entry point
│   ├── config.ts                   # Environment + Juicebox config
│   ├── routes/
│   │   ├── search.ts               # POST /api/search
│   │   ├── profiles.ts             # GET /api/profiles/:id
│   │   ├── export.ts               # POST /api/export (ATS push)
│   │   ├── webhooks.ts             # POST /webhooks/juicebox
│   │   └── health.ts               # GET /health, /health/ready
│   ├── services/
│   │   ├── juicebox-client.ts      # Juicebox API wrapper
│   │   ├── search.service.ts       # Search orchestration + caching
│   │   ├── enrichment.service.ts   # Profile enrichment logic
│   │   ├── profile.service.ts      # Profile CRUD (PostgreSQL)
│   │   └── ats-sync.service.ts     # Merge API integration
│   ├── workers/
│   │   └── enrichment.worker.ts    # BullMQ enrichment worker
│   ├── lib/
│   │   ├── cache.ts                # Redis cache wrapper
│   │   ├── secrets.ts              # Secret manager integration
│   │   └── circuit-breaker.ts      # Circuit breaker for Juicebox calls
│   └── db/
│       ├── schema.sql              # PostgreSQL schema
│       └── migrations/             # Database migrations
├── tests/
│   ├── search.test.ts
│   ├── enrichment.test.ts
│   └── ats-sync.test.ts
├── Dockerfile
├── docker-compose.yml
├── package.json
└── tsconfig.json
```

### Step 3: Core Service Layer

Build the following services (full implementations in [service layer reference](references/service-layer.md)):

- **JuiceboxClient** (`juicebox-client.ts`) — Thin wrapper handling `Authorization: token {user}:{token}` auth, 15s timeout via AbortController, and typed methods for `search()`, `enrichProfile()`, and `getMe()`. Throws `JuiceboxApiError` (with status/body) or `RateLimitError` (with retry-after seconds).
- **SearchService** (`search.service.ts`) — Cache-first search with Redis (TTL 300s). Retries up to 3 times with exponential backoff (rate-limit-aware). Includes `searchAll()` async generator for cursor-based pagination.
- **EnrichmentService** (`enrichment.service.ts`) — Enriches profiles via Juicebox API and persists to PostgreSQL. Skips re-enrichment if data is less than 24 hours old. `enrichBatch()` continues on individual failures.

### Step 4: Data Flow Implementation

Build the pipeline components (full implementations in [service layer reference](references/service-layer.md)):

- **ATSSyncService** (`ats-sync.service.ts`) — Exports enriched profiles to 50+ ATS/CRM systems via Merge API. Splits name into first/last, maps Juicebox fields to Merge candidate model.
- **Enrichment Worker** (`enrichment.worker.ts`) — BullMQ worker with concurrency 5 and rate limiter (10 jobs/min). Enriches profiles and optionally exports to ATS in a single job.
- **Webhook Handler** (`webhooks.ts`) — Express router with HMAC-SHA256 signature verification. Handles `agent.completed`, `enrichment.completed`, and `credits.low` events.

### Step 5: Database Schema

Create PostgreSQL tables (full SQL in [service layer reference](references/service-layer.md)):

- `profiles` — Primary storage with JSONB columns for skills/experience/education, GIN index on skills, partial index on enriched_at
- `search_history` — Query audit trail with latency and cache-hit tracking
- `ats_exports` — Export records linking profile_id to Merge/ATS IDs with status tracking

### Step 6: Environment Isolation

Create a config module with dev/staging/production presets (full code in [service layer reference](references/service-layer.md)). Key differences: dev uses 60s cache TTL and 2 concurrent enrichments; production uses 300s TTL, 10 concurrent enrichments, and 60 requests/minute rate limit.

## Output
- Architecture diagram showing App, Juicebox API, cache, enrichment worker, ATS sync, and webhook handler
- Project structure with services, workers, routes, and database layers
- `juicebox-client.ts` — API wrapper with auth, retry, and error types
- `search.service.ts` — Cached search with pagination generator
- `enrichment.service.ts` — Profile enrichment with staleness checks
- `ats-sync.service.ts` — Merge API export to 50+ ATS/CRM systems
- `enrichment.worker.ts` — BullMQ worker for async enrichment + ATS export
- `webhooks.ts` — Webhook handler with HMAC signature verification
- `schema.sql` — PostgreSQL schema for profiles, search history, and ATS exports
- `config.ts` — Environment-isolated configuration (dev/staging/prod)

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `JuiceboxApiError 401` | Invalid or expired API token | Regenerate at juicebox.ai/settings; update secret manager |
| `RateLimitError` with `retryAfterSeconds` | Exceeded plan quota | Worker limiter handles this automatically; increase plan if sustained |
| `Merge API error 422` | Invalid candidate data (missing email) | Enrichment must succeed before ATS export; check email field is populated |
| `ECONNREFUSED` on Redis | Redis not running | Start Redis: `docker compose up redis -d` |
| `relation "profiles" does not exist` | Schema not applied | Run `psql -f db/schema.sql` against target database |
| Webhook signature mismatch | Wrong `JUICEBOX_WEBHOOK_SECRET` | Verify the secret matches the one configured in Juicebox dashboard |
| Worker job stuck in `active` | Node process crashed mid-job | BullMQ auto-retries with exponential backoff; check worker logs |

## Examples

### Full Pipeline: Search, Enrich, Export
```typescript
const client = new JuiceboxClient();
const search = new SearchService(client, cache);
const enrichment = new EnrichmentService(client, profileService);
const ats = new ATSSyncService(process.env.MERGE_API_KEY!, process.env.MERGE_ACCOUNT_TOKEN!);

// Search → Enrich top 10 → Export to ATS
const results = await search.search({ query: 'senior backend engineer Go Kubernetes Austin TX', limit: 20 });
const enriched = await enrichment.enrichBatch(results.profiles.slice(0, 10).map(p => p.id));
for (const profile of enriched.filter(p => p.email)) {
  const { atsId } = await ats.exportCandidate(profile, 'job_abc123');
  console.log(`Exported ${profile.name} -> ATS ID: ${atsId}`);
}
```

For Docker Compose setup and additional examples, see [service layer reference](references/service-layer.md).

## Resources
- [Juicebox API Documentation](https://juicebox.ai/docs/api)
- [Juicebox AI Recruiting Agents](https://juicebox.ai/docs/agents)
- [Merge API — ATS Integration](https://docs.merge.dev/ats/overview/)
- [BullMQ Documentation](https://docs.bullmq.io/)
- [Redis Caching Patterns](https://redis.io/docs/manual/patterns/)

## Next Steps
After implementing the architecture, use `juicebox-multi-env-setup` for environment configuration and `juicebox-deploy-integration` for production deployment.
