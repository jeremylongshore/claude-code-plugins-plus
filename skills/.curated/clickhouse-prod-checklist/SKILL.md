---
name: clickhouse-prod-checklist
description: |
  Production readiness checklist for ClickHouse — server tuning, backup,
  monitoring, and deployment verification.
  Use when launching a ClickHouse deployment, doing a go-live review,
  or auditing production readiness before flipping traffic.
  Trigger with "clickhouse production", "clickhouse go-live",
  "clickhouse launch checklist", "production clickhouse",
  "clickhouse prod ready".
allowed-tools: Read, Bash(clickhouse-client:*), Bash(curl:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Production Checklist

## Overview

Comprehensive go-live checklist for ClickHouse covering schema and engine design,
server tuning, backup configuration, monitoring, security, application
integration, and operational readiness. Walk the eight sections top to bottom;
each is a gate that must be green before production traffic is allowed. Deep
configuration — server XML, backup SQL, and verification queries — lives in
`references/` so this file stays a fast operational scan.

## Prerequisites

Before starting the checklist, confirm the following are in place:

- A ClickHouse instance is provisioned (ClickHouse Cloud or self-hosted) and
  reachable from the environment you will run traffic from.
- Application integration code has been exercised end-to-end in a staging
  environment against a ClickHouse of the same major version.
- You have admin credentials able to read `system.*` tables and, for
  self-hosted, edit `config.xml` / `users.xml`.

## Instructions

Work each section in order. Every box must be checked (or explicitly waived with
a reason) before go-live.

### 1. Schema & Engine Design

- [ ] Tables use `MergeTree` family engines (not `Memory`, `Log`, or `TinyLog`)
- [ ] `ORDER BY` columns match primary filter/group patterns
- [ ] `PARTITION BY` is coarse (monthly or weekly, never by ID)
- [ ] `TTL` configured for data retention policy
- [ ] `LowCardinality(String)` used for low-cardinality columns
- [ ] `CODEC(ZSTD)` applied to large String/JSON columns
- [ ] ReplacingMergeTree used with `FINAL` or dedup logic if upserts needed

### 2. Server Configuration (Self-Hosted)

Set memory to ~80% of RAM, cap per-query memory and execution time, and size the
merge pools to the core count. ClickHouse Cloud manages these for you.

```xml
<max_server_memory_usage_to_ram_ratio>0.8</max_server_memory_usage_to_ram_ratio>
<max_concurrent_queries>150</max_concurrent_queries>
<max_execution_time>300</max_execution_time>  <!-- 5 min: cap runaway scans -->
```

Full annotated `config.xml` / `users.xml` block and tuning rationale:
[server configuration reference](references/server-config.md).

### 3. Backup Configuration

- [ ] Backup schedule configured (daily minimum)
- [ ] Backup restore tested and documented
- [ ] Point-in-time recovery possible (incremental backups)
- [ ] Backup stored in different region/account from primary

Native `BACKUP ... TO S3` syntax, incremental base+delta backups, and recovery
drill guidance: [backup & recovery reference](references/backup-and-recovery.md).

### 4. Monitoring & Alerting

- [ ] Prometheus endpoint configured (`/metrics` via Exporter or Cloud endpoint)
- [ ] Grafana dashboard with key panels (QPS, latency, memory, parts, merges)
- [ ] Alerts on: error rate > 5%, p95 latency > 5s, parts > 300, disk < 20%
- [ ] Query log monitoring for slow/failed queries

Health-check queries and the full metrics list:
[monitoring & verification reference](references/monitoring-and-verification.md).

### 5. Security

- [ ] Default user password changed or user disabled
- [ ] Application user has minimal privileges (see `clickhouse-security-basics`)
- [ ] TLS enabled (HTTPS on port 8443)
- [ ] IP allowlist configured
- [ ] Secrets in environment variables or secret manager (not code)

### 6. Application Integration

- [ ] Connection pooling configured (`max_open_connections`)
- [ ] Graceful shutdown calls `client.close()`
- [ ] Insert batching in place (10K+ rows per INSERT)
- [ ] Retry logic for transient errors (see `clickhouse-rate-limits`)
- [ ] Health check endpoint includes ClickHouse ping (see reference for the
      TypeScript `/health` handler)

### 7. Operational Readiness

- [ ] Incident runbook documented (see `clickhouse-incident-runbook`)
- [ ] On-call escalation path defined
- [ ] Key rotation procedure documented
- [ ] Schema migration process in place (see `clickhouse-migration-deep-dive`)
- [ ] Load testing completed at expected peak traffic

### 8. Verification Queries

Immediately before flipping traffic, run the three go-live verification queries
(part health, pending mutations, replication lag) from the
[monitoring & verification reference](references/monitoring-and-verification.md)
under "Go-live verification queries". A clean launch returns zero rows from the
mutations and replicas queries.

## Output

Completing this checklist produces a go / no-go readiness decision:

- **Section-by-section status** — each of the eight gates marked pass, or failed
  with the specific unchecked item.
- **Verification query results** — part-health, mutation, and replication-lag
  output captured as launch evidence.
- **Go-live decision** — GO only when all eight sections are green and the
  verification queries return the expected clean-launch results; otherwise a
  NO-GO with the blocking items listed.

## Error Handling

| Issue | Detection | Action |
|-------|-----------|--------|
| Parts > 300 | Monitoring alert | Review insert patterns, wait for merges |
| Disk > 80% | Disk alert | Add storage, drop old partitions |
| Query p95 > 5s | Latency alert | Check `system.query_log` for slow queries |
| Replication lag | Replica check | Investigate network, merge backlog |

## Examples

**Minimal health probe** (load-balancer readiness check):

```sql
SELECT 1;
```

**Go-live part-health check** (fails the launch if any table exceeds its
active-parts threshold):

```sql
SELECT database, table, count() AS parts, sum(rows) AS rows,
       formatReadableSize(sum(bytes_on_disk)) AS size
FROM system.parts WHERE active
GROUP BY database, table ORDER BY sum(bytes_on_disk) DESC;
```

For the full thorough health-check query, the incremental S3 backup example, and
the annotated server-config block, see the `references/` files linked from each
section above.

## Resources

- [ClickHouse Operations Guide](https://clickhouse.com/docs/operations)
- [Backup & Restore](https://clickhouse.com/docs/operations/backup)
- [Monitoring with Prometheus](https://clickhouse.com/docs/integrations/prometheus)
- [server configuration reference](references/server-config.md)
- [backup & recovery reference](references/backup-and-recovery.md)
- [monitoring & verification reference](references/monitoring-and-verification.md)

## Next Steps

After a clean go-live, keep the deployment healthy: schedule a periodic backup
restore drill, wire the monitoring alerts into your on-call rotation, and review
`clickhouse-incident-runbook` for response procedures. For SDK version upgrades,
see `clickhouse-upgrade-migration`.
