---
name: clickhouse-observability
description: |
  Monitor ClickHouse with Prometheus metrics, Grafana dashboards, system table queries,
  and alerting for query performance, merge health, and resource usage.
  Use when setting up ClickHouse monitoring, building Grafana dashboards,
  or configuring alerts for production ClickHouse deployments.
  Trigger: "clickhouse monitoring", "clickhouse metrics", "clickhouse Grafana",
  "clickhouse observability", "monitor clickhouse", "clickhouse Prometheus".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Observability

## Overview

Set up comprehensive monitoring for ClickHouse using built-in system tables,
Prometheus integration, Grafana dashboards, and alerting rules.

## Prerequisites

- ClickHouse instance with `system.*` table access
- Prometheus (or compatible: Grafana Alloy, Victoria Metrics)
- Grafana for dashboards
- AlertManager or PagerDuty for alerts

## Instructions

### Step 1: Key Metrics from System Tables

```sql
-- Real-time server health snapshot
SELECT
    (SELECT count() FROM system.processes) AS running_queries,
    (SELECT value FROM system.metrics WHERE metric = 'MemoryTracking') AS memory_bytes,
    (SELECT value FROM system.metrics WHERE metric = 'Query') AS concurrent_queries,
    (SELECT count() FROM system.merges) AS active_merges,
    (SELECT value FROM system.asynchronous_metrics WHERE metric = 'Uptime') AS uptime_sec;

-- Query throughput (last hour, per minute)
SELECT
    toStartOfMinute(event_time) AS minute,
    count() AS queries,
    countIf(exception_code != 0) AS errors,
    round(avg(query_duration_ms)) AS avg_ms,
    round(quantile(0.95)(query_duration_ms)) AS p95_ms,
    formatReadableSize(sum(read_bytes)) AS total_read
FROM system.query_log
WHERE type IN ('QueryFinish', 'ExceptionWhileProcessing')
  AND event_time >= now() - INTERVAL 1 HOUR
GROUP BY minute ORDER BY minute;

-- Insert throughput (last hour)
SELECT
    toStartOfMinute(event_time) AS minute,
    count() AS inserts,
    sum(written_rows) AS rows_written,
    formatReadableSize(sum(written_bytes)) AS bytes_written
FROM system.query_log
WHERE type = 'QueryFinish' AND query_kind = 'Insert'
  AND event_time >= now() - INTERVAL 1 HOUR
GROUP BY minute ORDER BY minute;

-- Part count per table (merge health indicator)
SELECT database, table, count() AS parts, sum(rows) AS rows,
       formatReadableSize(sum(bytes_on_disk)) AS size
FROM system.parts WHERE active
GROUP BY database, table
HAVING parts > 50
ORDER BY parts DESC;
```

### Step 2: Prometheus Integration

**ClickHouse Cloud** exposes a managed Prometheus endpoint:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: clickhouse-cloud
    metrics_path: /v1/organizations/<ORG_ID>/prometheus
    basic_auth:
      username: <API_KEY_ID>
      password: <API_KEY_SECRET>
    static_configs:
      - targets: ['api.clickhouse.cloud']
    params:
      filtered_metrics: ['true']   # 125 critical metrics only
```

**Self-hosted** — use clickhouse-exporter or built-in metrics endpoint:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: clickhouse
    static_configs:
      - targets: ['clickhouse-server:9363']  # Built-in Prometheus endpoint
    metrics_path: /metrics
```

```xml
<!-- Enable Prometheus endpoint in config.xml -->
<prometheus>
    <endpoint>/metrics</endpoint>
    <port>9363</port>
    <metrics>true</metrics>
    <events>true</events>
    <asynchronous_metrics>true</asynchronous_metrics>
</prometheus>
```

### Step 3: Application-Level Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const queryDuration = new Histogram({
  name: 'clickhouse_query_duration_seconds',
  help: 'ClickHouse query duration',
  labelNames: ['query_type', 'status'],
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

const queryErrors = new Counter({
  name: 'clickhouse_query_errors_total',
  help: 'ClickHouse query errors',
  labelNames: ['error_code'],
  registers: [registry],
});

const insertRows = new Counter({
  name: 'clickhouse_insert_rows_total',
  help: 'Total rows inserted into ClickHouse',
  labelNames: ['table'],
  registers: [registry],
});

