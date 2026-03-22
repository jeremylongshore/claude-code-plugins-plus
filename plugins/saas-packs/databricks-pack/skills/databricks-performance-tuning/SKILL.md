---
name: databricks-performance-tuning
description: |
  Optimize Databricks cluster and query performance.
  Use when jobs are running slowly, optimizing Spark configurations,
  or improving Delta Lake query performance.
  Trigger with phrases like "databricks performance", "spark tuning",
  "databricks slow", "optimize databricks", "cluster performance".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, performance]

---
# Databricks Performance Tuning

## Overview
Optimize Databricks cluster sizing, Spark configuration, and Delta Lake query performance. Covers workload-specific Spark configs, Adaptive Query Execution (AQE), Liquid Clustering, Z-ordering, OPTIMIZE/VACUUM maintenance, query plan analysis, and caching strategies.

## Prerequisites
- Access to cluster configuration (admin or cluster owner)
- Understanding of workload type (ETL batch, ML training, streaming, interactive)
- Query history access for identifying slow queries

## Instructions

### Step 1: Cluster Sizing by Workload

| Workload | Instance Family | Why | Workers |
|----------|----------------|-----|---------|
| ETL Batch | Compute-optimized (c5/c6) | CPU-heavy transforms | 2-8, autoscale |
| ML Training | Memory-optimized (r5/r6) | Large model fits | 4-16, fixed |
| Streaming | Compute-optimized (c5) | Sustained throughput | 2-4, fixed |
| Interactive / Ad-hoc | General-purpose (m5) | Balanced | Single node or 1-4 |
| Heavy shuffle / spill | Storage-optimized (i3) | Fast local NVMe | 4-8 |

```python
def recommend_cluster(data_size_gb: float, workload: str) -> dict:
    """Recommend cluster config based on data size and workload type."""
    configs = {
        "etl_batch": {"node": "c5.2xlarge", "memory_gb": 16, "multiplier": 1.5},
        "ml_training": {"node": "r5.2xlarge", "memory_gb": 64, "multiplier": 2.0},
        "streaming": {"node": "c5.xlarge", "memory_gb": 8, "multiplier": 1.0},
        "interactive": {"node": "m5.xlarge", "memory_gb": 16, "multiplier": 1.0},
    }
    cfg = configs.get(workload, configs["etl_batch"])
    workers = max(1, int(data_size_gb / cfg["memory_gb"] * cfg["multiplier"]))

    return {
        "node_type_id": cfg["node"],
        "num_workers": workers,
        "autoscale": {"min_workers": max(1, workers // 2), "max_workers": workers * 2},
    }
```

### Step 2: Spark Configuration by Workload
```python
spark_configs = {
    "etl_batch": {
        "spark.sql.shuffle.partitions": "auto",  # AQE handles this in DBR 14+
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.sql.adaptive.skewJoin.enabled": "true",
        "spark.databricks.delta.optimizeWrite.enabled": "true",
        "spark.databricks.delta.autoCompact.enabled": "true",
        "spark.sql.files.maxPartitionBytes": "134217728",  # 128MB
    },
    "ml_training": {
        "spark.driver.memory": "16g",
        "spark.executor.memory": "16g",
        "spark.memory.fraction": "0.8",
        "spark.memory.storageFraction": "0.3",
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
        "spark.kryoserializer.buffer.max": "1024m",
    },
    "streaming": {
        "spark.sql.streaming.schemaInference": "true",
        "spark.databricks.delta.autoCompact.minNumFiles": "10",
        "spark.sql.shuffle.partitions": "auto",
    },
    "interactive": {
        "spark.sql.inMemoryColumnarStorage.compressed": "true",
        "spark.databricks.cluster.profile": "singleNode",
        "spark.master": "local[*]",
    },
}
```

### Step 3: Delta Lake Optimization

#### OPTIMIZE with Z-Ordering
```sql
-- Compact small files and co-locate data by frequently filtered columns
OPTIMIZE prod_catalog.silver.orders ZORDER BY (order_date, customer_id);

-- Check file stats before and after
DESCRIBE DETAIL prod_catalog.silver.orders;
-- Look at: numFiles (should decrease), sizeInBytes
```

#### Liquid Clustering (DBR 13.3+ — Replaces Partitioning + Z-Order)
```sql
-- Enable Liquid Clustering — Databricks auto-optimizes data layout
ALTER TABLE prod_catalog.silver.orders CLUSTER BY (order_date, region);

-- Trigger incremental clustering
OPTIMIZE prod_catalog.silver.orders;

-- Advantages over Z-order:
-- * Incremental (only re-clusters new data)
-- * No need to choose between partitioning and Z-ordering
-- * Works with Deletion Vectors for faster DELETE/UPDATE
```

