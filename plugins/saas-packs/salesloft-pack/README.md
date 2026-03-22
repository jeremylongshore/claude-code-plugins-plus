# SalesLoft Skill Pack

> 18 production-ready Claude Code skills for SalesLoft -- real REST API v2 code with OAuth, cadences, people, and activity tracking.

## What This Is

A complete skill pack for building, deploying, and operating SalesLoft API integrations. Every skill contains real SalesLoft REST API v2 code: people CRUD, cadence enrollment, email/call activity tracking, cost-based rate limiting (600 points/min), OAuth 2.0 flows, and webhook signature verification. No placeholder imports, no fake SDK patterns.

## Installation

```bash
/plugin install salesloft-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `salesloft-install-auth` | OAuth 2.0 authorization code + client credentials flows, token refresh |
| S02 | `salesloft-hello-world` | List people, create person, enroll in cadence -- first API calls |
| S03 | `salesloft-local-dev-loop` | Vitest mocking with real API response shapes, environment separation |
| S04 | `salesloft-sdk-patterns` | Typed client singleton, async pagination iterator, rate-limit interceptor |
| S05 | `salesloft-core-workflow-a` | People search/dedup, cadence listing, bulk enrollment pipeline |
| S06 | `salesloft-core-workflow-b` | Email engagement metrics, call activity logs, per-cadence analytics |
| S07 | `salesloft-common-errors` | Fix 401/403/404/422/429 with real error payloads and diagnostics |
| S08 | `salesloft-debug-bundle` | Bash script collecting auth state, rate limits, endpoint health |
| S09 | `salesloft-rate-limits` | Cost-based model (pages 100+ cost 3-30x), pagination budget calculator |
| S10 | `salesloft-security-basics` | Token lifecycle, webhook HMAC-SHA256, scope minimization |
| S11 | `salesloft-prod-checklist` | Go-live checklist: auth, monitoring, alerting thresholds, rollback |
| S12 | `salesloft-upgrade-migration` | API key to OAuth migration, cadence import/export API adoption |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `salesloft-ci-integration` | GitHub Actions with unit + integration tests, secret management |
| P14 | `salesloft-deploy-integration` | Vercel/Fly.io/Cloud Run deployment with webhook endpoints |
| P15 | `salesloft-webhooks-events` | Signature verification, event routing, idempotency with Redis |
| P16 | `salesloft-performance-tuning` | LRU caching, incremental sync, connection pooling, parallel reads |
| P17 | `salesloft-cost-tuning` | Rate limit cost calculator, incremental vs full sync cost analysis |
| P18 | `salesloft-reference-architecture` | Service layer, typed models, background sync jobs, architecture diagram |

## Key SalesLoft API Concepts Covered

- **Base URL**: `https://api.salesloft.com/v2/` -- all endpoints end in `.json`
- **Auth**: OAuth 2.0 (authorization code + client credentials) or API key
- **Rate Limits**: 600 cost/minute, deep pagination multiplies cost 3-30x
- **People**: CRUD + email search + tag filtering + cadence membership
- **Cadences**: List/import/export sequences with steps (email, phone, other)
- **Activities**: Email sent/opened/clicked/replied, calls with dispositions
- **Webhooks**: HMAC-SHA256 signatures with timestamp replay protection

## License

MIT
