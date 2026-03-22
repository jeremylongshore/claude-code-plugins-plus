# Snowflake Skill Pack

> 30 production-grade Claude Code skills for Snowflake data platform development — real `snowflake-sdk`, `snowflake-connector-python`, and Snowflake SQL patterns.

## What's Inside

Real Snowflake code, not placeholders. Every skill uses actual Snowflake APIs: `snowflake.createConnection()`, `connection.execute()`, `cursor.execute()`, `COPY INTO`, `CREATE STREAM`, `CREATE TASK`, `MERGE INTO`, `ACCOUNT_USAGE` views, and more.

## Installation

```bash
/plugin install snowflake-pack@claude-code-plugins-plus
```

## Skills (30)

### Standard (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `snowflake-install-auth` | Install `snowflake-sdk`/`snowflake-connector-python`, configure key pair, OAuth, SSO auth |
| S02 | `snowflake-hello-world` | First queries with `connection.execute()`, parameterized binds, streaming results |
| S03 | `snowflake-local-dev-loop` | Dev warehouses, SnowSQL, vitest mocks, integration tests with temp tables |
| S04 | `snowflake-sdk-patterns` | Connection pooling, promise wrappers, streaming generators, context managers |
| S05 | `snowflake-core-workflow-a` | Data loading: stages, file formats, COPY INTO, Snowpipe auto-ingest |
| S06 | `snowflake-core-workflow-b` | Data transformation: streams, tasks, task DAGs, dynamic tables |
| S07 | `snowflake-common-errors` | Error codes 002003, 000606, 390100, 390144, 100038 with real fixes |
| S08 | `snowflake-debug-bundle` | QUERY_HISTORY diagnostics, LOGIN_HISTORY, WAREHOUSE_LOAD_HISTORY |
| S09 | `snowflake-rate-limits` | Warehouse concurrency, multi-cluster scaling, SQL API throttling |
| S10 | `snowflake-security-basics` | Network policies, key rotation, MFA, secret managers, audit queries |
| S11 | `snowflake-prod-checklist` | Resource monitors, warehouse config, RBAC audit, Snowflake alerts |
| S12 | `snowflake-upgrade-migration` | Driver upgrades, BCR bundles, Python connector breaking changes |

### Pro (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `snowflake-ci-integration` | SchemaChange migrations, GitHub Actions, Terraform provider |
| P14 | `snowflake-deploy-integration` | Serverless connections, Cloud Run, Lambda, Docker with key pair auth |
| P15 | `snowflake-webhooks-events` | Snowflake alerts, email notifications, external functions, Snowpipe events |
| P16 | `snowflake-performance-tuning` | Clustering keys, materialized views, query profiling, partition pruning |
| P17 | `snowflake-cost-tuning` | Resource monitors, auto-suspend, right-sizing, WAREHOUSE_METERING_HISTORY |
| P18 | `snowflake-reference-architecture` | Medallion pattern, bronze/silver/gold, warehouse strategy, role hierarchy |

### Flagship (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `snowflake-multi-env-setup` | Zero-copy clones, env-specific roles, masking policies, resource monitors |
| F20 | `snowflake-observability` | ACCOUNT_USAGE dashboards, Snowflake alerts, metrics export, pipeline health |
| F21 | `snowflake-incident-runbook` | Triage with QUERY_HISTORY, Time Travel rollback, UNDROP, stale stream recovery |
| F22 | `snowflake-data-handling` | Masking policies, row access policies, tagging, GDPR/CCPA stored procedures |
| F23 | `snowflake-enterprise-rbac` | System roles, custom hierarchy, SSO/SAML, SCIM provisioning, grant audits |
| F24 | `snowflake-migration-deep-dive` | Redshift/BigQuery migration, schema conversion, FLATTEN, write_pandas |

### Flagship+ (X25-X30)

| # | Skill | What It Does |
|---|-------|-------------|
| X25 | `snowflake-advanced-troubleshooting` | Query profile analysis, spill detection, lock contention, partition pruning |
| X26 | `snowflake-load-scale` | Warehouse benchmarking, concurrent load testing, multi-cluster config |
| X27 | `snowflake-reliability-patterns` | Replication, failover groups, Time Travel recovery, connection failover |
| X28 | `snowflake-policy-guardrails` | Network rules, authentication policies, session policies, CI governance |
| X29 | `snowflake-architecture-variants` | Lakehouse/Iceberg, data mesh/sharing, Snowpark-native, decision matrix |
| X30 | `snowflake-known-pitfalls` | Top 10 anti-patterns: always-on warehouses, stale streams, SELECT *, more |

## Key Technologies Covered

- **Drivers:** `snowflake-sdk` (Node.js), `snowflake-connector-python`, Snowpark Python
- **Data Loading:** Stages, COPY INTO, Snowpipe, file formats (CSV, JSON, Parquet)
- **Transformation:** Streams, Tasks, Dynamic Tables, MERGE INTO
- **Auth:** Key pair, OAuth, SSO/SAML, SCIM, MFA, authentication policies
- **Governance:** Masking policies, row access policies, tags, network policies
- **Monitoring:** ACCOUNT_USAGE views, QUERY_HISTORY, WAREHOUSE_METERING_HISTORY, alerts
- **Infrastructure:** Terraform, SchemaChange, zero-copy cloning, replication, failover
- **Advanced:** Iceberg tables, data sharing, Snowpark DataFrames, Cortex AI, external functions

## License

MIT