#### Predictive Optimization
```sql
-- Let Databricks auto-schedule OPTIMIZE and VACUUM
ALTER TABLE prod_catalog.silver.orders
SET TBLPROPERTIES ('delta.enableDeletionVectors' = 'true');

-- Enable at schema level for all tables
ALTER SCHEMA prod_catalog.silver
SET DBPROPERTIES ('delta.enablePredictiveOptimization' = 'true');
```

#### Compute Statistics
```sql
ANALYZE TABLE prod_catalog.silver.orders COMPUTE STATISTICS;
ANALYZE TABLE prod_catalog.silver.orders COMPUTE STATISTICS FOR COLUMNS order_date, amount, region;
```

### Step 4: Query Performance Analysis
```sql
-- Find slow queries (SQL warehouse query history)
SELECT statement_id, executed_by,
       total_duration_ms / 1000 AS duration_sec,
       rows_produced, bytes_scanned / 1024 / 1024 AS scanned_mb,
       statement_text
FROM system.query.history
WHERE total_duration_ms > 30000  -- > 30 seconds
  AND start_time > current_timestamp() - INTERVAL 24 HOURS
ORDER BY total_duration_ms DESC
LIMIT 20;
```

```python
# Analyze a query plan for bottlenecks
df = spark.table("prod_catalog.silver.orders").filter("region = 'US'")
df.explain(mode="formatted")
# Look for: BroadcastHashJoin (good), SortMergeJoin (may be slow on skewed data)
# Look for: ColumnarToRow conversion (indicates non-Photon path)
```

### Step 5: Join Optimization
```python
from pyspark.sql.functions import broadcast

# Rule of thumb: broadcast tables < 100MB
# BAD: Sort-merge join on small lookup table
result = orders.join(products, "product_id")  # triggers expensive shuffle

# GOOD: Broadcast the small table
result = orders.join(broadcast(products), "product_id")  # no shuffle

# For skewed keys: use AQE skew join handling
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256m")
```

### Step 6: Caching Strategy
```python
# Cache a frequently-accessed table
spark.table("prod_catalog.gold.daily_metrics").cache()

# Or use Delta Cache (automatic for i3/r5 instances with local SSD)
# Enable in cluster config:
# spark.databricks.io.cache.enabled = true
# spark.databricks.io.cache.maxDiskUsage = 50g

# NEVER cache Bronze tables — they're too large and change frequently
# ALWAYS cache small lookup/dimension tables used in multiple queries
```

### Step 7: VACUUM and Table Maintenance Schedule
```sql
-- Clean up old file versions (default retention: 7 days)
VACUUM prod_catalog.silver.orders RETAIN 168 HOURS;

-- Schedule via Databricks job or DLT maintenance task
-- Recommended: weekly OPTIMIZE, daily VACUUM for active tables
```

## Output
- Cluster sized appropriately for workload type
- Spark configs tuned per workload (ETL, ML, streaming, interactive)
- Delta tables optimized with Z-ordering or Liquid Clustering
- Slow queries identified via query history analysis
- Join and caching strategies applied

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| OOM during shuffle | Skewed partition | Enable AQE skew join or salt the join key |
| Slow joins | Large shuffle | `broadcast()` tables < 100MB |
| Too many small files | Frequent small writes | Run `OPTIMIZE` or enable `autoCompact` |
| VACUUM below retention | Retention < 7 days | Minimum is `168 HOURS`; set `delta.deletedFileRetentionDuration` |
| Query plan shows `ColumnarToRow` | Non-Photon code path | Use Photon-enabled runtime (suffix `-photon-scala2.12`) |

## Examples

### Quick Table Tune-Up
```sql
OPTIMIZE prod_catalog.silver.orders ZORDER BY (order_date, customer_id);
ANALYZE TABLE prod_catalog.silver.orders COMPUTE STATISTICS;
VACUUM prod_catalog.silver.orders RETAIN 168 HOURS;
```

### Before/After Comparison
```python
import time
table = "prod_catalog.silver.orders"
query = f"SELECT region, SUM(amount) FROM {table} WHERE order_date > '2024-01-01' GROUP BY region"

# Before optimization
start = time.time()
spark.sql(query).collect()
before = time.time() - start

spark.sql(f"OPTIMIZE {table} ZORDER BY (order_date, region)")

# After optimization
start = time.time()
spark.sql(query).collect()
after = time.time() - start

print(f"Before: {before:.1f}s, After: {after:.1f}s, Speedup: {before/after:.1f}x")
```

## Resources
- [Performance Guide](https://docs.databricks.com/aws/en/delta/best-practices)
- [Liquid Clustering](https://docs.databricks.com/aws/en/delta/clustering)
- [OPTIMIZE](https://docs.databricks.com/aws/en/sql/language-manual/delta-optimize)
- [AQE](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-adaptive)

## Next Steps
For cost optimization, see `databricks-cost-tuning`.
