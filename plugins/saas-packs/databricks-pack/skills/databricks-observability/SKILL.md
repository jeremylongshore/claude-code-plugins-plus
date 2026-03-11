---
name: databricks-observability
description: |
  Set up comprehensive observability for Databricks with metrics, traces, and alerts.
  Use when implementing monitoring for Databricks jobs, setting up dashboards,
  or configuring alerting for pipeline health.
  Trigger with phrases like "databricks monitoring", "databricks metrics",
  "databricks observability", "monitor databricks", "databricks alerts", "databricks logging".
allowed-tools: Read, Write, Edit, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Databricks Observability

## Overview
Monitor Databricks job runs, cluster utilization, query performance, and costs using system tables and the Databricks SDK. Databricks exposes observability data through system tables in the `system` catalog (audit logs, billing, compute, query history) and real-time Ganglia metrics on clusters. Key signals include job failure rates, cluster auto-scaling efficiency (idle time vs compute time), SQL warehouse queue depth, and DBU consumption by workspace/cluster.

## Prerequisites
- Databricks Premium or Enterprise with Unity Catalog enabled
- Access to `system.billing`, `system.compute`, and `system.access` catalogs
- SQL warehouse or cluster for running monitoring queries

## Instructions

### Step 1: Monitor Job Health via System Tables
```sql
-- Failed jobs in the last 24 hours with error details
SELECT job_id, run_name, result_state, start_time, end_time,
       TIMESTAMPDIFF(MINUTE, start_time, end_time) AS duration_min,
       error_message
FROM system.lakeflow.job_run_timeline
WHERE result_state = 'FAILED'
  AND start_time > current_timestamp() - INTERVAL 24 HOURS
ORDER BY start_time DESC;
```

### Step 2: Track Cluster Utilization and Costs
```sql
-- DBU consumption by cluster over the last 7 days
SELECT cluster_id, cluster_name, sku_name,
       SUM(usage_quantity) AS total_dbus,
       SUM(usage_quantity * list_price) AS estimated_cost_usd
FROM system.billing.usage
WHERE usage_date >= current_date() - INTERVAL 7 DAYS
GROUP BY cluster_id, cluster_name, sku_name
ORDER BY estimated_cost_usd DESC
LIMIT 20;
```

### Step 3: Monitor SQL Warehouse Performance
```sql
-- Slow queries (>30s) on SQL warehouses
SELECT warehouse_id, statement_id, executed_by,
       total_duration_ms / 1000 AS duration_sec,
       rows_produced, bytes_scanned_mb
FROM system.query.history
WHERE total_duration_ms > 30000
  AND start_time > current_timestamp() - INTERVAL 24 HOURS
ORDER BY total_duration_ms DESC
LIMIT 50;
```

### Step 4: Set Up Alerts with Databricks SQL Alerts
```sql
-- Create alert: notify if any job fails more than 3 times in an hour
-- In Databricks SQL > Alerts > New Alert:
-- Query:
SELECT COUNT(*) AS failure_count
FROM system.lakeflow.job_run_timeline
WHERE result_state = 'FAILED'
  AND start_time > current_timestamp() - INTERVAL 1 HOUR;
-- Trigger when: failure_count > 3
-- Notification: Slack webhook or email
```

### Step 5: Export Metrics to External Systems
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Export cluster metrics to Prometheus via pushgateway
for cluster in w.clusters.list():
    if cluster.state == 'RUNNING':
        events = w.clusters.events(cluster.cluster_id, limit=10)
        # Push utilization metrics to your monitoring stack
        push_metric('databricks_cluster_state', 1, labels={'cluster': cluster.cluster_name, 'state': cluster.state.value})
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| System tables empty | Unity Catalog not enabled | Enable Unity Catalog for the workspace |
| Query history missing | Serverless warehouse not tracked | Use classic SQL warehouse or check retention |
| Billing data delayed | System table lag (up to 24h) | Use for trend analysis, not real-time alerting |
| Cluster metrics gaps | Cluster was terminated | Check terminated cluster events in audit log |

## Examples
```sql
-- Quick health dashboard: top 5 most expensive jobs this week
SELECT job_id, run_name, SUM(usage_quantity) AS dbus,
       SUM(usage_quantity * list_price) AS cost_usd
FROM system.billing.usage u
JOIN system.lakeflow.job_run_timeline j ON u.usage_metadata.job_id = j.job_id
WHERE usage_date >= current_date() - INTERVAL 7 DAYS
GROUP BY job_id, run_name
ORDER BY cost_usd DESC LIMIT 5;
```
