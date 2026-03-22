# Webflow Skill Pack

> 24 Claude Code skills for the Webflow Data API v2 — CMS content management, ecommerce, forms, webhooks, and site operations via the `webflow-api` SDK.

Production-ready patterns for building Webflow integrations. Every skill uses real v2 endpoints (`api.webflow.com/v2/*`), real SDK methods (`webflow-api` npm package, `WebflowClient` class), real OAuth 2.0 scopes, and real rate limit handling.

**Links:** [npm: webflow-api](https://www.npmjs.com/package/webflow-api) | [Webflow Developer Docs](https://developers.webflow.com) | [API Reference](https://developers.webflow.com/data/reference/rest-introduction) | [SDK GitHub](https://github.com/webflow/js-webflow-api)

---

## Installation

```bash
/plugin install webflow-pack@claude-code-plugins-plus
```

## What You Get

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `webflow-install-auth` | Install `webflow-api` SDK, configure API tokens and OAuth 2.0 authorization flow |
| S02 | `webflow-hello-world` | First API calls — list sites, read CMS collections, create items |
| S03 | `webflow-local-dev-loop` | TypeScript dev environment with hot reload, vitest mocks, ngrok webhook tunneling |
| S04 | `webflow-sdk-patterns` | Singleton client, typed error handling, pagination helpers, bulk operations, Zod validation |
| S05 | `webflow-core-workflow-a` | CMS content lifecycle — CRUD items, bulk create/update/delete (100/batch), publish |
| S06 | `webflow-core-workflow-b` | Sites, Pages, Forms, Ecommerce (products/orders/inventory), Custom Code APIs |
| S07 | `webflow-common-errors` | Diagnose 400/401/403/404/409/429/500 errors with concrete fixes |
| S08 | `webflow-debug-bundle` | Collect SDK version, token status, rate limits, and connectivity into support bundle |
| S09 | `webflow-rate-limits` | Per-key rate limits, Retry-After headers, p-queue throttling, bulk endpoint optimization |
| S10 | `webflow-security-basics` | Token management, least privilege scopes, webhook HMAC verification, rotation procedures |
| S11 | `webflow-prod-checklist` | Pre-deploy checklist, health checks, circuit breaker, graceful degradation, rollback |
| S12 | `webflow-upgrade-migration` | SDK v1-to-v3 upgrade, API v1-to-v2 endpoint migration, breaking change detection |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `webflow-ci-integration` | GitHub Actions pipelines — unit tests, integration tests, CMS schema validation, publish-on-merge |
| P14 | `webflow-deploy-integration` | Deploy to Vercel/Fly.io/Cloud Run with secrets management and webhook registration |
| P15 | `webflow-webhooks-events` | Register webhooks, HMAC signature verification, event routing for all 11 trigger types |
| P16 | `webflow-performance-tuning` | CDN-cached reads (no rate limit), LRU/Redis caching, bulk batching, webhook cache invalidation |
| P17 | `webflow-cost-tuning` | Plan right-sizing, CDN read optimization, bulk endpoints, usage monitoring, polling elimination |
| P18 | `webflow-reference-architecture` | Layered project structure — client wrapper, CMS service, webhook handlers, caching layer |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `webflow-multi-env-setup` | Per-environment tokens and site IDs with AWS/GCP/Vault secret management |
| F20 | `webflow-observability` | Prometheus metrics, OpenTelemetry tracing, pino structured logging, Grafana dashboards |
| F21 | `webflow-incident-runbook` | Triage script, decision tree, remediation by error type, communication templates, postmortem |
| F22 | `webflow-data-handling` | PII detection/redaction, GDPR DSAR export, right to deletion, data retention policies |
| F23 | `webflow-enterprise-rbac` | OAuth scope-based RBAC, per-site token isolation, permission middleware, audit logging |
| F24 | `webflow-migration-deep-dive` | Bulk import engine (WordPress/CSV/JSON), data transformation, validation, rollback |

## Key API Coverage

| Domain | Endpoints | Skills |
|--------|-----------|--------|
| Sites | List, get, publish | S02, S06, S11 |
| CMS Collections | List, get schema, field types | S02, S05 |
| CMS Items | CRUD, bulk (100/batch), staged vs live, publish | S05, P16, F24 |
| Pages | List, get metadata, update SEO/OG | S06 |
| Forms | List forms, read submissions | S06, F22 |
| Ecommerce | Products, SKUs, orders, inventory, refunds | S06 |
| Webhooks | Register, list, delete (11 trigger types) | P15 |
| Custom Code | Register hosted/inline scripts | S06 |
| OAuth 2.0 | Authorization code flow, scopes, token exchange | S01, F23 |

## Quick Start

```typescript
import { WebflowClient } from "webflow-api";

const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
});

// List sites
const { sites } = await webflow.sites.list();

// List CMS collections
const { collections } = await webflow.collections.list(sites![0].id!);

// Create a CMS item
await webflow.collections.items.createItem(collections![0].id!, {
  fieldData: { name: "Hello API", slug: "hello-api" },
  isDraft: false,
});

// Bulk create up to 100 items
await webflow.collections.items.createItemsBulk(collections![0].id!, {
  items: [{ fieldData: { name: "Item 1", slug: "item-1" } }],
});
```

## License

MIT
