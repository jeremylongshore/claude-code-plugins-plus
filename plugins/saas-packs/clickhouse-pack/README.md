# ClickHouse Skill Pack

> 24 skills for building, operating, and scaling ClickHouse-powered analytics — real `@clickhouse/client` code, real SQL, real MergeTree engines.

Every skill uses the **official ClickHouse Node.js client** (`@clickhouse/client` with `createClient`), actual ClickHouse SQL syntax (MergeTree, ReplacingMergeTree, AggregatingMergeTree), real system tables (`system.parts`, `system.query_log`, `system.merges`), and production patterns (parameterized queries, streaming inserts, materialized views).

**Links:** [tonsofskills.com](https://tonsofskills.com) | [ClickHouse Docs](https://clickhouse.com/docs) | [@clickhouse/client](https://github.com/ClickHouse/clickhouse-js)

---

## Installation

```bash
/plugin install clickhouse-pack@claude-code-plugins-plus
```

## Skills (24)

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `clickhouse-install-auth` | Install `@clickhouse/client`, configure Cloud/self-hosted connection, verify with ping + version query |
| S02 | `clickhouse-hello-world` | Create MergeTree table, insert with JSONEachRow, query with GROUP BY, explore system.parts |
| S03 | `clickhouse-local-dev-loop` | Docker Compose setup, init SQL scripts, seed data, vitest integration tests, CLI shortcuts |
| S04 | `clickhouse-sdk-patterns` | Typed query helper, streaming inserts with backpressure, batch retry, streaming SELECT, error handling |
| S05 | `clickhouse-core-workflow-a` | Schema design — engine selection, ORDER BY key design, partitioning, codecs, compression |
| S06 | `clickhouse-core-workflow-b` | Bulk inserts, analytical queries, parameterized queries, materialized views, window functions |
| S07 | `clickhouse-common-errors` | Top 10 error codes (252, 241, 62, 60, 159) with diagnostic SQL and real fixes |
| S08 | `clickhouse-debug-bundle` | Diagnostic queries against system tables, automated bash collector, Node.js debug bundle |
| S09 | `clickhouse-rate-limits` | Server concurrency limits, per-user quotas, connection pooling, insert buffer pattern |
| S10 | `clickhouse-security-basics` | SQL-based user creation, roles, row-level security, TLS config, audit logging |
| S11 | `clickhouse-prod-checklist` | Go-live checklist: schema, backup (BACKUP TO S3), monitoring, security, health checks |
| S12 | `clickhouse-upgrade-migration` | Server + client version upgrades, breaking change detection, validation scripts, rollback |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `clickhouse-ci-integration` | GitHub Actions with ClickHouse service container, schema validation tests, version matrix |
| P14 | `clickhouse-deploy-integration` | Deploy to Vercel/Fly.io/Cloud Run with ClickHouse Cloud connections, secrets, health checks |
| P15 | `clickhouse-webhooks-events` | Data ingestion — webhook batching, Kafka table engine, ClickPipes, HTTP bulk insert, S3 import |
| P16 | `clickhouse-performance-tuning` | EXPLAIN PLAN, ORDER BY optimization, data skipping indexes, projections, server settings |
| P17 | `clickhouse-cost-tuning` | Storage analysis, compression codecs, TTL tiers, compute scaling, query cost tracking |
| P18 | `clickhouse-reference-architecture` | 3-layer schema (raw → hourly → daily), multi-tenant patterns, data flow diagrams |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `clickhouse-multi-env-setup` | Dev/staging/prod config, secrets management (Vault/AWS/GCP), environment guards, CI/CD integration |
| F20 | `clickhouse-observability` | Prometheus metrics, Grafana dashboards, system table monitoring, alert rules, structured logging |
| F21 | `clickhouse-incident-runbook` | P1-P4 triage procedures, KILL QUERY, disk full recovery, merge backlog, communication templates |
| F22 | `clickhouse-data-handling` | TTL expiration, GDPR deletion (lightweight DELETE + mutations), data masking, audit trails |
| F23 | `clickhouse-enterprise-rbac` | SQL-based RBAC — users, roles, row policies, column grants, quotas, settings profiles |
| F24 | `clickhouse-migration-deep-dive` | ALTER TABLE operations, ORDER BY changes, engine migration, versioned migration runner |

## What Makes This Different

These are **not** generic SaaS API wrappers. Every skill is built from actual ClickHouse documentation and real-world patterns:

- **Real imports:** `import { createClient } from '@clickhouse/client'` (the official client)
- **Real SQL:** `ENGINE = MergeTree() ORDER BY (tenant_id, event_type, created_at) PARTITION BY toYYYYMM(created_at)`
- **Real system tables:** `system.parts`, `system.query_log`, `system.merges`, `system.mutations`
- **Real error codes:** 252 (TOO_MANY_PARTS), 241 (MEMORY_LIMIT_EXCEEDED), 62 (SYNTAX_ERROR)
- **Real patterns:** Streaming inserts with backpressure, materialized views with AggregateFunction states, parameterized queries with `{name:Type}` syntax

## License

MIT
