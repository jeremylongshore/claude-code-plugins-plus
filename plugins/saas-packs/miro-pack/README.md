# Miro Skill Pack

> 24 Claude Code skills for building integrations with the Miro REST API v2 — real endpoints, real item types, real OAuth flows.

Every skill targets `https://api.miro.com/v2/` with actual Miro concepts: boards, sticky notes, shapes, cards, frames, connectors, tags, app cards, webhooks, SCIM provisioning, and the credit-based rate limiting system.

## Installation

```bash
/plugin install miro-pack@claude-code-plugins-plus
```

## Skills

### Standard (S01-S12) — Setup through production

| # | Skill | What It Covers |
|---|-------|---------------|
| S01 | `miro-install-auth` | OAuth 2.0 authorization code flow, `@mirohq/miro-api` SDK, token refresh, scope configuration |
| S02 | `miro-hello-world` | Create board, add sticky note + shape + connector, list items, all v2 item types reference |
| S03 | `miro-local-dev-loop` | Project structure, vitest mocks with API fixtures, ngrok tunneling, debug logging |
| S04 | `miro-sdk-patterns` | High-level `Miro` vs low-level `MiroApi` clients, item factory, error wrapper, multi-tenant, Zod validation |
| S05 | `miro-core-workflow-a` | Board CRUD, sticky notes, shapes, cards, frames, text, tags (attach/detach), board members, sharing |
| S06 | `miro-core-workflow-b` | Connectors (captions, snapTo, stroke caps), images (URL + base64), embeds, app cards, documents |
| S07 | `miro-common-errors` | Every HTTP status (400/401/403/404/409/429/5xx) with real error response bodies and fixes |
| S08 | `miro-debug-bundle` | Diagnostic shell script: DNS, HTTPS, auth, rate limit headers, token introspection, status page |
| S09 | `miro-rate-limits` | Credit-based system (100K/min), `X-RateLimit-*` headers, exponential backoff, p-queue, monitor class |
| S10 | `miro-security-basics` | Scope minimization, token lifecycle management, webhook signature verification, secret rotation |
| S11 | `miro-prod-checklist` | OAuth, code quality, infrastructure, circuit breaker, health check, monitoring, rollback |
| S12 | `miro-upgrade-migration` | v1-to-v2 migration map (widgets to items, lines to connectors), SDK upgrade, response shape changes |

### Pro (P13-P18) — CI/CD, webhooks, architecture

| # | Skill | What It Covers |
|---|-------|---------------|
| P13 | `miro-ci-integration` | GitHub Actions workflow, test board isolation, integration tests, token refresh in CI, cleanup |
| P14 | `miro-deploy-integration` | Vercel (serverless webhook handler), Fly.io (fly.toml + health checks), Cloud Run (Secret Manager) |
| P15 | `miro-webhooks-events` | Board subscriptions (`/v2-experimental/webhooks/`), event payload structure, signature verification, idempotency |
| P16 | `miro-performance-tuning` | Cursor pagination iterator, LRU + Redis caching, PQueue concurrency control, connection pooling |
| P17 | `miro-cost-tuning` | Credit usage tracking, caching ROI, type-filtered queries, webhook vs polling cost comparison |
| P18 | `miro-reference-architecture` | Layered architecture, MiroApiClient, BoardService, WebhookProcessor, ConnectorBuilder fluent API |

### Flagship (F19-F24) — Enterprise and migration

| # | Skill | What It Covers |
|---|-------|---------------|
| F19 | `miro-multi-env-setup` | Separate Miro apps per env, config loader, secret managers (GCP/AWS/Vault), environment guards |
| F20 | `miro-observability` | Prometheus metrics (requests, latency, credits), OpenTelemetry traces, pino logging, Grafana panels, alert rules |
| F21 | `miro-incident-runbook` | Triage script, decision tree by status code, token refresh, rate limit mitigation, postmortem template |
| F22 | `miro-data-handling` | PII detection in board content, DSAR export, data redaction, retention policies, secret scanning |
| F23 | `miro-enterprise-rbac` | Board roles (viewer/editor/coowner/owner), team/org management, SCIM 2.0 provisioning, audit logs, sharing policies |
| F24 | `miro-migration-deep-dive` | Board export/import, cross-team duplication, CSV-to-cards import, migration validation, rollback |

## Key Miro Concepts

| Concept | API Endpoint | Skills |
|---------|-------------|--------|
| Boards | `POST/GET/PATCH/DELETE /v2/boards/{id}` | S01, S02, S05 |
| Sticky Notes | `POST /v2/boards/{id}/sticky_notes` | S02, S05 |
| Shapes | `POST /v2/boards/{id}/shapes` | S02, S05, S06 |
| Cards | `POST /v2/boards/{id}/cards` | S05, F24 |
| Connectors | `POST /v2/boards/{id}/connectors` | S02, S06, P18 |
| Tags | `POST /v2/boards/{id}/tags` | S05 |
| Frames | `POST /v2/boards/{id}/frames` | S05, S06 |
| App Cards | `POST /v2/boards/{id}/app_cards` | S06 |
| Webhooks | `POST /v2-experimental/webhooks/board_subscriptions` | P15 |
| Board Members | `POST /v2/boards/{id}/members` | S05, F23 |
| SCIM | `POST miro.com/api/v1/scim/v2/Users` | F23 |
| OAuth 2.0 | `POST /v1/oauth/token` | S01, S10 |

## License

MIT
