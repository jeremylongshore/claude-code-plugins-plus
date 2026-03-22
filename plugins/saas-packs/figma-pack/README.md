# Figma Skill Pack

> 30 production-grade Claude Code skills for the Figma REST API and Plugin API

Build design-to-code pipelines, extract design tokens, export assets, handle webhooks, and manage Enterprise features -- all with real Figma API endpoints, actual response shapes, and working TypeScript code.

## Quick Start

```bash
# Install
/plugin install figma-pack@claude-code-plugins-plus

# Set up authentication
export FIGMA_PAT="figd_your-personal-access-token"
export FIGMA_FILE_KEY="your-file-key-from-figma-url"

# Try it
"Help me extract design tokens from my Figma file"
"Export all icons from my Figma components as SVG"
"Set up a webhook to sync tokens when my Figma file changes"
```

## What's Covered

| Area | Key Endpoints | Skills |
|------|--------------|--------|
| **Files & Nodes** | `GET /v1/files/:key`, `GET /v1/files/:key/nodes` | hello-world, core-workflow-a |
| **Image Export** | `GET /v1/images/:key` (PNG/SVG/JPG/PDF) | core-workflow-b |
| **Comments** | `GET/POST /v1/files/:key/comments` | data-handling |
| **Variables** | `GET /v1/files/:key/variables/local` (Enterprise) | core-workflow-a, enterprise-rbac |
| **Components & Styles** | `GET /v1/teams/:id/components`, `GET /v1/files/:key/styles` | core-workflow-a, migration-deep-dive |
| **Webhooks V2** | `POST /v2/webhooks` (FILE_UPDATE, COMMENT, LIBRARY_PUBLISH) | webhooks-events |
| **OAuth 2.0** | `/v1/oauth/token`, `/v1/oauth/refresh` | install-auth, enterprise-rbac |
| **Version History** | `GET /v1/files/:key/versions` | data-handling |
| **Plugin API** | `figma.currentPage`, `figma.createRectangle` | local-dev-loop, architecture-variants |

## Skills

### Standard (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `figma-install-auth` | PAT generation, OAuth 2.0 flow, scope selection |
| `figma-hello-world` | First API call, file structure, node tree walkthrough |
| `figma-local-dev-loop` | Plugin dev with esbuild, REST API testing with fixtures |
| `figma-sdk-patterns` | Typed client wrapper, error classes, node walker, retry logic |
| `figma-core-workflow-a` | Extract design tokens (colors, typography) from styles and variables |
| `figma-core-workflow-b` | Export images/icons as SVG/PNG, batch asset pipelines |
| `figma-common-errors` | HTTP error reference (403, 404, 429, 500) with diagnostics |
| `figma-debug-bundle` | Diagnostic script for support tickets (connectivity, headers, redaction) |
| `figma-rate-limits` | Leaky bucket handling, Retry-After compliance, request queuing |
| `figma-security-basics` | Token storage, scope minimization, webhook passcode verification |
| `figma-prod-checklist` | Production readiness: auth, error handling, monitoring, health checks |
| `figma-upgrade-migration` | Scope deprecation (files:read), Webhooks V1 to V2, OAuth publishing |

### Pro (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `figma-ci-integration` | GitHub Actions for scheduled token sync and asset export |
| `figma-deploy-integration` | Deploy to Vercel, Cloud Run, Fly.io with secret management |
| `figma-webhooks-events` | Webhooks V2 setup, event types, passcode verification, idempotency |
| `figma-performance-tuning` | Response caching, depth parameter, batch fetches, connection reuse |
| `figma-cost-tuning` | Plan-based rate limits, usage tracking, webhook-vs-polling savings |
| `figma-reference-architecture` | Project structure, data flow, token/asset/webhook pipelines |

### Flagship (F19-F24)

| Skill | What It Does |
|-------|-------------|
| `figma-multi-env-setup` | Per-environment PATs, file keys, secret management, env guards |
| `figma-observability` | Prometheus metrics, structured logging, alert rules, health checks |
| `figma-incident-runbook` | Triage script, decision tree, mitigation playbooks, postmortem template |
| `figma-data-handling` | Comments API, version history, PII redaction, data retention |
| `figma-enterprise-rbac` | OAuth 2.0 flow, team/project management, Variables API (Enterprise) |
| `figma-migration-deep-dive` | Style extraction, token transformation, Variables API migration |

### Flagship+ (X25-X30)

| Skill | What It Does |
|-------|-------------|
| `figma-advanced-troubleshooting` | Verbose tracing, response validation, large file chunking |
| `figma-load-scale` | k6 load testing, rate limit measurement, capacity planning |
| `figma-reliability-patterns` | Circuit breaker, cached fallback, retry with Retry-After |
| `figma-policy-guardrails` | Token leak prevention, ESLint rules, runtime policies, config validation |
| `figma-architecture-variants` | CLI vs webhook service vs Figma plugin decision matrix |
| `figma-known-pitfalls` | Top 10 anti-patterns (full file fetch, stale URLs, color format, etc.) |

## Key Concepts

**Authentication:** Figma uses Personal Access Tokens (PATs) with the `X-Figma-Token` header, or OAuth 2.0 for user-facing apps. PATs expire after 90 days max.

**Rate Limits:** Leaky bucket algorithm, per-user per-minute. On 429, read the `Retry-After` header. Limits vary by plan tier and endpoint tier (1/2/3).

**Webhooks V2:** Event-driven notifications via `POST /v2/webhooks`. Authenticated with a `passcode` field echoed in each payload (not HMAC signatures).

**Image Export:** `GET /v1/images/:key` renders nodes as PNG/SVG/JPG/PDF. URLs expire after 30 days. SVGs always export at 1x regardless of scale parameter.

**Variables API:** Enterprise-only. `GET /v1/files/:key/variables/local` for design tokens. All other plans use the styles API (`file.styles` in the file response).

## Resources

- [Figma REST API](https://developers.figma.com/docs/rest-api/)
- [Figma Plugin API](https://developers.figma.com/docs/plugins/)
- [Figma Webhooks V2](https://developers.figma.com/docs/rest-api/webhooks/)
- [Figma API OpenAPI Spec](https://github.com/figma/rest-api-spec)
- [Figma Status Page](https://status.figma.com)

## License

MIT
