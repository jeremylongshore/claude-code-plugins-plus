# Canva Skill Pack

> Claude Code skill pack for the Canva Connect REST API — 30 skills covering OAuth 2.0 PKCE authentication, design creation, export, asset management, brand template autofill, webhooks, and enterprise patterns.

## What It Does

Gives Claude Code deep knowledge of the Canva Connect API at `api.canva.com/rest/v1/*` — real endpoints, real OAuth flows, real rate limits, real error codes. Every skill uses actual API calls with `fetch`, not a fictitious SDK.

## Installation

```bash
/plugin install canva-pack@claude-code-plugins-plus
```

## API Coverage

| Canva API | Endpoints Covered | Key Skills |
|-----------|------------------|------------|
| **OAuth 2.0 PKCE** | `/oauth/authorize`, `/oauth/token`, `/oauth/revoke` | `canva-install-auth` |
| **Designs** | `POST/GET /designs`, `GET /designs/{id}` | `canva-core-workflow-a` |
| **Exports** | `POST /exports`, `GET /exports/{id}` | `canva-core-workflow-a` |
| **Assets** | `POST /asset-uploads`, `POST /url-asset-uploads`, `GET/PATCH/DELETE /assets` | `canva-core-workflow-b` |
| **Brand Templates** | `GET /brand-templates`, `GET /brand-templates/{id}/dataset` | `canva-core-workflow-b` |
| **Autofill** | `POST /autofills`, `GET /autofills/{id}` | `canva-core-workflow-b` |
| **Folders** | `POST/GET/PATCH/DELETE /folders` | `canva-core-workflow-b` |
| **Comments** | `POST /comment_threads`, `POST /replies` | `canva-webhooks-events` |
| **Users** | `GET /users/me`, `GET /users/me/profile`, `GET /users/me/capabilities` | `canva-hello-world` |
| **Webhooks** | JWK signature verification via `/connect/keys` | `canva-webhooks-events` |

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `canva-install-auth` | OAuth 2.0 PKCE setup, token exchange, refresh, scopes |
| `canva-hello-world` | First API call — create design, export, list |
| `canva-local-dev-loop` | Dev server, OAuth callback, MSW mocks, hot reload |
| `canva-sdk-patterns` | Type-safe REST client, auto-refresh, multi-tenant factory |
| `canva-core-workflow-a` | Design creation, export (PDF/PNG/JPG/PPTX/GIF/MP4) |
| `canva-core-workflow-b` | Asset upload, brand template autofill, folder management |
| `canva-common-errors` | HTTP 401/403/429/400/404 diagnosis with real error codes |
| `canva-debug-bundle` | Diagnostic script — connectivity, token, rate limits |
| `canva-rate-limits` | Per-endpoint limits, backoff, queue-based throttling |
| `canva-security-basics` | Token security, JWK webhook verification, scope policy |
| `canva-prod-checklist` | Production readiness checklist, health checks |
| `canva-upgrade-migration` | API changelog tracking, brand template ID migration |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `canva-ci-integration` | GitHub Actions, MSW mocks, token refresh workflow |
| `canva-deploy-integration` | Vercel, Fly.io, Cloud Run deployment patterns |
| `canva-webhooks-events` | JWK verification, 11 event types, idempotency |
| `canva-performance-tuning` | Caching, pagination, export polling optimization |
| `canva-cost-tuning` | Canva tier comparison, API call reduction strategies |
| `canva-reference-architecture` | Layered project structure, service patterns |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `canva-multi-env-setup` | Per-environment OAuth integrations, secret management |
| `canva-observability` | Prometheus metrics, OpenTelemetry traces, alert rules |
| `canva-incident-runbook` | Triage script, decision tree, postmortem template |
| `canva-data-handling` | Token redaction, URL expiry tracking, GDPR compliance |
| `canva-enterprise-rbac` | Scope-based access control, capabilities API |
| `canva-migration-deep-dive` | Strangler fig pattern, asset migration, feature flags |

### Flagship+ Skills (X25-X30)
| Skill | Description |
|-------|-------------|
| `canva-advanced-troubleshooting` | Layer diagnostics, export debugging, token lifecycle |
| `canva-load-scale` | k6 load tests, capacity planning, HPA config |
| `canva-reliability-patterns` | Circuit breaker, graceful degradation, dead letter queue |
| `canva-policy-guardrails` | ESLint rules, pre-commit hooks, CI policy checks |
| `canva-architecture-variants` | Monolith / Service Layer / Microservice blueprints |
| `canva-known-pitfalls` | 10 anti-patterns with real API fixes |

## Usage

Skills trigger automatically when you discuss Canva topics:

- "Help me set up Canva OAuth" triggers `canva-install-auth`
- "Export this design as PDF" triggers `canva-core-workflow-a`
- "Autofill a brand template" triggers `canva-core-workflow-b`
- "Debug this Canva 429 error" triggers `canva-rate-limits`
- "Deploy my Canva integration" triggers `canva-deploy-integration`

## Key Facts

- **Base URL:** `https://api.canva.com/rest/v1`
- **Auth:** OAuth 2.0 Authorization Code with PKCE (SHA-256)
- **Token lifetime:** ~4 hours (refresh tokens are single-use)
- **No SDK:** All calls use `fetch` against the REST API
- **Autofill:** Requires Canva Enterprise organization membership
- **Docs:** [canva.dev/docs/connect](https://www.canva.dev/docs/connect/)
- **OpenAPI:** [canva.dev/sources/connect/api/latest/api.yml](https://www.canva.dev/sources/connect/api/latest/api.yml)

## License

MIT
