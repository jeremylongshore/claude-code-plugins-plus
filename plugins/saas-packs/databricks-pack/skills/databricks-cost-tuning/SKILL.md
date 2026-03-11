---
name: databricks-cost-tuning
description: |
  Optimize Databricks costs with cluster policies, spot instances, and monitoring.
  Use when reducing cloud spend, implementing cost controls,
  or analyzing Databricks usage costs.
  Trigger with phrases like "databricks cost", "reduce databricks spend",
  "databricks billing", "databricks cost optimization", "cluster cost".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Cost Tuning

## Overview
Reduce Databricks spending by optimizing cluster configurations, leveraging spot instances, right-sizing SQL warehouses, and implementing cost governance policies. Databricks charges per DBU (Databricks Unit) with rates varying by workload type: Jobs Compute (~$0.15/DBU), All-Purpose Compute (~$0.40/DBU), SQL Compute (~$0.22/DBU), and Serverless (~$0.07/DBU).

## Prerequisites
- Databricks Premium or Enterprise workspace
- Access to `system.billing.usage` tables
- Workspace admin for cluster policy creation

## Instructions

### Step 1: Identify Top Cost Drivers
```sql
-- Top 10 most expensive clusters this month
SELECT cluster_id, cluster_name, sku_name,
       SUM(usage_quantity) AS total_dbus,
       ROUND(SUM(usage_quantity * list_price), 2) AS cost_usd
FROM system.billing.usage
WHERE usage_date >= date_trunc('month', current_date())
GROUP BY cluster_id, cluster_name, sku_name
ORDER BY cost_usd DESC
LIMIT 10;
```

### Step 2: Enforce Cluster Policies
```json
{
  "name": "cost-optimized-interactive",
  "definition": {
    "autotermination_minutes": { "type": "range", "minValue": 10, "maxValue": 60, "defaultValue": 20 },
    "num_workers": { "type": "range", "minValue": 1, "maxValue": 8 },
    "node_type_id": { "type": "allowlist", "values": ["m5.xlarge", "m5.2xlarge"] },
    "aws_attributes.availability": { "type": "fixed", "value": "SPOT_WITH_FALLBACK" },
    "spark_conf.spark.databricks.cluster.profile": { "type": "fixed", "value": "singleNode" }
  }
}
```

### Step 3: Use Spot Instances for Jobs
```python
# jobs/cost_optimized_job.py
job_config = {
    "name": "nightly-etl",
    "new_cluster": {
        "num_workers": 4,
        "node_type_id": "m5.2xlarge",
        "aws_attributes": {
            "availability": "SPOT_WITH_FALLBACK",
            "first_on_demand": 1,  # Driver on-demand, workers spot
            "spot_bid_price_percent": 100,
        },
        "autotermination_minutes": 0,  # Jobs clusters auto-terminate on completion
    },
}
# Spot instances save 60-90% on worker node costs
```

### Step 4: Right-Size SQL Warehouses
```sql
-- Check warehouse utilization (queries/hour and queue time)
SELECT warehouse_id, warehouse_name,
       COUNT(*) AS query_count,
       AVG(total_duration_ms) AS avg_duration_ms,
       MAX(queue_duration_ms) AS max_queue_ms
FROM system.query.history
WHERE start_time > current_timestamp() - INTERVAL 7 DAYS
GROUP BY warehouse_id, warehouse_name;
-- If max_queue_ms is near 0, warehouse is oversized. Reduce cluster size.
-- If max_queue_ms > 30000, warehouse needs more capacity or auto-scaling.  # 30000: 30 seconds in ms
```

### Step 5: Schedule Auto-Stop for Development Clusters
```bash
# Set aggressive auto-termination for all dev clusters
databricks clusters list --output JSON | \
  jq -r '.[] | select(.cluster_name | test("dev|sandbox|test")) | .cluster_id' | \
  xargs -I{} databricks clusters edit {} --json '{"autotermination_minutes": 15}'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Spot instance interruption | Cloud provider reclaiming capacity | Use SPOT_WITH_FALLBACK, checkpoint long jobs |
| Cluster policy too restrictive | Workers can't handle workload | Increase max_workers or allow larger instance types |
| SQL warehouse idle but running | No auto-stop configured | Enable auto-stop with 10-minute timeout |
| Billing data not available | System tables not enabled | Enable system table access in account settings |

## Examples

**Basic usage**: Apply databricks cost tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize databricks cost tuning for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack