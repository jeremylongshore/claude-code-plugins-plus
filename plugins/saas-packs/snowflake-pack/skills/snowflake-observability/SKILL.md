---
name: snowflake-observability
description: |
  Set up Snowflake observability using ACCOUNT_USAGE views, alerts, and external monitoring.
  Use when implementing Snowflake monitoring dashboards, setting up query performance tracking,
  or configuring alerting for warehouse and pipeline health.
  Trigger with phrases like "snowflake monitoring", "snowflake metrics",
  "snowflake observability", "snowflake dashboard", "snowflake alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Observability

## Overview

Set up comprehensive observability for Snowflake using built-in ACCOUNT_USAGE views, Snowflake Alerts, and integration with external monitoring systems.

## Prerequisites

- Role with access to `SNOWFLAKE.ACCOUNT_USAGE` (ACCOUNTADMIN or granted)
- Notification integration configured for alerts
- Optional: Prometheus/Grafana or Datadog for external dashboards

## Instructions

### Step 1: Key Monitoring Queries

```sql
-- === QUERY PERFORMANCE ===
-- Average query time by warehouse (last 7 days)
SELECT warehouse_name,
       COUNT(*) AS query_count,
       ROUND(AVG(total_elapsed_time) / 1000, 1) AS avg_seconds,
       ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_elapsed_time) / 1000, 1) AS p95_seconds,
       ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_elapsed_time) / 1000, 1) AS p99_seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD(days, -7, CURRENT_TIMESTAMP())
  AND execution_status = 'SUCCESS'
  AND query_type = 'SELECT'
GROUP BY warehouse_name
ORDER BY avg_seconds DESC;

-- === ERROR RATE ===
-- Error rate by hour
SELECT DATE_TRUNC('hour', start_time) AS hour,
       COUNT_IF(execution_status = 'SUCCESS') AS success,
       COUNT_IF(execution_status = 'FAIL') AS failures,
       ROUND(COUNT_IF(execution_status = 'FAIL') * 100.0 /
             NULLIF(COUNT(*), 0), 2) AS error_rate_pct
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
GROUP BY hour
ORDER BY hour;

-- === CREDIT CONSUMPTION ===
-- Hourly credit usage
SELECT DATE_TRUNC('hour', start_time) AS hour,
       warehouse_name,
       SUM(credits_used) AS credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
GROUP BY hour, warehouse_name
ORDER BY hour DESC, credits DESC;

-- === STORAGE GROWTH ===
-- Daily storage trend
SELECT usage_date,
       ROUND(storage_bytes / 1e12, 3) AS storage_tb,
       ROUND(stage_bytes / 1e12, 3) AS stage_tb,
       ROUND(failsafe_bytes / 1e12, 3) AS failsafe_tb
FROM SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE
WHERE usage_date >= DATEADD(days, -30, CURRENT_DATE())
ORDER BY usage_date;
```

### Step 2: Built-in Snowflake Alerts

```sql
-- Alert: High error rate
CREATE OR REPLACE ALERT high_error_rate_alert
  WAREHOUSE = ANALYTICS_WH
  SCHEDULE = '15 MINUTE'
  IF (EXISTS (
    SELECT 1
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE start_time >= DATEADD(minutes, -15, CURRENT_TIMESTAMP())
    GROUP BY ALL
    HAVING COUNT_IF(execution_status = 'FAIL') * 100.0 / COUNT(*) > 5
  ))
  THEN
    CALL SYSTEM$SEND_EMAIL(
      'ops_notifications',
      'oncall@company.com',
      'Snowflake: Error rate > 5%',
      'Query error rate exceeded 5% in the last 15 minutes.'
    );

-- Alert: Warehouse stuck running (no auto-suspend)
CREATE OR REPLACE ALERT warehouse_running_alert
  WAREHOUSE = ANALYTICS_WH
  SCHEDULE = '60 MINUTE'
  IF (EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.WAREHOUSES
    WHERE state = 'STARTED'
      AND DATEDIFF('hour', COALESCE(resumed_on, created_on), CURRENT_TIMESTAMP()) > 4
  ))
  THEN
    CALL SYSTEM$SEND_EMAIL(
      'ops_notifications',
      'ops@company.com',
      'Snowflake: Warehouse running > 4 hours',
      'A warehouse has been running for over 4 hours. Check auto-suspend settings.'
    );

-- Alert: Task failures
CREATE OR REPLACE ALERT task_failure_alert
  WAREHOUSE = ANALYTICS_WH
  SCHEDULE = '10 MINUTE'
  IF (EXISTS (
    SELECT 1
    FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
      SCHEDULED_TIME_RANGE_START => DATEADD(minutes, -10, CURRENT_TIMESTAMP())
    ))
    WHERE state = 'FAILED'
  ))
  THEN
    CALL SYSTEM$SEND_EMAIL(
      'ops_notifications',
      'oncall@company.com',
      'Snowflake: Task Failure',
      'One or more Snowflake tasks failed. Check TASK_HISTORY for details.'
    );

-- Resume all alerts
ALTER ALERT high_error_rate_alert RESUME;
ALTER ALERT warehouse_running_alert RESUME;
ALTER ALERT task_failure_alert RESUME;
```

