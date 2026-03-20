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
---
# Databricks Performance Tuning

## Overview
Optimize Databricks cluster, Spark, and Delta Lake performance.

## Prerequisites
- Access to cluster configuration
- Understanding of workload characteristics
- Query history access

## Instructions

### Step 1: Cluster Sizing

```python
# Cluster sizing calculator
def recommend_cluster_size(
    data_size_gb: float,
    complexity: str = "medium",  # low, medium, high
    parallelism_need: str = "standard",  # standard, high
) -> dict:
    """
    Recommend cluster configuration based on workload.

    Args:
        data_size_gb: Estimated data size to process
        complexity: Query/transform complexity
        parallelism_need: Required parallelism level

    Returns:
        Recommended cluster configuration
    """
    # Memory per executor (standard DS3_v2 = 14GB)
    memory_per_worker = 14

    # Base calculation
    workers_by_data = max(1, int(data_size_gb / memory_per_worker / 2))

    # Adjust for complexity
    complexity_multiplier = {"low": 1, "medium": 1.5, "high": 2.5}
    workers = int(workers_by_data * complexity_multiplier.get(complexity, 1.5))

    # Adjust for parallelism
    if parallelism_need == "high":
        workers = max(workers, 8)

    return {
        "node_type_id": "Standard_DS3_v2",
        "num_workers": workers,
        "autoscale": {
            "min_workers": max(1, workers // 2),
            "max_workers": workers * 2,
        },
        "spark_conf": {
            "spark.sql.shuffle.partitions": str(workers * 4),
            "spark.default.parallelism": str(workers * 4),
        }
    }
```

### Step 2: Spark Configuration Optimization

```python
# Optimized Spark configurations by workload type
spark_configs = {
    "etl_batch": {
        # Memory and parallelism
        "spark.sql.shuffle.partitions": "200",  # HTTP 200 OK
        "spark.default.parallelism": "200",  # HTTP 200 OK
        "spark.sql.files.maxPartitionBytes": "134217728",  # 134217728: 128MB

        # Delta Lake optimizations
        "spark.databricks.delta.optimizeWrite.enabled": "true",
        "spark.databricks.delta.autoCompact.enabled": "true",
        "spark.databricks.delta.properties.defaults.autoOptimize.optimizeWrite": "true",

        # Adaptive query execution
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.sql.adaptive.skewJoin.enabled": "true",
    },

    "ml_training": {
        # Memory for ML workloads
        "spark.driver.memory": "16g",
        "spark.executor.memory": "16g",
        "spark.memory.fraction": "0.8",
        "spark.memory.storageFraction": "0.3",

        # Serialization for ML
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
        "spark.kryoserializer.buffer.max": "1024m",
    },

    "streaming": {
        # Streaming configurations
        "spark.sql.streaming.schemaInference": "true",
        "spark.sql.streaming.checkpointLocation": "/mnt/checkpoints",
        "spark.databricks.delta.autoCompact.minNumFiles": "10",

        # Micro-batch tuning
        "spark.sql.streaming.forEachBatch.enabled": "true",
    },

    "interactive": {
        # Fast startup
        "spark.databricks.cluster.profile": "singleNode",
        "spark.master": "local[*]",

        # Caching
        "spark.sql.inMemoryColumnarStorage.compressed": "true",
        "spark.sql.inMemoryColumnarStorage.batchSize": "10000",  # 10000: 10 seconds in ms
    }
}
```

### Step 3: Delta Lake Optimization

```python
# delta_optimization.py
from pyspark.sql import SparkSession

def optimize_delta_table(
    spark: SparkSession,
    table_name: str,
    z_order_columns: list[str] = None,
    vacuum_hours: int = 168,  # 7 days
) -> dict:
    """
    Optimize Delta table for query performance.

    Args:
        spark: SparkSession
        table_name: Fully qualified table name
        z_order_columns: Columns for Z-ordering (max 4)
        vacuum_hours: Retention period for vacuum

    Returns:
        Optimization results
    """
    results = {}

    # 1. Run OPTIMIZE with Z-ordering
    if z_order_columns:
        z_order_clause = ", ".join(z_order_columns[:4])  # Max 4 columns
        spark.sql(f"OPTIMIZE {table_name} ZORDER BY ({z_order_clause})")
        results["z_order"] = z_order_columns
    else:
        spark.sql(f"OPTIMIZE {table_name}")

    results["optimized"] = True

    # 2. Analyze table statistics
    spark.sql(f"ANALYZE TABLE {table_name} COMPUTE STATISTICS")
    results["statistics_computed"] = True

    # 3. Vacuum old files
    spark.sql(f"VACUUM {table_name} RETAIN {vacuum_hours} HOURS")
    results["vacuumed"] = True

    # 4. Get table metrics
    detail = spark.sql(f"DESCRIBE DETAIL {table_name}").first()
    results["metrics"] = {
        "num_files": detail.numFiles,
        "size_bytes": detail.sizeInBytes,
        "partitions": detail.partitionColumns,
    }

    return results

def enable_liquid_clustering(
    spark: SparkSession,
    table_name: str,
    cluster_columns: list[str],
) -> None:
    """
    Enable Liquid Clustering for automatic data layout optimization.

    Liquid Clustering replaces traditional partitioning and Z-ordering
    with automatic, incremental clustering.
    """
    columns = ", ".join(cluster_columns)
    spark.sql(f"""
        ALTER TABLE {table_name}
        CLUSTER BY ({columns})
    """)

def enable_predictive_optimization(
    spark: SparkSession,
    table_name: str,
) -> None:
    """Enable Databricks Predictive Optimization."""
    spark.sql(f"""
        ALTER TABLE {table_name}
        SET TBLPROPERTIES (
            'delta.enableDeletionVectors' = 'true',
            'delta.targetFileSize' = '104857600'  # 104857600 = configured value
        )
    """)
```

For query analysis, caching, join optimization, and benchmarking patterns, see [Advanced Patterns](references/advanced-patterns.md).

## Output
- Optimized cluster configuration with right-sized workers and autoscaling
- Spark configs tuned per workload type (ETL, ML, streaming, interactive)
- Delta tables optimized with Z-ordering or Liquid Clustering
- Query performance analysis queries for identifying slow operations

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| OOM errors | Insufficient memory | Increase executor memory or reduce partition size |
| Skewed data | Uneven distribution | Use salting or AQE skew handling |
| Slow joins | Large shuffle | Use broadcast for small tables (<100MB) |
| Too many files | Small files problem | Run `OPTIMIZE` regularly or enable autoCompact |

## Examples

### Quick Delta Table Tune-Up
```python
# One-command optimization for a table
spark.sql("OPTIMIZE prod.silver.orders ZORDER BY (order_date, customer_id)")
spark.sql("ANALYZE TABLE prod.silver.orders COMPUTE STATISTICS")
spark.sql("VACUUM prod.silver.orders RETAIN 168 HOURS")
```

## Resources
- [Databricks Performance Guide](https://docs.databricks.com/optimizations/index.html)
- [Delta Lake Optimization](https://docs.databricks.com/delta/optimizations/index.html)
- [Spark Tuning Guide](https://spark.apache.org/docs/latest/tuning.html)

## Next Steps
For cost optimization, see `databricks-cost-tuning`.