# BambooHR Skill Pack

> 18 Claude Code skills for building production BambooHR API integrations — employee management, time off, webhooks, and HR data pipelines.

Build real BambooHR integrations with real API endpoints (`api.bamboohr.com/api/gateway.php/{company}/v1/`), real employee fields, real webhook HMAC verification, and real error handling. Every skill uses the actual BambooHR REST API — no fake SDKs or placeholder code.

## Installation

```bash
/plugin install bamboohr-pack@claude-code-plugins-plus
```

## What You Can Build

- **Employee directory sync** to downstream systems (Slack, Google Workspace, AD)
- **Time off management** — request, approve, track PTO balances
- **HR data pipelines** — custom reports, headcount analytics, compliance exports
- **Employee lifecycle automation** — onboarding provisioning, offboarding deprovisioning
- **Real-time change detection** via BambooHR webhooks (HMAC-SHA256 verified)

## Skills

### Standard (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `bamboohr-install-auth` | HTTP Basic Auth setup, API key generation, connection verification |
| `bamboohr-hello-world` | First API calls — directory, single employee, custom report |
| `bamboohr-local-dev-loop` | MSW mocks, vitest tests, hot reload, integration test setup |
| `bamboohr-sdk-patterns` | Type-safe client wrapper, retry logic, multi-tenant factory, Zod validation |
| `bamboohr-core-workflow-a` | Employee CRUD, directory sync, custom/saved reports, table data |
| `bamboohr-core-workflow-b` | Time off requests, PTO balances, employee files/photos, goals, training |
| `bamboohr-common-errors` | Diagnostic guide for 400/401/403/404/429/503 with `X-BambooHR-Error-Message` |
| `bamboohr-debug-bundle` | Debug bundle script with redacted API responses and connectivity tests |
| `bamboohr-rate-limits` | `Retry-After` handling, p-queue throttling, request volume reduction |
| `bamboohr-security-basics` | API key rotation, webhook HMAC verification, PII field classification |
| `bamboohr-prod-checklist` | Pre-launch checklist, health check endpoint, monitoring alerts, rollback |
| `bamboohr-upgrade-migration` | API change detection, field deprecation mapping, feature-flagged migration |

### Pro (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `bamboohr-ci-integration` | GitHub Actions with MSW unit tests + live API integration tests |
| `bamboohr-deploy-integration` | Deploy to Vercel, Fly.io, Cloud Run with secrets management |
| `bamboohr-webhooks-events` | Global + permissioned webhooks, event routing, idempotency |
| `bamboohr-performance-tuning` | Custom reports vs N+1, incremental sync, caching, DataLoader batching |
| `bamboohr-cost-tuning` | Usage auditing, polling-to-webhook migration, request budgets |
| `bamboohr-reference-architecture` | Full system design — sync engine, lifecycle automation, PostgreSQL schema |

## Key BambooHR API Endpoints Covered

| Endpoint | Method | Skill |
|----------|--------|-------|
| `/employees/directory` | GET | hello-world, core-workflow-a |
| `/employees/{id}/` | GET, POST | core-workflow-a, sdk-patterns |
| `/employees/` | POST | core-workflow-a |
| `/employees/changed/` | GET | performance-tuning, core-workflow-a |
| `/reports/custom` | POST | hello-world, core-workflow-a, performance-tuning |
| `/reports/{id}` | GET | core-workflow-a |
| `/employees/{id}/tables/{table}` | GET, POST | core-workflow-a |
| `/time_off/requests/` | GET | core-workflow-b |
| `/employees/{id}/time_off/request` | PUT | core-workflow-b |
| `/time_off/requests/{id}/status` | PUT | core-workflow-b |
| `/meta/time_off/types` | GET | core-workflow-b |
| `/employees/{id}/files/view` | GET | core-workflow-b |
| `/webhooks/` | GET, POST, DELETE | webhooks-events |
| `/webhooks/{id}/log` | GET | webhooks-events |

## Quick Start

```bash
# 1. Set credentials
export BAMBOOHR_API_KEY="your-key"
export BAMBOOHR_COMPANY_DOMAIN="yourcompany"

# 2. Test connection
curl -s -u "${BAMBOOHR_API_KEY}:x" \
  "https://api.bamboohr.com/api/gateway.php/${BAMBOOHR_COMPANY_DOMAIN}/v1/employees/directory" \
  -H "Accept: application/json" | head -c 200
```

Then ask Claude: "Help me sync BambooHR employees to my database" and the relevant skills activate automatically.

## License

MIT
