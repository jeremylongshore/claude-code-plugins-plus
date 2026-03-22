# Apollo Skill Pack

> Claude Code skill pack for Apollo.io sales intelligence platform (24 skills)

Apollo.io is a B2B sales intelligence and engagement platform with 275M+ contacts, lead search, enrichment, email sequences, and deal management. This pack provides production-ready skills for every stage of Apollo API integration — from first API call to enterprise deployment.

**Links:** [Apollo API Docs](https://docs.apollo.io/) | [Tons of Skills](https://tonsofskills.com) | [Install](#installation)

---

## One-Pager

### The Problem
Apollo.io has no official SDK. The REST API uses non-obvious conventions — `x-api-key` headers (not query params), separate search endpoints that changed names (`/mixed_people/api_search`), a master vs standard key distinction, and a credit model where search is free but enrichment costs money. Teams waste days learning these details.

### The Solution
24 skills covering the full Apollo integration lifecycle with correct endpoints, real code, and production patterns. Every skill uses the actual API (`https://api.apollo.io/api/v1/`), real authentication (`x-api-key` header), and real response shapes from Apollo's documentation.

| What | Detail |
|------|--------|
| **Who** | Developers integrating Apollo.io into sales tools, CRMs, and data pipelines |
| **What** | 24 Claude Code skills: 12 standard, 6 pro, 6 flagship |
| **Where** | Any Node.js/TypeScript or Python project using Apollo's REST API |
| **When** | During development, CI/CD setup, production deployment, or incident response |
| **Why** | Eliminate trial-and-error with Apollo's undocumented patterns |

| Stack | |
|-------|---|
| API | Apollo.io REST API v1 (`api.apollo.io/api/v1`) |
| Auth | `x-api-key` header (master + standard key types) |
| Languages | TypeScript, Python |
| Testing | Vitest + MSW mocks, sandbox tokens |
| Infra | GCP Cloud Run, Vercel, Kubernetes |

### Key Differentiators
- **Correct endpoints**: Uses `/mixed_people/api_search` (not the deprecated `/people/search`), `/people/bulk_match`, `/emailer_campaigns/search`
- **Credit-aware**: Every skill notes which operations cost credits and which are free
- **Master vs standard keys**: Skills flag which endpoints require master API keys
- **Real error handling**: Covers the actual HTTP codes Apollo returns (401 for bad key, 403 for wrong key type, 429 with rate limit details)

---

## Installation

```bash
/plugin install apollo-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `apollo-install-auth` | Configure `x-api-key` header auth, verify with `/auth/health` |
| `apollo-hello-world` | First API call: people search, person enrichment, org enrichment |
| `apollo-local-dev-loop` | MSW mocks, sandbox tokens, Vitest config, dev scripts |
| `apollo-sdk-patterns` | Zod-validated client, retry, pagination, bulk enrichment patterns |
| `apollo-core-workflow-a` | Lead search (`/mixed_people/api_search`) + enrichment pipeline |
| `apollo-core-workflow-b` | Sequences, email accounts, contact management, outreach pipeline |
| `apollo-common-errors` | 401/403/422/429 diagnosis, master vs standard key detection |
| `apollo-debug-bundle` | Connectivity test, key type detection, rate limit headers, endpoint health |
| `apollo-rate-limits` | Per-endpoint sliding window limiter, backoff, p-queue concurrency |
| `apollo-security-basics` | PII redaction, scoped clients, key rotation, security audit |
| `apollo-prod-checklist` | Automated validation: auth, resilience, observability, credit controls |
| `apollo-upgrade-migration` | Audit deprecated patterns, feature-flagged endpoint migration |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `apollo-ci-integration` | GitHub Actions with MSW tests, sandbox staging, secret scanning |
| `apollo-deploy-integration` | GCP Cloud Run, Vercel, Kubernetes with health checks |
| `apollo-webhooks-events` | Polling-based sync, contact stages, sequence monitoring, tasks API |
| `apollo-performance-tuning` | Connection pooling, LRU cache, bulk ops, parallel search, benchmarks |
| `apollo-cost-tuning` | Credit tracking, dedup, lead scoring, budget-aware client |
| `apollo-reference-architecture` | Layered architecture with deals API, BullMQ jobs, CRM sync |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `apollo-multi-env-setup` | Dev/staging/prod configs, sandbox tokens, feature gating, K8s secrets |
| `apollo-observability` | Prometheus metrics, Pino logging, OpenTelemetry tracing, alert rules |
| `apollo-incident-runbook` | Severity matrix, diagnosis script, circuit breaker, post-incident template |
| `apollo-data-handling` | GDPR SAR/erasure, retention policies, field encryption, audit logging |
| `apollo-enterprise-rbac` | Role matrix, scoped API keys, permission middleware, API proxy |
| `apollo-migration-deep-dive` | Salesforce/HubSpot field mapping, bulk create, reconciliation, rollback |

## Apollo API Quick Reference

| Endpoint | Method | Credits | Key Type |
|----------|--------|---------|----------|
| `/mixed_people/api_search` | POST | Free | Standard |
| `/mixed_companies/search` | POST | Free | Standard |
| `/people/match` | POST | 1 | Standard |
| `/people/bulk_match` | POST | 1/match | Standard |
| `/organizations/enrich` | GET | 1 | Standard |
| `/contacts` | POST/PUT/DELETE | Free | Master |
| `/contacts/search` | POST | Free | Master |
| `/contacts/bulk_create` | POST | Free | Master |
| `/emailer_campaigns/search` | POST | Free | Master |
| `/emailer_campaigns/{id}/add_contact_ids` | POST | Free | Master |
| `/opportunities` | POST/PATCH | Free | Master |
| `/email_accounts` | GET | Free | Master |
| `/tasks` | POST | Free | Master |
| `/auth/health` | GET | Free | Any |

## License

MIT
