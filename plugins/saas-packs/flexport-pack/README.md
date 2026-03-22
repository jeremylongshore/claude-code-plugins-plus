# Flexport Skill Pack

> 24 production-ready Claude Code skills for Flexport supply chain and logistics API -- real REST API v2 code with actual endpoints, not templates.

## What This Is

A complete skill pack for building, deploying, and operating Flexport-powered logistics integrations. Every skill contains real Flexport REST API v2 code: shipment tracking, booking creation, purchase order management, commercial invoices, product catalog, and webhook handling. No fake SDK imports -- Flexport uses direct HTTP calls with bearer token auth and `Flexport-Version: 2` header.

## Installation

```bash
/plugin install flexport-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `flexport-install-auth` | Configure API key or OAuth credentials, verify connection with cURL and TypeScript |
| S02 | `flexport-hello-world` | List shipments, retrieve tracking milestones, query containers |
| S03 | `flexport-local-dev-loop` | Typed HTTP client wrapper, mock shipment data, Vitest unit tests |
| S04 | `flexport-sdk-patterns` | Singleton client, paginated iterator, Zod validation, Python typed client |
| S05 | `flexport-core-workflow-a` | Create purchase orders, book shipments, track milestones, retrieve documents |
| S06 | `flexport-core-workflow-b` | Product catalog (HS codes), commercial invoices, freight invoices |
| S07 | `flexport-common-errors` | Fix 401/403/404/422/429/5xx with real error JSON and diagnostic script |
| S08 | `flexport-debug-bundle` | Collect API connectivity, error logs, status page check into support bundle |
| S09 | `flexport-rate-limits` | Header monitoring, exponential backoff, p-queue throttling |
| S10 | `flexport-security-basics` | `X-Hub-Signature` webhook verification, key rotation, least privilege |
| S11 | `flexport-prod-checklist` | Pre-deploy checks, health endpoint, alert thresholds, rollback |
| S12 | `flexport-upgrade-migration` | API v1 to v2 migration, Logistics API versioning, dual-version testing |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `flexport-ci-integration` | GitHub Actions with unit/integration tests, API contract validation |
| P14 | `flexport-deploy-integration` | Vercel webhook routes, Fly.io always-on receiver, Cloud Run sync worker |
| P15 | `flexport-webhooks-events` | Milestone/booking/invoice/document events, signature verification, idempotent handlers |
| P16 | `flexport-performance-tuning` | Max page size, LRU caching, parallel requests, webhook-driven invalidation |
| P17 | `flexport-cost-tuning` | Webhooks over polling, cache TTL by data type, usage monitoring |
| P18 | `flexport-reference-architecture` | Three-tier architecture, project layout, data flow, infrastructure decisions |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `flexport-multi-env-setup` | Per-environment config, production safety guards, environment matrix |
| F20 | `flexport-observability` | Prometheus metrics, pino logging, alert rules, Grafana panels |
| F21 | `flexport-incident-runbook` | Triage decision tree, circuit breaker, postmortem template |
| F22 | `flexport-data-handling` | PII redaction, data retention, GDPR right to erasure |
| F23 | `flexport-enterprise-rbac` | Application-layer RBAC, multi-tenant API keys, audit logging |
| F24 | `flexport-migration-deep-dive` | Legacy forwarder migration, strangler fig, route-by-route cutover |

## Key Flexport API Concepts

- **Base URL**: `https://api.flexport.com` with `Flexport-Version: 2` header
- **Auth**: Bearer token (API Key) or JWT (OAuth client credentials, 24h lifetime)
- **Pagination**: `?page=N&per=M` (max 100 per page), response in `data.records`
- **Webhooks**: HMAC-SHA256 via `X-Hub-Signature` header
- **Core resources**: `/shipments`, `/bookings`, `/purchase_orders`, `/products`, `/commercial_invoices`, `/freight_invoices`
- **Event types**: Milestones, transit, bookings, POs, invoices, documents, containers

## License

MIT
