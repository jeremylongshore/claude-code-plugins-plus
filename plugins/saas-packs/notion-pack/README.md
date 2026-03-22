# Notion Skill Pack

> 30 production-ready skills for building Notion API integrations with `@notionhq/client`

Real API code. Real filter syntax. Real error handling. No placeholders.

## What You Get

Every skill uses the official `@notionhq/client` SDK with actual Notion API patterns: database queries with typed filters, page creation with all property types, block content operations, rich text annotations, pagination, rate limit handling, webhook events, and OAuth flows.

## Installation

```bash
/plugin install notion-pack@claude-code-plugins-plus
```

## Skills (30)

### Getting Started (S01-S12)
| Skill | What It Does |
|-------|-------------|
| `notion-install-auth` | Install `@notionhq/client`, create integration, configure OAuth |
| `notion-hello-world` | First API calls: search, query, create pages, append blocks |
| `notion-local-dev-loop` | Dev environment with hot reload, mocked tests, integration tests |
| `notion-sdk-patterns` | Singleton client, typed error handling, pagination helpers, property extractors |
| `notion-core-workflow-a` | Database queries with all filter types, page CRUD with typed properties |
| `notion-core-workflow-b` | Block content: append/read/update, rich text, comments, nested trees |
| `notion-common-errors` | Every Notion error code (401, 403, 404, 400, 429, 409, 502) with fixes |
| `notion-debug-bundle` | Diagnostic bundle: connectivity, SDK version, platform status, redacted logs |
| `notion-rate-limits` | 3 req/s limit handling: SDK retry, p-queue throttling, batch processing |
| `notion-security-basics` | Token management, least-privilege capabilities, page-level access, rotation |
| `notion-prod-checklist` | Production readiness: auth, error handling, monitoring, data integrity, rollback |
| `notion-upgrade-migration` | SDK upgrades, API version migration, 2025-09-03 data source model |

### Integration (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `notion-ci-integration` | GitHub Actions with mocked unit tests + gated live API integration tests |
| `notion-deploy-integration` | Deploy to Vercel, Fly.io, Cloud Run with secrets management |
| `notion-webhooks-events` | Webhook receiver: verification, event handling, idempotent processing |
| `notion-performance-tuning` | Caching, efficient pagination, parallel fetches, block batching |
| `notion-cost-tuning` | Reduce API volume: filters, timestamps, webhooks over polling |
| `notion-reference-architecture` | Layered project structure with extractors, services, error classification |

### Enterprise (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `notion-multi-env-setup` | Per-environment integrations, secret management, environment guards |
| `notion-observability` | Prometheus metrics, structured logging, health checks, alert rules |
| `notion-incident-runbook` | Triage script, decision tree, mitigation by error type, postmortem template |
| `notion-data-handling` | PII detection in properties, redaction, GDPR export/deletion, retention |
| `notion-enterprise-rbac` | OAuth 2.0 multi-workspace, token storage, permission-aware API calls |
| `notion-migration-deep-dive` | CSV/JSON import, database export, cross-database sync, validation |

### Advanced (X25-X30)
| Skill | What It Does |
|-------|-------------|
| `notion-advanced-troubleshooting` | Debug logging, raw curl testing, request ID tracking, schema validation |
| `notion-load-scale` | Throughput benchmarks, k6 load tests, multi-token scaling, capacity planning |
| `notion-reliability-patterns` | Circuit breaker, cached fallback, idempotent creates, dead letter queue |
| `notion-policy-guardrails` | Secret scanning, ESLint rules, CI policy checks, TypeScript type guards |
| `notion-architecture-variants` | Direct/Service/Event-driven patterns with decision matrix |
| `notion-known-pitfalls` | 10 common mistakes with correct patterns (wrong imports, missing pagination, etc.) |

## Key Notion Concepts Covered

- **Property types:** title, rich_text, number, select, multi_select, date, checkbox, url, email, phone_number, people, relation, formula, rollup
- **Filter syntax:** All property-specific filter conditions with compound and/or
- **Block types:** paragraph, headings, lists, to_do, code, callout, quote, toggle, divider
- **Rich text:** Annotations (bold, italic, code, color), links, mentions, equations
- **Pagination:** Cursor-based with `start_cursor` and `has_more`
- **Rate limits:** 3 req/s average, `Retry-After` header, SDK built-in retry
- **Authentication:** Internal tokens (`ntn_*`), OAuth 2.0 for public integrations
- **Webhooks:** Event types, verification handshake, idempotent processing

## License

MIT
