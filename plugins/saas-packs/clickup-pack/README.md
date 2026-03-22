# ClickUp Skill Pack

> 24 production-ready Claude Code skills for ClickUp API v2 integration — from first API call to enterprise multi-workspace apps.

Build, test, deploy, and operate ClickUp integrations using real API v2 endpoints (`https://api.clickup.com/api/v2/`), real response shapes, and real error codes. No fake SDKs, no placeholder code.

**Links:** [ClickUp API Docs](https://developer.clickup.com/) | [ClickUp Status](https://status.clickup.com) | [Tons of Skills](https://tonsofskills.com)

---

## Installation

```bash
/plugin install clickup-pack@claude-code-plugins-plus
```

## What You Get

| Tier | Skills | Coverage |
|------|--------|----------|
| **Standard (S01-S12)** | Auth, hello world, task CRUD, hierarchy management, error handling, rate limits, security, debug, testing, CI, deploy, upgrades | Day-to-day ClickUp API development |
| **Pro (P13-P18)** | Webhooks, performance tuning, cost optimization, reference architecture (custom fields, time tracking, goals), CI/CD, deployment | Production integrations |
| **Flagship (F19-F24)** | Multi-environment setup, observability, incident response, data handling (GDPR/PII), enterprise RBAC (OAuth multi-workspace), migration (Jira/Asana/Trello) | Enterprise operations |

## ClickUp API Coverage

- **Hierarchy**: Workspace > Space > Folder > List > Task (full CRUD)
- **Tasks**: Create, read, update, delete, subtasks, bulk operations, filtering, pagination
- **Custom Fields**: All types (text, number, dropdown, label, date, currency, checkbox, email, phone, URL, rating, location)
- **Time Tracking**: Create/get/update entries, running timers, date range queries
- **Goals & Key Results**: OKR management, target tracking
- **Webhooks**: 20+ event types (task/list/folder/space/goal), payload handling, idempotency
- **Views**: Board, list, calendar, gantt, table, timeline
- **Auth**: Personal tokens (`pk_*`), OAuth 2.0 Authorization Code flow
- **Rate Limits**: Per-plan tiers (100/1K/10K req/min), `X-RateLimit-*` headers
- **Error Codes**: `OAUTH_017`, `OAUTH_023`, `OAUTH_027`, HTTP 400/401/403/404/429/500

## Skills Reference

| Skill | What It Does |
|-------|-------------|
| `clickup-install-auth` | Personal tokens, OAuth 2.0 flow, connection verification |
| `clickup-hello-world` | First API calls: discover hierarchy, create a task |
| `clickup-core-workflow-a` | Task CRUD: create, read, update, delete, subtasks, assignees, priorities |
| `clickup-core-workflow-b` | Spaces, folders, lists, views (board/gantt/calendar), tags |
| `clickup-common-errors` | Error reference: OAUTH_* codes, 401/403/429/500, diagnostic script |
| `clickup-debug-bundle` | Health check script, diagnostic archive, rate limit inspection |
| `clickup-rate-limits` | Per-plan limits, exponential backoff, queue-based throttling |
| `clickup-security-basics` | Token rotation, git pre-commit hooks, audit logging |
| `clickup-sdk-patterns` | Typed REST client wrapper, singleton, multi-tenant factory, Zod validation |
| `clickup-local-dev-loop` | Project setup, mock API for tests, vitest integration, hot reload |
| `clickup-ci-integration` | GitHub Actions workflows, integration tests, task status sync from CI |
| `clickup-deploy-integration` | Vercel, Fly.io, Cloud Run deployment with secrets management |
| `clickup-prod-checklist` | Go-live checklist, health verification script, rollback procedures |
| `clickup-upgrade-migration` | API v2-to-v3 migration, adapter pattern, feature flags |
| `clickup-webhooks-events` | Create webhooks, 20+ events, payload format, idempotent handlers |
| `clickup-performance-tuning` | LRU caching, pagination generators, connection pooling, webhook cache invalidation |
| `clickup-cost-tuning` | Plan comparison, request reduction, polling-to-webhook migration |
| `clickup-reference-architecture` | Custom fields API, time tracking, goals/OKRs, two-way sync |
| `clickup-multi-env-setup` | Per-environment tokens, workspace isolation, environment guards |
| `clickup-observability` | Prometheus metrics, OpenTelemetry traces, Grafana alerts |
| `clickup-incident-runbook` | Triage script, decision tree, circuit breaker, postmortem template |
| `clickup-data-handling` | PII detection, response redaction, GDPR export, data retention |
| `clickup-enterprise-rbac` | OAuth multi-workspace apps, role checking, user groups, permission middleware |
| `clickup-migration-deep-dive` | Jira/Asana/Trello import, workspace cloning, validation |

## License

MIT
