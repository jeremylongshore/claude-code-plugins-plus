# Databricks Skill Pack

> 24 production-ready skills for the Databricks Lakehouse Platform — Unity Catalog, Delta Lake, MLflow, Spark SQL, Asset Bundles, and the full REST API.

## Installation

```bash
/plugin install databricks-pack@claude-code-plugins-plus
```

## What It Does

This pack gives Claude Code deep operational knowledge of Databricks: real REST API endpoints (`/api/2.1/jobs/*`, `/api/2.0/clusters/*`), real Python SDK patterns (`databricks-sdk` WorkspaceClient, typed error handling), real Spark SQL (Auto Loader, MERGE INTO, OPTIMIZE, Liquid Clustering), and real deployment workflows (Declarative Automation Bundles, GitHub Actions CI/CD).

Every skill contains working code, not placeholder templates.

## Skills (24)

### Standard (S01-S12)

| Skill | What It Covers |
|-------|---------------|
| `databricks-install-auth` | CLI v2, Python SDK, PAT/OAuth U2M/OAuth M2M, profiles |
| `databricks-hello-world` | First cluster, notebook upload, runs/submit, SQL warehouse |
| `databricks-local-dev-loop` | Databricks Connect v2, pytest fixtures, Asset Bundle sync |
| `databricks-sdk-patterns` | Singleton client, typed errors, cluster lifecycle, job builder |
| `databricks-core-workflow-a` | Medallion ETL: Auto Loader, MERGE upserts, DLT pipelines |
| `databricks-core-workflow-b` | Feature Store, MLflow tracking, model registry, serving endpoints |
| `databricks-common-errors` | OOM, concurrent writes, permissions, schema mismatch, 429 |
| `databricks-debug-bundle` | Diagnostic tar.gz: cluster events, run output, driver logs |
| `databricks-rate-limits` | Exponential backoff, token-bucket, idempotent submissions |
| `databricks-security-basics` | Secret scopes, token rotation, column masking, audit queries |
| `databricks-prod-checklist` | Pre-deploy checklist, job YAML, rollback procedure |
| `databricks-upgrade-migration` | DBR version upgrade, Hive-to-Unity-Catalog, protocol upgrade |

### Pro (P13-P18)

| Skill | What It Covers |
|-------|---------------|
| `databricks-ci-integration` | GitHub Actions, bundle validation, unit tests, OIDC auth |
| `databricks-deploy-integration` | Declarative Automation Bundles, targets, variables, permissions |
| `databricks-webhooks-events` | Notification destinations, SQL alerts, system table auditing |
| `databricks-performance-tuning` | Cluster sizing, AQE, Liquid Clustering, Z-order, query plans |
| `databricks-cost-tuning` | Billing tables, cluster policies, spot instances, instance pools |
| `databricks-reference-architecture` | Lakehouse layout, Unity Catalog hierarchy, maintenance jobs |

### Flagship (F19-F24)

| Skill | What It Covers |
|-------|---------------|
| `databricks-multi-env-setup` | Dev/staging/prod profiles, per-env secrets, Terraform |
| `databricks-observability` | System tables, job health, cost-per-job, SQL alerts, Prometheus |
| `databricks-incident-runbook` | Triage script, decision tree, evidence collection, postmortem |
| `databricks-data-handling` | GDPR deletion, PII masking, retention enforcement, row-level security |
| `databricks-enterprise-rbac` | SCIM groups, Unity Catalog grants, cluster policies, service principals |
| `databricks-migration-deep-dive` | Hadoop/Snowflake/Redshift migration, schema conversion, cutover |

## Key APIs Covered

| API | Endpoints |
|-----|-----------|
| Jobs API 2.1 | `POST /api/2.1/jobs/create`, `runs/submit`, `run-now` |
| Clusters API 2.0 | `create`, `list`, `start`, `delete`, `events` |
| SQL Statement API | `execute-statement` |
| Unity Catalog | `catalogs`, `schemas`, `tables`, `grants` |
| DBFS / Files API | `put`, `get`, `list` |
| Secrets API | `create-scope`, `put-secret`, `list-acls` |
| SCIM API | `groups`, `users`, `service-principals` |
| Model Serving | `serving-endpoints/create`, `query` |

## Usage

Skills trigger automatically on Databricks topics:

- "Set up Databricks auth" -- `databricks-install-auth`
- "Build a Delta Lake pipeline" -- `databricks-core-workflow-a`
- "Deploy my Databricks job" -- `databricks-deploy-integration`
- "Optimize my Spark queries" -- `databricks-performance-tuning`
- "Set up Unity Catalog permissions" -- `databricks-enterprise-rbac`
- "Migrate from Snowflake" -- `databricks-migration-deep-dive`

## Architecture

### Why two MCP servers, not one

The v2 rebuild ships with a deliberate split across **two** MCP servers, not a single shared one. Common question on contributor PRs — answering it once at the top so future readers don't have to re-derive it.

- **Databricks managed SQL MCP** — serves `system.*` reads (cost data, query history, streaming progress). Operated by Databricks; we consume it.
- **Custom workspace MCP** — serves cluster events, instance pools, pipeline event logs, external locations, storage credentials. Operated by this pack.

The two authenticate independently. Losing access to one does not disable the other; `cost-leak-hunter` (SQL MCP) and `cluster-forensics` (workspace MCP) fail independently when their respective MCP is unavailable. Single skills can be installed without pulling in the other MCP's dependency surface.

Full scope-boundary rationale — including the 8 → 6 endpoint cut and the auth-flow decisions — is in [`000-docs/013-AT-ADEC-epic1-mcp-scope-adjustment.md`](000-docs/013-AT-ADEC-epic1-mcp-scope-adjustment.md). Reference document for any "why is this skill not pulling X?" question.

Thanks to [@Gingiris-1031](https://github.com/Gingiris-1031) ([#795](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/795)) for surfacing the isolation-story framing that made this section necessary.

## Design Records

All architecture decisions, pain research, and pressure tests for this pack live in [`000-docs/`](000-docs/). Index: [`000-INDEX.md`](000-docs/000-INDEX.md).

## License

MIT
