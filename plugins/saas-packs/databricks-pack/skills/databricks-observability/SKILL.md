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
tags: [saas, databricks, monitoring, observability, dashboard]

---
# Databricks Observability

## Overview
Monitor Databricks jobs, clusters, SQL warehouses, and costs using system tables in the `system` catalog. System tables provide queryable observability data: `system.lakeflow` (job runs), `system.billing` (costs), `system.query` (SQL history), `system.access` (audit logs), and `system.compute` (cluster metrics). Data updates throughout the day, not real-time.

## Prerequisites
- Databricks Premium or Enterprise with Unity Catalog enabled
- Access to `system.billing`, `system.lakeflow`, `system.query`, and `system.access` schemas
- SQL warehouse for running monitoring queries

## Instructions

### Step 1: Job Health Monitoring
```sql
-- Job success/failure over last 24 hours
SELECT
    COUNT(CASE WHEN result_state = 'SUCCESS' THEN 1 END) AS succeeded,
    COUNT(CASE WHEN result_state = 'FAILED' THEN 1 END) AS failed,
    COUNT(CASE WHEN result_state = 'TIMED_OUT' THEN 1 END) AS timed_out,
    ROUND(100.0 * COUNT(CASE WHEN result_state = 'SUCCESS' THEN 1 END) / COUNT(*), 1) AS success_rate_pct,
    ROUND(AVG(TIMESTAMPDIFF(MINUTE, start_time, end_time)), 1) AS avg_duration_min
FROM system.lakeflow.job_run_timeline
WHERE start_time > current_timestamp() - INTERVAL 24 HOURS;

-- Failed jobs with error details
SELECT job_id, run_name, result_state, start_time, end_time,
       TIMESTAMPDIFF(MINUTE, start_time, end_time) AS duration_min,
       error_message
FROM system.lakeflow.job_run_timeline
WHERE result_state = 'FAILED'
  AND start_time > current_timestamp() - INTERVAL 24 HOURS
ORDER BY start_time DESC;
```

### Step 2: Cluster Utilization and Costs
```sql
-- DBU consumption by cluster (last 7 days)
SELECT usage_metadata.cluster_id,
       COALESCE(usage_metadata.cluster_name, 'unnamed') AS cluster_name,
       sku_name,
       SUM(usage_quantity) AS total_dbus,
       ROUND(SUM(usage_quantity * p.pricing.default), 2) AS cost_usd
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices p ON u.sku_name = p.sku_name
WHERE u.usage_date >= current_date() - INTERVAL 7 DAYS
GROUP BY usage_metadata.cluster_id, cluster_name, u.sku_name
ORDER BY cost_usd DESC
LIMIT 20;
```

### Step 3: SQL Warehouse Performance
```sql
-- Slow queries (>30s) on SQL warehouses
SELECT warehouse_id, statement_id, executed_by,
       ROUND(total_duration_ms / 1000, 1) AS duration_sec,
       rows_produced,
       ROUND(bytes_scanned / 1048576, 1) AS scanned_mb,
       LEFT(statement_text, 200) AS query_preview
FROM system.query.history
WHERE total_duration_ms > 30000
  AND start_time > current_timestamp() - INTERVAL 24 HOURS
ORDER BY total_duration_ms DESC
LIMIT 50;

-- Warehouse queue times (right-sizing indicator)
SELECT warehouse_id, warehouse_name,
       COUNT(*) AS query_count,
       ROUND(AVG(total_duration_ms) / 1000, 1) AS avg_sec,
       ROUND(MAX(queue_duration_ms) / 1000, 1) AS max_queue_sec
FROM system.query.history
WHERE start_time > current_timestamp() - INTERVAL 7 DAYS
GROUP BY warehouse_id, warehouse_name;
```

