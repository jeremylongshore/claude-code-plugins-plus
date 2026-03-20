# Advanced Performance Patterns

## Query Performance Analysis

```sql
-- Find slow queries from query history
SELECT
    query_id,
    query_text,
    duration / 1000 as seconds,
    rows_produced,
    bytes_read,
    start_time
FROM system.query.history
WHERE duration > 60000  -- > 60 seconds
  AND start_time > current_timestamp() - INTERVAL 24 HOURS
ORDER BY duration DESC
LIMIT 20;

-- Analyze query plan
EXPLAIN FORMATTED
SELECT * FROM main.silver.orders
WHERE order_date > '2024-01-01'
  AND region = 'US';

-- Check table scan statistics
SELECT
    table_name,
    SUM(bytes_read) / 1024 / 1024 / 1024 as gb_read,
    SUM(rows_produced) as total_rows,
    COUNT(*) as query_count
FROM system.query.history
WHERE start_time > current_timestamp() - INTERVAL 7 DAYS
GROUP BY table_name
ORDER BY gb_read DESC;
```

## Caching Strategy

```python
from pyspark.sql import DataFrame
from pyspark import StorageLevel

class CacheManager:
    """Manage Spark DataFrame caching."""

    def __init__(self, spark):
        self.spark = spark
        self._cache_registry = {}

    def cache_table(self, table_name: str, cache_level: str = "MEMORY_AND_DISK") -> DataFrame:
        """Cache table with specified storage level."""
        if table_name in self._cache_registry:
            return self._cache_registry[table_name]

        df = self.spark.table(table_name)

        if cache_level == "MEMORY_ONLY":
            df.cache()
        elif cache_level == "MEMORY_AND_DISK":
            df.persist(StorageLevel.MEMORY_AND_DISK)
        elif cache_level == "DISK_ONLY":
            df.persist(StorageLevel.DISK_ONLY)

        df.count()  # Trigger caching
        self._cache_registry[table_name] = df
        return df

    def uncache_all(self):
        """Clear all cached DataFrames."""
        for df in self._cache_registry.values():
            df.unpersist()
        self._cache_registry.clear()
        self.spark.catalog.clearCache()
```

Enable Delta Cache in cluster config:
```
"spark.databricks.io.cache.enabled": "true"
"spark.databricks.io.cache.maxDiskUsage": "50g"
```

## Join Optimization

```python
from pyspark.sql import DataFrame
from pyspark.sql.functions import broadcast

def optimize_join(df_large: DataFrame, df_small: DataFrame, join_key: str, small_table_threshold_mb: int = 100) -> DataFrame:
    """Use broadcast join for small tables, sort-merge for large."""
    small_size_mb = df_small.count() * 100 / 1024 / 1024
    if small_size_mb < small_table_threshold_mb:
        return df_large.join(broadcast(df_small), join_key)
    else:
        return df_large.join(df_small, join_key, "inner")

def create_bucketed_table(spark, df: DataFrame, table_name: str, bucket_columns: list, num_buckets: int = 100):
    """Create bucketed table for join optimization."""
    df.write.bucketBy(num_buckets, *bucket_columns).sortBy(*bucket_columns).saveAsTable(table_name)
```

## Performance Benchmark

```python
import time

def benchmark_query(spark, query: str, runs: int = 3) -> dict:
    """Benchmark query execution time."""
    times = []
    for _ in range(runs):
        spark.catalog.clearCache()
        start = time.time()
        spark.sql(query).collect()
        times.append(time.time() - start)

    return {
        "min": min(times),
        "max": max(times),
        "avg": sum(times) / len(times),
        "runs": runs,
    }
```
