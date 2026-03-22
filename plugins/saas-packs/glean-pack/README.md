# Glean Skill Pack

> 24 production-ready Claude Code skills for Glean enterprise search -- real Indexing API and Client API code with actual endpoints.

## What This Is

A complete skill pack for building, deploying, and operating Glean enterprise search integrations. Every skill contains real Glean REST API code: custom datasource creation, document indexing (individual and bulk), search queries, AI chat, and permission management. Uses the actual Glean Indexing API (`/index/v1/`) and Client API (`/client/v1/`) endpoints.

## Installation

```bash
/plugin install glean-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `glean-install-auth` | Configure indexing and client API tokens, verify both APIs |
| S02 | `glean-hello-world` | Create datasource, index documents, search them back |
| S03 | `glean-local-dev-loop` | Mock search responses, test connector transforms, Vitest |
| S04 | `glean-sdk-patterns` | Typed GleanClient class, bulk indexing, search with filters |
| S05 | `glean-core-workflow-a` | Search with filters/facets, AI chat, autocomplete |
| S06 | `glean-core-workflow-b` | Bulk indexing, custom connectors, permissions, document deletion |
| S07 | `glean-common-errors` | Fix 401/403, empty results, bulk upload errors, permissions |
| S08 | `glean-debug-bundle` | Collect datasource config, search test, indexing status |
| S09 | `glean-rate-limits` | Batch sizing, backoff strategies, indexing throughput |
| S10 | `glean-security-basics` | Token scoping, document permissions, SSO integration |
| S11 | `glean-prod-checklist` | Datasource verification, search quality, connector scheduling |
| S12 | `glean-upgrade-migration` | API version migration, SDK updates, schema changes |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `glean-ci-integration` | Automated connector testing, search quality validation |
| P14 | `glean-deploy-integration` | Deploy connectors to Cloud Run, Lambda, Fly.io |
| P15 | `glean-webhooks-events` | Event-driven indexing from source system webhooks |
| P16 | `glean-performance-tuning` | Search relevance tuning, indexing throughput optimization |
| P17 | `glean-cost-tuning` | Efficient indexing, datasource management, content pruning |
| P18 | `glean-reference-architecture` | Enterprise search architecture with custom connectors |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `glean-multi-env-setup` | Staging/production datasource isolation, token separation |
| F20 | `glean-observability` | Indexing metrics, search quality tracking, alerting |
| F21 | `glean-incident-runbook` | Search outage triage, stale content, connector failures |
| F22 | `glean-data-handling` | PII filtering, document classification, retention policies |
| F23 | `glean-enterprise-rbac` | Group-based permissions, SSO mapping, admin roles |
| F24 | `glean-migration-deep-dive` | Migrate from Elasticsearch/Algolia to Glean |

## Key Glean API Concepts

- **Indexing API**: `POST /api/index/v1/indexdocuments` with `Authorization: Bearer <indexing_token>`
- **Client API**: `POST /api/client/v1/search` with `Authorization: Bearer <client_token>` + `X-Glean-Auth-Type: BEARER`
- **Bulk indexing**: `/bulkindexdocuments` with `uploadId` for full datasource refresh
- **Custom datasources**: `/adddatasource` to register new content sources
- **Permissions**: Document-level via `allowedUsers`, `allowedGroups`, or `allowAnonymousAccess`
- **Chat/AI**: `/client/v1/chat` for AI-powered answers with citations

## License

MIT
