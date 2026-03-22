# Attio Skill Pack

> 18 production-grade Claude Code skills for the Attio CRM REST API — real endpoints, real data models, real error codes.

Build Attio integrations with `https://api.attio.com/v2` using typed TypeScript patterns, from first API call through production deployment. Every skill uses actual Attio endpoints, the real object/record/list data model, real attribute types, and actual error response formats.

## Installation

```bash
/plugin install attio-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| Skill | What it does |
|-------|-------------|
| `attio-install-auth` | Access tokens, OAuth 2.0, scope configuration, Bearer auth |
| `attio-hello-world` | First API calls -- list objects, create person, query companies |
| `attio-local-dev-loop` | Project structure, typed client, MSW mocks, integration tests |
| `attio-sdk-patterns` | Typed client wrapper, retry, pagination iterator, multi-tenant factory |
| `attio-core-workflow-a` | Full record CRUD -- create, read, update, delete, search, filter |
| `attio-core-workflow-b` | Lists, entries, notes, tasks -- pipeline management and activity tracking |
| `attio-common-errors` | Every HTTP error code with real response format, causes, and fixes |
| `attio-debug-bundle` | Diagnostic script -- auth, scopes, schemas, rate limits, connectivity |
| `attio-rate-limits` | Sliding window, Retry-After parsing, p-queue throttling, circuit breaker |
| `attio-security-basics` | Token scoping, rotation, webhook signatures, secret scanning |
| `attio-prod-checklist` | 9-phase launch checklist -- auth, errors, rate limits, monitoring, rollback |
| `attio-upgrade-migration` | V1-to-V2 migration, endpoint mapping, community SDK upgrades |

### Pro Skills (P13-P18)

| Skill | What it does |
|-------|-------------|
| `attio-ci-integration` | GitHub Actions with MSW mocks, gated live API tests, release workflow |
| `attio-deploy-integration` | Vercel, Fly.io, Cloud Run deployment with secrets and webhook registration |
| `attio-webhooks-events` | All event types, signature verification, filtered subscriptions, idempotency |
| `attio-performance-tuning` | LRU caching, batch queries with $in, streaming pagination, keep-alive |
| `attio-cost-tuning` | Usage auditing, polling-to-webhook migration, tiered caching, budget alerts |
| `attio-reference-architecture` | Layered project structure, sync patterns, webhook router, multi-env config |

## Attio API Quick Reference

| Resource | Endpoint | Method |
|----------|----------|--------|
| List objects | `/v2/objects` | GET |
| Get object | `/v2/objects/{slug}` | GET |
| List attributes | `/v2/objects/{slug}/attributes` | GET |
| Query records | `/v2/objects/{slug}/records/query` | POST |
| Create record | `/v2/objects/{slug}/records` | POST |
| Get record | `/v2/objects/{slug}/records/{id}` | GET |
| Update record | `/v2/objects/{slug}/records/{id}` | PATCH/PUT |
| Delete record | `/v2/objects/{slug}/records/{id}` | DELETE |
| Search records | `/v2/records/search` | POST |
| Query list entries | `/v2/lists/{slug}/entries/query` | POST |
| Create list entry | `/v2/lists/{slug}/entries` | POST |
| Create note | `/v2/notes` | POST |
| Create task | `/v2/tasks` | POST |
| Manage webhooks | `/v2/webhooks` | GET/POST/PATCH/DELETE |

## Usage

Skills trigger automatically when you discuss Attio topics:

- "Set up Attio API auth" triggers `attio-install-auth`
- "Create an Attio person record" triggers `attio-core-workflow-a`
- "Add a record to a pipeline list" triggers `attio-core-workflow-b`
- "Fix this Attio 429 error" triggers `attio-rate-limits`
- "Deploy my Attio webhook handler" triggers `attio-deploy-integration`

## License

MIT
