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
tags: [saas, databricks, monitoring, cost-optimization]

---
# Databricks Cost Tuning

## Overview
Reduce Databricks spending through cluster policies, spot instances, SQL warehouse right-sizing, and cost governance. Databricks charges per DBU (Databricks Unit) with rates varying by compute type: Jobs Compute (~$0.15/DBU), All-Purpose Compute (~$0.40/DBU), SQL Compute (~$0.22/DBU), Serverless (~$0.07/DBU). System tables (`system.billing.usage` and `system.billing.list_prices`) provide cost visibility.

## Prerequisites
- Databricks Premium or Enterprise workspace
- Access to `system.billing.usage` and `system.billing.list_prices` tables
- Workspace admin for cluster policy creation

## Instructions

### Step 1: Identify Top Cost Drivers
```sql
-- Top 10 most expensive resources this month
SELECT cluster_id,
       COALESCE(usage_metadata.cluster_name, 'unnamed') AS cluster_name,
       sku_name,
       SUM(usage_quantity) AS total_dbus,
       ROUND(SUM(usage_quantity * p.pricing.default), 2) AS estimated_cost_usd
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices p ON u.sku_name = p.sku_name
WHERE u.usage_date >= date_trunc('month', current_date())
GROUP BY cluster_id, cluster_name, u.sku_name
ORDER BY estimated_cost_usd DESC
LIMIT 10;

-- Cost by team (requires cluster tags)
SELECT usage_metadata.cluster_tags.Team AS team,
       sku_name,
       ROUND(SUM(usage_quantity), 1) AS total_dbus,
       ROUND(SUM(usage_quantity * p.pricing.default), 2) AS cost_usd
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices p ON u.sku_name = p.sku_name
WHERE u.usage_date >= date_trunc('month', current_date())
GROUP BY team, u.sku_name
ORDER BY cost_usd DESC;
```

### Step 2: Enforce Cluster Policies
Cluster policies restrict what users can configure, preventing runaway costs.

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create a cost-optimized policy for interactive clusters
policy = w.cluster_policies.create(
    name="cost-optimized-interactive",
    definition="""{
        "autotermination_minutes": {
            "type": "range", "minValue": 10, "maxValue": 60, "defaultValue": 20
        },
        "num_workers": {
            "type": "range", "minValue": 0, "maxValue": 8
        },
        "node_type_id": {
            "type": "allowlist",
            "values": ["m5.xlarge", "m5.2xlarge", "c5.xlarge", "c5.2xlarge"],
            "defaultValue": "m5.xlarge"
        },
        "aws_attributes.availability": {
            "type": "fixed", "value": "SPOT_WITH_FALLBACK"
        },
        "custom_tags.CostCenter": {
            "type": "fixed", "value": "engineering"
        }
    }""",
)

# Assign policy to a group
w.cluster_policies.set_permissions(
    cluster_policy_id=policy.policy_id,
    access_control_list=[{
        "group_name": "data-analysts",
        "all_permissions": [{"permission_level": "CAN_USE"}],
    }],
)
```

### Step 3: Spot Instances for Batch Jobs
Spot instances save 60-90% on worker nodes. Always keep the driver on-demand.

```python
# Job cluster config with spot instances
job_cluster_config = {
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "i3.xlarge",
    "num_workers": 4,
    "aws_attributes": {
        "availability": "SPOT_WITH_FALLBACK",
        "first_on_demand": 1,          # Driver is on-demand
        "spot_bid_price_percent": 100,  # Pay up to on-demand price
        "zone_id": "auto",             # Let Databricks pick cheapest AZ
    },
}
# Workers use spot, driver uses on-demand
# If spot instances unavailable, falls back to on-demand automatically
```

### Step 4: Right-Size SQL Warehouses
```sql
-- Check warehouse utilization
SELECT warehouse_id, warehouse_name,
       COUNT(*) AS query_count,
       ROUND(AVG(total_duration_ms) / 1000, 1) AS avg_duration_sec,
       ROUND(MAX(queue_duration_ms) / 1000, 1) AS max_queue_sec,
       ROUND(AVG(queue_duration_ms) / 1000, 1) AS avg_queue_sec
FROM system.query.history
WHERE start_time > current_timestamp() - INTERVAL 7 DAYS
GROUP BY warehouse_id, warehouse_name;

-- If avg_queue_sec is near 0 → warehouse is oversized, reduce cluster_size
-- If avg_queue_sec > 30 → warehouse needs more capacity or auto-scaling
```

```python
# Migrate to serverless for bursty workloads (cheaper per-second billing)
for wh in w.warehouses.list():
    print(f"{wh.name}: type={wh.warehouse_type}, size={wh.cluster_size}, "
          f"auto_stop={wh.auto_stop_mins}min, state={wh.state}")
    # Serverless (~$0.07/DBU) vs Classic (~$0.22/DBU) for bursty workloads
```

### Step 5: Auto-Terminate Idle Development Clusters
```bash
# Find and set aggressive auto-termination on dev clusters
databricks clusters list --output JSON | \
  jq -r '.[] | select(.cluster_name | test("dev|sandbox|test")) | .cluster_id' | \
  while read CID; do
    echo "Setting 15min auto-stop on cluster $CID"
    databricks clusters edit --cluster-id "$CID" --json '{"autotermination_minutes": 15}'
  done
```

```python
# Find idle running clusters wasting money
from datetime import datetime, timedelta

for c in w.clusters.list():
    if c.state.value == "RUNNING" and c.last_activity_time:
        idle_minutes = (datetime.now().timestamp() * 1000 - c.last_activity_time) / 60000
        if idle_minutes > 60:
            print(f"IDLE {idle_minutes:.0f}min: {c.cluster_name} "
                  f"({c.num_workers} x {c.node_type_id})")
```

### Step 6: Instance Pools for Faster + Cheaper Startup
```python
# Create a pool of pre-allocated instances
pool = w.instance_pools.create(
    instance_pool_name="etl-pool",
    node_type_id="i3.xlarge",
    min_idle_instances=2,     # Keep 2 warm for instant startup
    max_capacity=10,
    idle_instance_autotermination_minutes=15,
    aws_attributes={"availability": "SPOT_WITH_FALLBACK"},
)

# Reference in job cluster config
job_cluster = {
    "instance_pool_id": pool.instance_pool_id,
    "num_workers": 4,
    # No node_type_id needed — inherited from pool
}
```

## Output
- Cost breakdown by cluster, team, and SKU
- Cluster policies enforcing auto-termination and instance limits
- Spot instance config for 60-90% savings on batch workers
- SQL warehouse utilization report for right-sizing
- Instance pools for faster cluster startup
- Idle cluster detection script

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Spot interruption | Cloud provider reclaiming capacity | `SPOT_WITH_FALLBACK` auto-recovers; checkpoint long jobs |
| Policy too restrictive | Workers can't handle workload | Increase `max_workers` or add larger instance types |
| SQL warehouse idle but running | Auto-stop not configured | Set `auto_stop_mins` to 5-10 for serverless |
| Billing data not available | System tables not enabled | Enable in Account Console > System Tables |

## Examples

### Monthly Cost Report
```sql
SELECT date_trunc('week', usage_date) AS week,
       sku_name,
       ROUND(SUM(usage_quantity), 0) AS total_dbus
FROM system.billing.usage
WHERE usage_date >= current_date() - INTERVAL 30 DAYS
GROUP BY week, sku_name
ORDER BY week, total_dbus DESC;
```

### Cost Savings Checklist
- [ ] Auto-termination enabled on ALL interactive clusters (15-30 min)
- [ ] Spot instances enabled for all batch job workers
- [ ] Instance pools for frequently-used cluster configs
- [ ] Serverless SQL warehouses for bursty query workloads
- [ ] Cluster policies assigned to all non-admin groups
- [ ] Team tags on all clusters for cost attribution
- [ ] Weekly cost review using `system.billing.usage`

## Resources
- [Cost Optimization Best Practices](https://docs.databricks.com/aws/en/lakehouse-architecture/cost-optimization/best-practices)
- [Cluster Policies](https://docs.databricks.com/aws/en/admin/clusters/policy-definition)
- [Billing Usage Tables](https://docs.databricks.com/aws/en/admin/system-tables/)
- [Serverless SQL Warehouses](https://docs.databricks.com/aws/en/admin/sql/serverless)
