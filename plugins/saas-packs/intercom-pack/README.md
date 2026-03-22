# Intercom Skill Pack

> 24 Claude Code skills for building production Intercom integrations with the `intercom-client` TypeScript SDK

## Installation

```bash
/plugin install intercom-pack@claude-code-plugins-plus
```

## What You Get

Real Intercom API code covering contacts, conversations, messages, Help Center articles, webhooks, data events, OAuth, and admin management. Every skill uses actual `intercom-client` SDK methods, real endpoint URLs (`api.intercom.io`), real response shapes, and real error codes (401, 404, 409, 422, 429).

## Skills

### Getting Started (S01-S04)
| Skill | What It Does |
|-------|-------------|
| `intercom-install-auth` | Install `intercom-client`, configure access tokens and OAuth |
| `intercom-hello-world` | First API calls: create contacts, send messages, start conversations |
| `intercom-local-dev-loop` | Dev environment with mocked SDK, vitest, ngrok webhook tunneling |
| `intercom-sdk-patterns` | Pagination, error handling, retry logic, search operators, multi-tenant |

### Core Workflows (S05-S08)
| Skill | What It Does |
|-------|-------------|
| `intercom-core-workflow-a` | Contact management: create, search, update, merge leads into users |
| `intercom-core-workflow-b` | Conversations: reply, assign, close, snooze, tag, conversation parts |
| `intercom-common-errors` | Error reference by HTTP code with real response shapes and fixes |
| `intercom-debug-bundle` | Diagnostic script: auth check, rate limits, status page, latency test |

### Operations (S09-S12)
| Skill | What It Does |
|-------|-------------|
| `intercom-rate-limits` | 429 handling, X-RateLimit headers, queue-based throttling, p-queue |
| `intercom-security-basics` | Webhook X-Hub-Signature verification, Identity Verification HMAC, token rotation |
| `intercom-prod-checklist` | Pre-deploy validation, health checks, rollback procedures |
| `intercom-upgrade-migration` | SDK v5 to v6 migration guide with method mapping table |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `intercom-ci-integration` | GitHub Actions CI with mocked unit tests and integration tests |
| `intercom-deploy-integration` | Deploy to Vercel, Fly.io, Cloud Run with webhook endpoints |
| `intercom-webhooks-events` | Webhook signature verification, topic routing, data event tracking |
| `intercom-performance-tuning` | LRU caching, cursor pagination, connection pooling, batch lookups |
| `intercom-cost-tuning` | Replace polling with webhooks, search vs list, request budget monitoring |
| `intercom-reference-architecture` | Layered architecture: client, services, webhooks, articles, sync |

### Flagship Skills (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `intercom-multi-env-setup` | Dev/staging/prod workspace isolation with safety guards |
| `intercom-observability` | Prometheus metrics, OpenTelemetry traces, Grafana alerts |
| `intercom-incident-runbook` | Triage script, decision tree by error code, graceful degradation |
| `intercom-data-handling` | GDPR export/deletion, Data Export API, PII redaction, retention |
| `intercom-enterprise-rbac` | OAuth flows, admin roles, scope-based access, team routing |
| `intercom-migration-deep-dive` | Bulk import contacts/companies/tags/articles from other platforms |

## Key Intercom Concepts

- **Contacts** have a `role` of `user` (identified) or `lead` (anonymous). Leads merge into users.
- **Conversations** contain threaded `conversation_parts` (comments, notes, assignments).
- **Messages** are outbound from admins to contacts (email, in-app, push).
- **Tags** label contacts, companies, and conversations.
- **Data Events** track custom contact activity (past-tense verb-noun naming).
- **Webhooks** use `X-Hub-Signature` (HMAC-SHA1) with a 5-second response timeout.

## API Quick Reference

| Resource | Endpoint | SDK Method |
|----------|----------|-----------|
| Contacts | `POST /contacts` | `client.contacts.create()` |
| Search | `POST /contacts/search` | `client.contacts.search()` |
| Conversations | `GET /conversations/{id}` | `client.conversations.find()` |
| Reply | `POST /conversations/{id}/reply` | `client.conversations.reply()` |
| Messages | `POST /messages` | `client.messages.create()` |
| Articles | `GET /articles` | `client.articles.list()` |
| Tags | `POST /tags` | `client.tags.create()` |
| Events | `POST /events` | `client.dataEvents.create()` |
| Admins | `GET /admins` | `client.admins.list()` |

Rate limits: 10,000 req/min per app, 25,000 req/min per workspace.

## License

MIT