### Step 4: Cost-per-Job Analysis
```sql
SELECT j.name AS job_name,
       COUNT(DISTINCT r.run_id) AS run_count,
       ROUND(AVG(TIMESTAMPDIFF(MINUTE, r.start_time, r.end_time)), 1) AS avg_min,
       ROUND(SUM(b.usage_quantity), 1) AS total_dbus,
       ROUND(SUM(b.usage_quantity * p.pricing.default), 2) AS total_cost_usd
FROM system.lakeflow.job_run_timeline r
JOIN system.lakeflow.jobs j ON r.job_id = j.job_id
LEFT JOIN system.billing.usage b
    ON r.run_id = b.usage_metadata.job_run_id
LEFT JOIN system.billing.list_prices p ON b.sku_name = p.sku_name
WHERE r.start_time > current_timestamp() - INTERVAL 7 DAYS
GROUP BY j.name
ORDER BY total_cost_usd DESC
LIMIT 15;
```

### Step 5: SQL Alerts for Automated Notifications
```sql
-- Create as SQL Alert: trigger when failure_count > 3
-- Schedule: every 15 minutes
-- Notification destination: Slack/email

SELECT COUNT(*) AS failure_count
FROM system.lakeflow.job_run_timeline
WHERE result_state = 'FAILED'
  AND start_time > current_timestamp() - INTERVAL 1 HOUR;
```

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create SQL alert programmatically
alert = w.alerts.create(
    name="Hourly Job Failure Alert",
    query_id="<saved-query-id>",
    options={"column": "failure_count", "op": ">", "value": "3"},
    rearm=900,  # re-alert after 15 min if still triggered
)
```

### Step 6: Export Metrics to External Systems
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Export cluster state metrics for Prometheus/Datadog
for cluster in w.clusters.list():
    if cluster.state.value == "RUNNING":
        print(f"databricks_cluster_workers{{name=\"{cluster.cluster_name}\"}} "
              f"{cluster.num_workers}")
        print(f"databricks_cluster_running{{name=\"{cluster.cluster_name}\"}} 1")

# Export job success rate for Grafana
runs = list(w.jobs.list_runs(limit=100, completed_only=True))
success = sum(1 for r in runs if r.state.result_state and r.state.result_state.value == "SUCCESS")
print(f"databricks_job_success_rate {success / len(runs):.2f}")
```

### Step 7: Audit Log Monitoring
```sql
-- Security: who accessed what in the last 7 days
SELECT event_time, user_identity.email, action_name,
       request_params, response.status_code
FROM system.access.audit
WHERE service_name IN ('unityCatalog', 'jobs', 'clusters')
  AND event_date >= current_date() - 7
  AND action_name NOT IN ('getStatus', 'list')  -- exclude noisy reads
ORDER BY event_time DESC
LIMIT 100;
```

## Output
- Job health dashboard (success rate, duration, failures)
- Cluster cost breakdown by team and SKU
- SQL warehouse performance report (slow queries, queue times)
- Per-job cost analysis
- Automated SQL alerts with Slack/email notifications
- External metric export for Prometheus/Grafana

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| System tables empty | Unity Catalog not enabled | Enable in Account Console > Settings |
| `TABLE_OR_VIEW_NOT_FOUND` | Schema not accessible | Request admin to grant `SELECT ON system.billing` |
| Billing data delayed | System table refresh lag (up to 24h) | Use for trends and alerts, not real-time |
| Query history missing | Serverless queries not tracked | Use classic SQL warehouse or check retention |

## Examples

### Daily Standup Dashboard
```sql
-- Single query for daily pipeline health
SELECT
    'Last 24h' AS period,
    COUNT(*) AS total_runs,
    COUNT(CASE WHEN result_state = 'SUCCESS' THEN 1 END) AS ok,
    COUNT(CASE WHEN result_state = 'FAILED' THEN 1 END) AS failed,
    ROUND(AVG(TIMESTAMPDIFF(MINUTE, start_time, end_time)), 1) AS avg_min
FROM system.lakeflow.job_run_timeline
WHERE start_time > current_timestamp() - INTERVAL 24 HOURS;
```

## Resources
- [System Tables](https://docs.databricks.com/aws/en/admin/system-tables/)
- [Audit Logs](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)
- [Observability Best Practices](https://docs.databricks.com/aws/en/data-engineering/observability-best-practices)
- [SQL Alerts](https://docs.databricks.com/aws/en/sql/user/alerts/)
