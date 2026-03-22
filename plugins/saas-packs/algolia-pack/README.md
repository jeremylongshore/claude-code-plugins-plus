# Algolia Skill Pack

> 24 production-ready Claude Code skills for Algolia search — real `algoliasearch` v5 API code, not templates.

## What This Is

A complete skill pack for building, deploying, and operating Algolia-powered search. Every skill contains real Algolia v5 JavaScript client code: `saveObjects`, `searchSingleIndex`, `setSettings`, `replaceAllObjects`, `generateSecuredApiKey`, and more. No placeholder imports, no fake API patterns.

## Installation

```bash
/plugin install algolia-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `algolia-install-auth` | Install `algoliasearch` v5, configure App ID + API keys, verify connection |
| S02 | `algolia-hello-world` | Index records with `saveObjects`, search with `searchSingleIndex`, configure settings |
| S03 | `algolia-local-dev-loop` | Dev index prefixing, seed scripts, Vitest mocking, integration tests |
| S04 | `algolia-sdk-patterns` | Singleton client, typed search results, `ApiError` handling, batch operations |
| S05 | `algolia-core-workflow-a` | Search with filters, facets, highlighting, pagination, `optionalFilters` |
| S06 | `algolia-core-workflow-b` | Indexing pipeline: `replaceAllObjects`, `partialUpdateObject`, synonyms, query rules |
| S07 | `algolia-common-errors` | Fix 403, 404, 429, `RetryError`, record-too-big, invalid filter syntax |
| S08 | `algolia-debug-bundle` | Collect index stats, API key ACLs, query logs, network diagnostics |
| S09 | `algolia-rate-limits` | Per-key limits, indexing queue limits, backoff strategies, `p-queue` throttling |
| S10 | `algolia-security-basics` | Key scoping, Secured API Keys, referer restrictions, key rotation |
| S11 | `algolia-prod-checklist` | Index settings audit, replica config, health checks, graceful degradation |
| S12 | `algolia-upgrade-migration` | v4 to v5 migration: `initIndex` removal, import changes, method renames |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `algolia-ci-integration` | GitHub Actions workflows, settings validation, integration tests, deploy-triggered reindex |
| P14 | `algolia-deploy-integration` | Vercel/Fly.io/Cloud Run deployment, InstantSearch.js + React InstantSearch frontend |
| P15 | `algolia-webhooks-events` | Insights API (click/conversion tracking), Analytics API, DB-to-Algolia sync pipelines |
| P16 | `algolia-performance-tuning` | Record optimization, `filterOnly()` faceting, caching, virtual replicas, query tuning |
| P17 | `algolia-cost-tuning` | Pricing breakdown, virtual replicas, multi-query batching, usage monitoring |
| P18 | `algolia-reference-architecture` | Index design, record transforms, settings-as-code, search service layer |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `algolia-multi-env-setup` | Index prefixing, scoped keys per environment, settings-as-code, isolation guards |
| F20 | `algolia-observability` | Prometheus metrics, OpenTelemetry tracing, pino structured logging, Grafana dashboards |
| F21 | `algolia-incident-runbook` | Triage script, decision tree, circuit breaker fallback, postmortem template |
| F22 | `algolia-data-handling` | PII filtering, Secured API Keys for RBAC, GDPR deletion, data retention |
| F23 | `algolia-enterprise-rbac` | ACL-scoped keys, multi-tenant Secured API Keys, key audit, dashboard team roles |
| F24 | `algolia-migration-deep-dive` | Elasticsearch/Typesense migration, query translation, strangler fig cutover |

## Usage

Skills trigger automatically when you discuss Algolia topics:

- "Help me set up Algolia" -> `algolia-install-auth`
- "Search not returning results" -> `algolia-common-errors`
- "Migrate from Elasticsearch" -> `algolia-migration-deep-dive`
- "Optimize Algolia costs" -> `algolia-cost-tuning`

## Key Algolia Concepts Covered

- **Client initialization**: `algoliasearch(appId, apiKey)` — no more `initIndex` in v5
- **Indexing**: `saveObjects`, `partialUpdateObject`, `replaceAllObjects`, `deleteBy`
- **Search**: `searchSingleIndex`, `search` (multi-index), `browse` (export)
- **Configuration**: `setSettings`, `saveSynonyms`, `saveRule`
- **Security**: Secured API Keys, ACL-scoped keys, `referers`, `maxQueriesPerIPPerHour`
- **Analytics**: Insights API (clicks/conversions), Analytics API (top searches, no-results)
- **Frontend**: InstantSearch.js, React InstantSearch, `liteClient`

## License

MIT
