# Salesforce Skill Pack

> 30 production-grade Claude Code skills for Salesforce CRM integration — jsforce, SOQL, Bulk API 2.0, Change Data Capture, and Apex development patterns.

## Installation

```bash
/plugin install salesforce-pack@claude-code-plugins-plus
```

## What's Inside

Real Salesforce API code — not templates. Every skill uses actual jsforce methods, real SOQL queries, genuine Salesforce REST endpoints (`/services/data/v59.0/sobjects/`), and authentic error codes (`INVALID_FIELD`, `REQUEST_LIMIT_EXCEEDED`, `UNABLE_TO_LOCK_ROW`).

## Skills Included

### Standard Skills (S01-S12)
| Skill | What It Does |
|-------|-------------|
| `salesforce-install-auth` | jsforce/simple-salesforce setup with OAuth 2.0 flows (Username-Password, JWT Bearer, Web Server) |
| `salesforce-hello-world` | First SOQL query and sObject CRUD on Account/Contact/Lead |
| `salesforce-local-dev-loop` | SFDX scratch orgs, hot reload with tsx, mocked jsforce testing |
| `salesforce-sdk-patterns` | Singleton connections, typed sObject interfaces, error code mapping |
| `salesforce-core-workflow-a` | SOQL queries, relationship queries, sObject Collections CRUD |
| `salesforce-core-workflow-b` | Bulk API 2.0 ingest/query, Composite API, Composite Graph |
| `salesforce-common-errors` | Top 10 Salesforce errors with real error messages and solutions |
| `salesforce-debug-bundle` | Debug logs, API limits, EventLogFile, Salesforce Status API |
| `salesforce-rate-limits` | 24-hour rolling API limits, backoff, quota monitoring |
| `salesforce-security-basics` | Connected App security, FLS, integration user profiles |
| `salesforce-prod-checklist` | Sandbox validation, API limit planning, deployment steps |
| `salesforce-upgrade-migration` | API version upgrades, jsforce v1-to-v3 migration |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `salesforce-ci-integration` | GitHub Actions with JWT auth, Apex testing, metadata deployment |
| `salesforce-deploy-integration` | Deploy to Heroku (Connect), Vercel, Cloud Run with JWT |
| `salesforce-webhooks-events` | Change Data Capture, Platform Events, Outbound Messages |
| `salesforce-performance-tuning` | SOQL optimization, describe caching, Collections batching |
| `salesforce-cost-tuning` | Edition selection, API call budgets, Bulk API cost savings |
| `salesforce-reference-architecture` | Polling vs event-driven vs Heroku Connect patterns |

### Flagship Skills (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `salesforce-multi-env-setup` | Sandbox types, org authentication, promotion flows |
| `salesforce-observability` | API limit Prometheus metrics, EventLogFile forensics, alerts |
| `salesforce-incident-runbook` | Triage with Salesforce Status API, error decision tree |
| `salesforce-data-handling` | GDPR Individual object, DSAR export, PII redaction |
| `salesforce-enterprise-rbac` | Profiles, Permission Sets, OWD, Sharing Rules, SAML SSO |
| `salesforce-migration-deep-dive` | Bulk API data migration with External ID relationships |

### Flagship+ Skills (X25-X30)
| Skill | What It Does |
|-------|-------------|
| `salesforce-advanced-troubleshooting` | Debug log analysis, SOQL query plans, governor limits |
| `salesforce-load-scale` | k6 load testing, Bulk API throughput, capacity planning |
| `salesforce-reliability-patterns` | Circuit breakers, idempotent upserts, dead letter queues |
| `salesforce-policy-guardrails` | SOQL injection prevention, credential leak detection, CI checks |
| `salesforce-architecture-variants` | Direct API vs Event-Driven vs Middleware decision matrix |
| `salesforce-known-pitfalls` | Top 10 anti-patterns with real error messages and fixes |

## Key APIs Covered

- **REST API** — sObject CRUD, SOQL, SOSL, describe, limits
- **Bulk API 2.0** — CSV ingest (insert/update/upsert/delete), bulk query
- **Composite API** — Multi-step transactions, batch, graph
- **Streaming API** — Change Data Capture, Platform Events
- **Tooling API** — Query plans, debug logs, metadata
- **Metadata API** — Permission Sets, profiles, custom objects

## Usage

Skills trigger automatically when you discuss Salesforce topics:

- "Query Salesforce accounts" triggers `salesforce-core-workflow-a`
- "Set up Salesforce authentication" triggers `salesforce-install-auth`
- "Bulk import contacts to Salesforce" triggers `salesforce-core-workflow-b`
- "Debug Salesforce API limit error" triggers `salesforce-common-errors`
- "Set up Salesforce Change Data Capture" triggers `salesforce-webhooks-events`

## License

MIT
