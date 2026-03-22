# HubSpot Skill Pack

> Claude Code skill pack for HubSpot CRM integration -- 30 skills covering the CRM v3 API, marketing automation, sales pipelines, and production operations.

## What is HubSpot?

HubSpot is a CRM platform for marketing, sales, and customer service. The HubSpot API (v3) provides programmatic access to CRM objects (contacts, companies, deals, tickets), marketing tools (emails, forms, lists), and automation (webhooks, workflows). The official Node.js SDK is `@hubspot/api-client`.

## Pack Overview

This pack provides 30 auto-activating skills covering the full lifecycle of a HubSpot integration: from first install to production-grade architecture. All skills use real HubSpot API endpoints (`/crm/v3/objects/*`), the actual `@hubspot/api-client` SDK, and documented error responses.

## Installation

```bash
/plugin install hubspot-pack@claude-code-plugins-plus
```

## Quick Start

```bash
npm install @hubspot/api-client
export HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

```typescript
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3,
});

// Create a contact
const contact = await client.crm.contacts.basicApi.create({
  properties: { email: 'jane@example.com', firstname: 'Jane', lifecyclestage: 'lead' },
  associations: [],
});

// Search contacts
const results = await client.crm.contacts.searchApi.doSearch({
  filterGroups: [{
    filters: [{ propertyName: 'lifecyclestage', operator: 'EQ', value: 'customer' }],
  }],
  properties: ['email', 'firstname'],
  limit: 10, after: 0, sorts: [],
});

// Batch read (100 contacts in 1 API call)
const batch = await client.crm.contacts.batchApi.read({
  inputs: ids.map(id => ({ id })),
  properties: ['email'], propertiesWithHistory: [],
});
```

## Skills Included

### Standard Skills (S01-S12)

| Skill | Description |
|-------|-------------|
| `hubspot-install-auth` | Install `@hubspot/api-client`, configure private app tokens and OAuth 2.0 |
| `hubspot-hello-world` | CRUD operations on contacts, companies, and deals with real endpoints |
| `hubspot-local-dev-loop` | Dev workflow with Vitest mocks, test accounts, and hot reload |
| `hubspot-sdk-patterns` | Typed client wrappers, batch operations, pagination, error classification |
| `hubspot-core-workflow-a` | Contact-to-deal sales pipeline: upsert, associate, advance stages, log notes |
| `hubspot-core-workflow-b` | Marketing automation: lists, forms, tickets, tasks, cross-object search |
| `hubspot-common-errors` | Real HubSpot error responses (401, 403, 409, 429) with fixes |
| `hubspot-debug-bundle` | Collect correlation IDs, rate limit state, and SDK diagnostics |
| `hubspot-rate-limits` | Backoff with Retry-After, request queues, batch call reduction |
| `hubspot-security-basics` | Token rotation, webhook v3 signature verification, scope management |
| `hubspot-prod-checklist` | Health checks, monitoring alerts, deploy verification scripts |
| `hubspot-upgrade-migration` | SDK version upgrades: API key to token, associations v3 to v4 |

### Pro Skills (P13-P18)

| Skill | Description |
|-------|-------------|
| `hubspot-ci-integration` | GitHub Actions CI with test account, integration tests, secret scanning |
| `hubspot-deploy-integration` | Deploy to Vercel, Fly.io, Cloud Run with secret management |
| `hubspot-webhooks-events` | CRM webhook subscriptions, v3 signature verification, idempotent handlers |
| `hubspot-performance-tuning` | Batch APIs (100x reduction), caching, search optimization, streaming pagination |
| `hubspot-cost-tuning` | API call monitoring, polling-to-webhook migration, batch vs individual analysis |
| `hubspot-reference-architecture` | Layered architecture: infrastructure, service, API layers with association constants |

### Flagship Skills (F19-F24)

| Skill | Description |
|-------|-------------|
| `hubspot-multi-env-setup` | Dev/staging/prod with separate portals, secret managers, environment guards |
| `hubspot-observability` | Prometheus metrics, OpenTelemetry tracing, Pino logging, AlertManager rules |
| `hubspot-incident-runbook` | Triage scripts, decision trees, 401/429/5xx response playbooks, postmortem template |
| `hubspot-data-handling` | GDPR delete API, data export, PII redaction, consent tracking |
| `hubspot-enterprise-rbac` | Multi-token role-based access, OAuth multi-portal, audit trails |
| `hubspot-migration-deep-dive` | Batch import with field mapping, upsert, deal associations, validation |

### Flagship+ Skills (X25-X30)

| Skill | Description |
|-------|-------------|
| `hubspot-advanced-troubleshooting` | Layer-by-layer diagnostics, correlation ID tracking, timing analysis |
| `hubspot-load-scale` | k6 load tests, capacity planning calculator, batch aggregation patterns |
| `hubspot-reliability-patterns` | Circuit breakers, graceful degradation, dead letter queues, health checks |
| `hubspot-policy-guardrails` | ESLint rules, CI token scanning, runtime self-rate-limiting, pre-commit hooks |
| `hubspot-architecture-variants` | Embedded vs service layer vs gateway patterns with decision matrix |
| `hubspot-known-pitfalls` | 10 real anti-patterns: deprecated auth, search limits, wrong association IDs |

## Key HubSpot API Concepts

- **Base URL:** `https://api.hubapi.com`
- **Auth:** Private app access tokens (`pat-na1-*`) or OAuth 2.0
- **Rate limits:** 10 requests/second, 500,000/day (shared per portal)
- **Batch limit:** 100 records per batch operation
- **Search limit:** 10,000 results maximum (use `getPage` for full exports)
- **SDK package:** `@hubspot/api-client` (not `@hubspot/sdk`)

## Usage

Skills trigger automatically when you discuss HubSpot topics:

- "Help me set up HubSpot" triggers `hubspot-install-auth`
- "Create a contact in HubSpot" triggers `hubspot-hello-world`
- "I'm getting a 429 error from HubSpot" triggers `hubspot-rate-limits`
- "Deploy my HubSpot integration" triggers `hubspot-deploy-integration`

## License

MIT
