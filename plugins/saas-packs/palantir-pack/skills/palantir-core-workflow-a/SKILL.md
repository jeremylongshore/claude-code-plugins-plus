---
name: palantir-core-workflow-a
description: |
  Build Palantir Foundry data pipelines using Python transforms.
  Use when creating ETL pipelines, writing @transform decorators,
  or building dataset-to-dataset processing in Foundry.
  Trigger with phrases like "palantir pipeline", "foundry transform",
  "palantir ETL", "palantir data pipeline", "foundry python transform".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, transforms, pipelines, spark]
compatible-with: claude-code, codex, openclaw
---

# Palantir Core Workflow A — Data Pipelines with Transforms

## Overview
Build Foundry data pipelines using the `transforms-python` library. Covers the `@transform` and `@transform_df` decorators, input/output dataset wiring, incremental transforms, and `@configure` for Spark tuning. This is the primary workflow for all data processing in Foundry.

## Prerequisites
- Completed `palantir-install-auth` setup
- A Foundry Code Repository (Python Transforms type)
- Understanding of PySpark DataFrames (Foundry runs Spark under the hood)

## Instructions

### Step 1: Project Structure
```
my-transforms-repo/
├── src/
│   └── myproject/
│       ├── __init__.py
│       ├── pipeline.py          # Main transforms
│       ├── utils.py             # Shared logic
│       └── datasets.py          # Dataset path constants
├── build.gradle                 # Foundry build config
├── conda_recipe/meta.yaml       # Dependency declarations
└── settings.gradle
```

### Step 2: Basic Transform with @transform_df
```python
# src/myproject/pipeline.py
from transforms.api import transform_df, Input, Output

@transform_df(
    Output("/Company/datasets/cleaned_orders"),
    orders=Input("/Company/datasets/raw_orders"),
)
def clean_orders(orders):
    """Clean raw orders: drop nulls, normalize dates, filter test data."""
    from pyspark.sql import functions as F

    return (
        orders
        .filter(F.col("order_id").isNotNull())
        .filter(~F.col("email").like("%@test.com"))
        .withColumn("order_date", F.to_date("order_date_str", "yyyy-MM-dd"))
        .withColumn("total_cents", (F.col("total") * 100).cast("long"))
        .drop("order_date_str", "total")
    )
```

### Step 3: Multi-Input Join Transform
```python
@transform_df(
    Output("/Company/datasets/order_enriched"),
    orders=Input("/Company/datasets/cleaned_orders"),
    customers=Input("/Company/datasets/customers"),
)
def enrich_orders(orders, customers):
    """Join orders with customer data for analytics."""
    from pyspark.sql import functions as F

    return (
        orders
        .join(customers, orders.customer_id == customers.id, "left")
        .select(
            orders.order_id,
            orders.order_date,
            orders.total_cents,
            customers.name.alias("customer_name"),
            customers.segment,
            customers.region,
        )
        .withColumn("processed_at", F.current_timestamp())
    )
```

### Step 4: Low-Level @transform for File I/O
```python
from transforms.api import transform, Input, Output

@transform(
    output=Output("/Company/datasets/report_summary"),
    orders=Input("/Company/datasets/order_enriched"),
)
def generate_summary(orders, output):
    """Write aggregated summary using low-level FileSystem API."""
    df = orders.dataframe()

    summary = (
        df.groupBy("region", "segment")
        .agg(
            {"total_cents": "sum", "order_id": "count"}
        )
        .withColumnRenamed("sum(total_cents)", "revenue_cents")
        .withColumnRenamed("count(order_id)", "order_count")
    )

    output.write_dataframe(summary)
```

### Step 5: Incremental Transforms
```python
from transforms.api import transform_df, Input, Output, incremental

@incremental()
@transform_df(
    Output("/Company/datasets/daily_events"),
    events=Input("/Company/datasets/raw_events"),
)
def process_events_incrementally(events):
    """Only process new rows since last build — much faster for append-only data."""
    from pyspark.sql import functions as F

    return events.withColumn("ingested_at", F.current_timestamp())
```

### Step 6: Configure Spark Resources
```python
from transforms.api import transform_df, Input, Output, configure

@configure(profile=["DRIVER_MEMORY_LARGE"])  # 16GB driver
@transform_df(
    Output("/Company/datasets/heavy_aggregation"),
    data=Input("/Company/datasets/large_dataset"),
)
def heavy_compute(data):
    """Resource-intensive transform needing extra Spark memory."""
    from pyspark.sql import functions as F

    return (
        data
        .groupBy("category")
        .agg(F.approx_count_distinct("user_id").alias("unique_users"))
    )
```

## Output
- Dataset-to-dataset transforms wired with `@transform_df`
- Multi-input joins connecting datasets across projects
- Incremental processing for append-only sources
- Spark resource tuning with `@configure`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `DatasetNotFound` | Wrong path string | Check dataset path in Foundry UI (right-click > Copy path) |
| `AnalysisException: cannot resolve` | Column name mismatch | Print `df.columns` to debug; Foundry columns are case-sensitive |
| `OutOfMemoryError` | Insufficient Spark memory | Add `@configure(profile=["DRIVER_MEMORY_LARGE"])` |
| `Transform is not incremental-compatible` | Using non-append operations | Only use `filter/select/withColumn` in incremental transforms |
| Build hangs | Circular dependency | Check that no two transforms reference each other's output |

## Examples

### Polars Transform (Lightweight)
```python
from transforms.api import transform_polars, Input, Output

@transform_polars(
    Output("/Company/datasets/fast_summary"),
    data=Input("/Company/datasets/small_table"),
)
def fast_polars(data):
    """Use Polars for small datasets — faster than Spark, no JVM overhead."""
    import polars as pl
    return data.group_by("category").agg(pl.col("amount").sum())
```

## Resources
- [Python Transforms Guide](https://www.palantir.com/docs/foundry/transforms-python/transforms)
- [Transforms API Reference](https://www.palantir.com/docs/foundry/transforms-python/transforms-python-api)
- [@configure Reference](https://www.palantir.com/docs/foundry/api-reference/transforms-python-library/api-configure)
- [Incremental Transforms](https://www.palantir.com/docs/foundry/transforms-python/transforms-pipelines)

## Next Steps
- Query Ontology objects and actions: `palantir-core-workflow-b`
- Optimize pipeline performance: `palantir-performance-tuning`
- Deploy across environments: `palantir-multi-env-setup`