### Step 3: Export Metrics to External Systems

```typescript
// src/snowflake/metrics-exporter.ts
// Export Snowflake metrics to Prometheus/Datadog

interface SnowflakeMetrics {
  queryCount: number;
  errorRate: number;
  avgLatencyMs: number;
  p95LatencyMs: number;
  creditsUsed: number;
  activeWarehouses: number;
}

async function collectSnowflakeMetrics(
  conn: snowflake.Connection
): Promise<SnowflakeMetrics> {
  const [queryStats] = await query(conn, `
    SELECT
      COUNT(*) AS query_count,
      COUNT_IF(execution_status = 'FAIL') * 100.0 / NULLIF(COUNT(*), 0) AS error_rate,
      AVG(total_elapsed_time) AS avg_latency,
      PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_elapsed_time) AS p95_latency
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE start_time >= DATEADD(minutes, -5, CURRENT_TIMESTAMP())
  `).then(r => r.rows);

  const [creditStats] = await query(conn, `
    SELECT COALESCE(SUM(credits_used), 0) AS credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE start_time >= CURRENT_DATE()
  `).then(r => r.rows);

  const [whStats] = await query(conn, `
    SELECT COUNT_IF(state = 'STARTED') AS active
    FROM INFORMATION_SCHEMA.WAREHOUSES
  `).then(r => r.rows);

  return {
    queryCount: queryStats.QUERY_COUNT,
    errorRate: queryStats.ERROR_RATE,
    avgLatencyMs: queryStats.AVG_LATENCY,
    p95LatencyMs: queryStats.P95_LATENCY,
    creditsUsed: creditStats.CREDITS,
    activeWarehouses: whStats.ACTIVE,
  };
}

// Prometheus exposition format
function formatPrometheus(metrics: SnowflakeMetrics): string {
  return [
    `snowflake_queries_total ${metrics.queryCount}`,
    `snowflake_error_rate_percent ${metrics.errorRate}`,
    `snowflake_avg_latency_ms ${metrics.avgLatencyMs}`,
    `snowflake_p95_latency_ms ${metrics.p95LatencyMs}`,
    `snowflake_credits_used_today ${metrics.creditsUsed}`,
    `snowflake_active_warehouses ${metrics.activeWarehouses}`,
  ].join('\n');
}
```

### Step 4: Operational Dashboard Queries

```sql
-- Pipeline health dashboard
SELECT
  'Tasks' AS component,
  COUNT_IF(state = 'started') AS running,
  COUNT_IF(state = 'suspended') AS suspended,
  (SELECT COUNT_IF(state = 'FAILED')
   FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
     SCHEDULED_TIME_RANGE_START => DATEADD(hours, -24, CURRENT_TIMESTAMP())
   ))) AS failures_24h
FROM INFORMATION_SCHEMA.TASKS

UNION ALL

SELECT 'Pipes',
  COUNT_IF(is_autoingest_enabled = 'true'), 0,
  0  -- Check PIPE_USAGE_HISTORY for errors
FROM INFORMATION_SCHEMA.PIPES

UNION ALL

SELECT 'Streams',
  COUNT_IF(stale = FALSE),
  COUNT_IF(stale = TRUE), 0
FROM INFORMATION_SCHEMA.STREAMS;
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| ACCOUNT_USAGE latency | Views have up to 45min lag | Use INFORMATION_SCHEMA for real-time data |
| Alert not firing | Alert suspended | `ALTER ALERT x RESUME` |
| Metrics gaps | Warehouse suspended | Only active warehouses report metrics |
| Email not delivered | Notification integration misconfigured | Check `ALLOWED_RECIPIENTS` |

## Resources

- [Account Usage Views](https://docs.snowflake.com/en/sql-reference/account-usage)
- [QUERY_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
- [WAREHOUSE_METERING_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_metering_history)
- [Snowflake Alerts](https://docs.snowflake.com/en/user-guide/alerts)

## Next Steps

For incident response, see `snowflake-incident-runbook`.
