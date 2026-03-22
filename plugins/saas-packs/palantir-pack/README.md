# Palantir Foundry Skill Pack

> Claude Code skill pack for Palantir Foundry — Ontology SDK, data pipelines, transforms, and enterprise data integration (24 skills)

## What This Covers

Palantir Foundry is an enterprise data platform with an Ontology layer that models real-world objects, actions, and relationships. This pack covers the **Foundry Platform SDK** (Python) for direct API access, the **OSDK** (TypeScript/Python) for Ontology-driven applications, and **transforms-python** for Spark-based data pipelines.

**Key APIs:** Ontology Objects (CRUD, search, aggregation), Actions (mutations with validation), Datasets (read/write/upload), Transforms (`@transform_df`, `@incremental`, `@configure`), OAuth2 authentication (client credentials + bearer tokens).

## Installation

```bash
/plugin install palantir-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `palantir-install-auth` | Install `foundry-platform-sdk` or `@osdk/client`, configure OAuth2 or bearer token auth |
| `palantir-hello-world` | First Ontology query — list objects, get by primary key, apply an action |
| `palantir-local-dev-loop` | Local PySpark testing, mocked API clients, pytest fixtures |
| `palantir-sdk-patterns` | Singleton clients, typed error handling, pagination helpers, retry logic |
| `palantir-core-workflow-a` | Build data pipelines with `@transform_df`, `@incremental`, multi-input joins |
| `palantir-core-workflow-b` | Query Ontology objects, follow links, apply actions, aggregate data |
| `palantir-common-errors` | Fix top 10 Foundry errors: 401, 403, ObjectTypeNotFound, OOM, AnalysisException |
| `palantir-debug-bundle` | Collect SDK versions, API connectivity, error logs into redacted tarball |
| `palantir-rate-limits` | Exponential backoff, token bucket rate limiter, batch processing |
| `palantir-security-basics` | Credential storage, scope management, secret rotation, pre-commit hooks |
| `palantir-prod-checklist` | Go-live checklist: health checks, monitoring, alerting, rollback |
| `palantir-upgrade-migration` | Upgrade `foundry-platform-sdk` versions, handle breaking changes |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `palantir-ci-integration` | GitHub Actions with PySpark tests, Foundry linting, integration smoke tests |
| `palantir-deploy-integration` | Deploy to Cloud Run/Docker with secrets management and health checks |
| `palantir-webhooks-events` | Handle Ontology change events, dataset updates, signature verification |
| `palantir-performance-tuning` | Pagination optimization, TTL caching, batch retrieval, Spark tuning |
| `palantir-cost-tuning` | Incremental transforms, right-sized profiles, webhook vs polling |
| `palantir-reference-architecture` | 3-layer pipeline (raw/clean/model), Ontology design, security layers |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `palantir-multi-env-setup` | Dev/staging/prod with separate hostnames, credentials, and scopes |
| `palantir-observability` | Prometheus metrics, structured logging, Grafana dashboards, alert rules |
| `palantir-incident-runbook` | Triage playbooks for auth failures, rate limits, transform build errors |
| `palantir-data-handling` | PII redaction, Foundry Markings, GDPR deletion, data retention |
| `palantir-enterprise-rbac` | Project roles, service users, group-based access, scope matrices |
| `palantir-migration-deep-dive` | Bulk import, incremental sync, strangler fig pattern, validation |

## Usage

Skills trigger automatically when you discuss Palantir Foundry topics:

- "Set up Palantir SDK" -- triggers `palantir-install-auth`
- "Query Ontology objects" -- triggers `palantir-core-workflow-b`
- "Build a data pipeline" -- triggers `palantir-core-workflow-a`
- "Fix Foundry 403 error" -- triggers `palantir-common-errors`
- "Deploy Foundry integration" -- triggers `palantir-deploy-integration`

## Key Documentation

- [Foundry API Reference](https://www.palantir.com/docs/foundry/api/general/overview/introduction)
- [Python SDK](https://github.com/palantir/foundry-platform-python)
- [OSDK Overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview)
- [Transforms Guide](https://www.palantir.com/docs/foundry/transforms-python/transforms)

## License

MIT