// Instrumented query wrapper
async function instrumentedQuery<T>(
  queryType: string,
  fn: () => Promise<T>,
): Promise<T> {
  const timer = queryDuration.startTimer({ query_type: queryType });
  try {
    const result = await fn();
    timer({ status: 'success' });
    return result;
  } catch (err: any) {
    timer({ status: 'error' });
    queryErrors.inc({ error_code: err.code ?? 'unknown' });
    throw err;
  }
}

// Expose /metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

### Step 4: Grafana Dashboard Panels

```json
{
  "panels": [
    {
      "title": "Query Rate (QPS)",
      "type": "timeseries",
      "targets": [{ "expr": "rate(clickhouse_query_duration_seconds_count[5m])" }]
    },
    {
      "title": "Query Latency P50 / P95 / P99",
      "type": "timeseries",
      "targets": [
        { "expr": "histogram_quantile(0.5, rate(clickhouse_query_duration_seconds_bucket[5m]))" },
        { "expr": "histogram_quantile(0.95, rate(clickhouse_query_duration_seconds_bucket[5m]))" },
        { "expr": "histogram_quantile(0.99, rate(clickhouse_query_duration_seconds_bucket[5m]))" }
      ]
    },
    {
      "title": "Error Rate",
      "type": "stat",
      "targets": [{
        "expr": "rate(clickhouse_query_errors_total[5m]) / rate(clickhouse_query_duration_seconds_count[5m])"
      }]
    },
    {
      "title": "Insert Throughput (rows/sec)",
      "type": "timeseries",
      "targets": [{ "expr": "rate(clickhouse_insert_rows_total[5m])" }]
    }
  ]
}
```

Import the official ClickHouse Grafana dashboard: `https://grafana.com/grafana/dashboards/23415`

### Step 5: Alert Rules

```yaml
# clickhouse-alerts.yml
groups:
  - name: clickhouse
    rules:
      - alert: ClickHouseHighErrorRate
        expr: |
          rate(clickhouse_query_errors_total[5m]) /
          rate(clickhouse_query_duration_seconds_count[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "ClickHouse error rate > 5%"

      - alert: ClickHouseHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(clickhouse_query_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "ClickHouse P95 latency > 5 seconds"

      - alert: ClickHouseTooManyParts
        expr: clickhouse_table_parts > 300
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Table has > 300 active parts — merges falling behind"

      - alert: ClickHouseMemoryHigh
        expr: clickhouse_server_memory_usage / clickhouse_server_memory_limit > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "ClickHouse memory usage > 90%"

      - alert: ClickHouseDiskLow
        expr: clickhouse_disk_free_bytes / clickhouse_disk_total_bytes < 0.15
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "ClickHouse disk space < 15% free"
```

### Step 6: Structured Logging

```typescript
import pino from 'pino';

const logger = pino({ name: 'clickhouse' });

// Log query performance for analysis
function logQuery(queryType: string, durationMs: number, rowsRead: number) {
  logger.info({
    service: 'clickhouse',
    query_type: queryType,
    duration_ms: durationMs,
    rows_read: rowsRead,
    status: durationMs > 5000 ? 'slow' : 'ok',
  });
}
```

## Key System Tables for Monitoring

| Table | What to Monitor | Frequency |
|-------|-----------------|-----------|
| `system.processes` | Running queries, memory usage | Every 10s |
| `system.query_log` | Query performance history | Every 1m |
| `system.parts` | Part count, merge health | Every 1m |
| `system.merges` | Active merge progress | Every 30s |
| `system.metrics` | Server-wide gauges (connections, memory) | Every 10s |
| `system.events` | Cumulative counters | Every 1m |
| `system.replicas` | Replication lag | Every 30s |
| `system.disks` | Disk space | Every 5m |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Metrics endpoint empty | Prometheus not configured | Enable `/metrics` in config |
| High cardinality alerts | Too many label values | Reduce label cardinality |
| Missing query_log data | Logging disabled | Set `log_queries = 1` in config |
| Dashboard gaps | Scrape interval too long | Use 10-15s scrape interval |

## Resources

- [Prometheus Integration](https://clickhouse.com/docs/integrations/prometheus)
- [ClickHouse Grafana Dashboard](https://grafana.com/grafana/dashboards/23415)
- [System Tables Reference](https://clickhouse.com/docs/operations/system-tables)
- [Cloud Monitoring](https://clickhouse.com/blog/clickhouse-cloud-now-supports-prometheus-monitoring)

## Next Steps

For incident response, see `clickhouse-incident-runbook`.
