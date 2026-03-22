---
name: clickhouse-prod-checklist
description: |
  Production readiness checklist for ClickHouse — server tuning, backup, monitoring,
  and deployment verification.
  Use when launching a ClickHouse deployment, doing go-live reviews,
  or auditing production readiness.
  Trigger: "clickhouse production", "clickhouse go-live", "clickhouse launch checklist",
  "production clickhouse", "clickhouse prod ready".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Production Checklist

## Overview

Comprehensive go-live checklist for ClickHouse covering server tuning, schema design,
backup configuration, monitoring, and operational readiness.

## Prerequisites

- ClickHouse instance provisioned (Cloud or self-hosted)
- Application integration code tested in staging

## Checklist

### 1. Schema & Engine Design

- [ ] Tables use `MergeTree` family engines (not `Memory`, `Log`, or `TinyLog`)
- [ ] `ORDER BY` columns match primary filter/group patterns
- [ ] `PARTITION BY` is coarse (monthly or weekly, never by ID)
- [ ] `TTL` configured for data retention policy
- [ ] `LowCardinality(String)` used for low-cardinality columns
- [ ] `CODEC(ZSTD)` applied to large String/JSON columns
- [ ] ReplacingMergeTree used with `FINAL` or dedup logic if upserts needed

### 2. Server Configuration (Self-Hosted)

```xml
<!-- Key production settings in config.xml / users.xml -->

<!-- Memory: set to ~80% of available RAM -->
<max_server_memory_usage_to_ram_ratio>0.8</max_server_memory_usage_to_ram_ratio>

<!-- Query limits -->
<max_concurrent_queries>150</max_concurrent_queries>
<max_memory_usage>10000000000</max_memory_usage>  <!-- 10GB per query -->
<max_execution_time>300</max_execution_time>       <!-- 5 min timeout -->

<!-- Merge settings -->
<background_pool_size>16</background_pool_size>
<background_schedule_pool_size>16</background_schedule_pool_size>

<!-- Logging -->
<query_log>
    <database>system</database>
    <table>query_log</table>
    <flush_interval_milliseconds>7500</flush_interval_milliseconds>
</query_log>
```

### 3. Backup Configuration

```sql
-- ClickHouse native BACKUP to S3
BACKUP TABLE analytics.events
    TO S3(
        'https://my-bucket.s3.us-east-1.amazonaws.com/backups/events',
        'ACCESS_KEY',
        'SECRET_KEY'
    )
    SETTINGS compression_method = 'zstd';

-- Incremental backup (base + delta)
BACKUP TABLE analytics.events
    TO S3('s3://my-bucket/backups/events-incremental')
    SETTINGS base_backup = S3('s3://my-bucket/backups/events-base');
```

**ClickHouse Cloud:** Backups are automatic. Configure retention and frequency
in the Cloud console under Service Settings.

- [ ] Backup schedule configured (daily minimum)
- [ ] Backup restore tested and documented
- [ ] Point-in-time recovery possible (incremental backups)
- [ ] Backup stored in different region/account from primary

### 4. Monitoring & Alerting

```sql
-- Key metrics to monitor
-- 1. Query latency (p50/p95/p99)
-- 2. Active parts per table (alert > 300)
-- 3. Merge queue depth
-- 4. Memory usage
-- 5. Disk space free
-- 6. Replication lag (if clustered)

-- Health check query (use for load balancer probes)
SELECT 1;

-- More thorough health check
SELECT
    (SELECT count() FROM system.processes) AS running_queries,
    (SELECT sum(value) FROM system.metrics WHERE metric = 'MemoryTracking') AS memory_bytes,
    (SELECT count() FROM system.merges) AS active_merges;
```

- [ ] Prometheus endpoint configured (`/metrics` via ClickHouse Exporter or Cloud endpoint)
- [ ] Grafana dashboard with key panels (QPS, latency, memory, parts, merges)
- [ ] Alerts on: error rate > 5%, p95 latency > 5s, parts > 300, disk < 20%
- [ ] Query log monitoring for slow/failed queries

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
- [ ] Health check endpoint includes ClickHouse ping

```typescript
// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const { success } = await client.ping();
    res.json({ status: success ? 'healthy' : 'degraded', clickhouse: success });
  } catch {
    res.status(503).json({ status: 'unhealthy', clickhouse: false });
  }
});
```

### 7. Operational Readiness

- [ ] Incident runbook documented (see `clickhouse-incident-runbook`)
- [ ] On-call escalation path defined
- [ ] Key rotation procedure documented
- [ ] Schema migration process in place (see `clickhouse-migration-deep-dive`)
- [ ] Load testing completed at expected peak traffic

### 8. Verification Queries

```sql
-- Verify table sizes and part health
SELECT database, table, count() AS parts, sum(rows) AS rows,
       formatReadableSize(sum(bytes_on_disk)) AS size
FROM system.parts WHERE active
GROUP BY database, table ORDER BY sum(bytes_on_disk) DESC;

-- Verify no pending mutations
SELECT * FROM system.mutations WHERE NOT is_done;

-- Verify no replication lag
SELECT database, table, queue_size, inserts_in_queue
FROM system.replicas WHERE queue_size > 0;
```

## Error Handling

| Issue | Detection | Action |
|-------|-----------|--------|
| Parts > 300 | Monitoring alert | Review insert patterns, wait for merges |
| Disk > 80% | Disk alert | Add storage, drop old partitions |
| Query p95 > 5s | Latency alert | Check `system.query_log` for slow queries |
| Replication lag | Replica check | Investigate network, merge backlog |

## Resources

- [ClickHouse Operations Guide](https://clickhouse.com/docs/operations)
- [Backup & Restore](https://clickhouse.com/docs/operations/backup)
- [Monitoring with Prometheus](https://clickhouse.com/docs/integrations/prometheus)

## Next Steps

For SDK version upgrades, see `clickhouse-upgrade-migration`.
