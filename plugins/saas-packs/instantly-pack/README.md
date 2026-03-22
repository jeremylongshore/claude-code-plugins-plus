# Instantly Skill Pack

> Cold email outreach automation via Instantly.ai API v2 — campaigns, leads, warmup, analytics, and webhooks (24 skills)

Instantly.ai is a cold email outreach platform that manages sending infrastructure, email warmup, campaign sequencing, and reply detection at scale. This skill pack provides production-ready patterns for the Instantly API v2 (`https://api.instantly.ai/api/v2/`), covering the full campaign lifecycle from account warmup through lead import, sequence creation, launch, analytics, and webhook-driven CRM sync.

**API Version:** v2 (v1 deprecated January 2026)
**Auth:** Bearer token with scoped API keys
**Plan Required:** Hypergrowth ($97.95/mo) for full API + webhooks

## Installation

```bash
/plugin install instantly-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `instantly-install-auth` | API v2 authentication, scoped key generation, client wrapper setup |
| `instantly-hello-world` | First API call — list campaigns, check accounts, pull analytics |
| `instantly-local-dev-loop` | Mock server, integration tests, local webhook testing with ngrok |
| `instantly-sdk-patterns` | Type-safe client, retry logic, cursor pagination, multi-tenant factory |
| `instantly-core-workflow-a` | Full campaign launch: create sequences, add leads, assign accounts, activate |
| `instantly-core-workflow-b` | Email warmup lifecycle, warmup analytics, campaign & step-level analytics |
| `instantly-common-errors` | HTTP error reference, campaign status codes, lead/account diagnostics |
| `instantly-debug-bundle` | Collect workspace-wide debug evidence (campaigns, accounts, warmup, webhooks) |
| `instantly-rate-limits` | 429 handling, exponential backoff, request queue, throttled email fetcher |
| `instantly-security-basics` | Scoped keys, secret management, key rotation, webhook auth, audit logs |
| `instantly-prod-checklist` | 5-phase pre-launch validation: accounts, config, leads, test, launch |
| `instantly-upgrade-migration` | API v1 to v2 migration: endpoint map, auth change, pagination, new features |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `instantly-ci-integration` | GitHub Actions CI with mock server, scope validation, deploy pipeline |
| `instantly-deploy-integration` | Deploy webhook receivers to Vercel, Cloud Run, or Fly.io |
| `instantly-webhooks-events` | All 16 event types, webhook CRUD, event routing, CRM sync handlers |
| `instantly-performance-tuning` | Caching, batch lead import, prefetch pagination, connection pooling |
| `instantly-cost-tuning` | Plan comparison, account utilization audit, campaign efficiency analysis |
| `instantly-reference-architecture` | Project layout, modular client design, campaign template system |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `instantly-multi-env-setup` | Dev/staging/prod workspace isolation, environment guards, webhook routing |
| `instantly-observability` | Campaign health monitor, warmup alerts, webhook delivery tracking |
| `instantly-incident-runbook` | P1-P4 response procedures: unhealthy accounts, bounce protect, rate storms |
| `instantly-data-handling` | Lead CRUD, list management, block lists, GDPR deletion, CAN-SPAM compliance |
| `instantly-enterprise-rbac` | Workspace members, scoped API keys, custom tags, audit logging |
| `instantly-migration-deep-dive` | Platform migration: account import, CSV leads, parallel run, cutover |

## Key API Endpoints Covered

| Category | Endpoints |
|----------|----------|
| Campaigns | `POST/GET/PATCH/DELETE /campaigns`, `activate`, `pause`, `analytics`, `variables` |
| Accounts | `POST/GET/PATCH /accounts`, `warmup/enable`, `warmup-analytics`, `test/vitals`, `pause`, `resume` |
| Leads | `POST/GET/PATCH/DELETE /leads`, `leads/list`, `leads/move`, `update-interest-status` |
| Lead Lists | `POST/GET/PATCH/DELETE /lead-lists` |
| Webhooks | `POST/GET/PATCH/DELETE /webhooks`, `test`, `resume`, `webhook-events/summary` |
| Email | `GET /emails`, `POST /emails/reply`, `POST /emails/test`, `unread/count` |
| Block Lists | `POST/GET/DELETE /block-lists-entries`, `bulk-create`, `bulk-delete` |
| Analytics | `campaigns/analytics`, `analytics/daily`, `analytics/steps`, `analytics/overview` |
| Admin | `api-keys`, `audit-logs`, `workspace-members`, `custom-tags`, `background-jobs` |

## Usage

Skills trigger automatically when you discuss Instantly topics:

- "Set up Instantly API" triggers `instantly-install-auth`
- "Create a cold email campaign" triggers `instantly-core-workflow-a`
- "Enable warmup on my accounts" triggers `instantly-core-workflow-b`
- "Handle Instantly webhooks" triggers `instantly-webhooks-events`
- "Debug Instantly errors" triggers `instantly-common-errors`

## License

MIT
