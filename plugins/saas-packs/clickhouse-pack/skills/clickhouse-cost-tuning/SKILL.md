---
name: clickhouse-cost-tuning
description: |
  Optimize ClickHouse Cloud costs — compute scaling, storage tiering, compression,
  and query efficiency for lower bills.
  Use when analyzing ClickHouse Cloud bills, reducing storage costs,
  or optimizing compute utilization.
  Trigger: "clickhouse cost", "clickhouse billing", "reduce clickhouse spend",
  "clickhouse pricing", "clickhouse expensive", "clickhouse storage cost".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Cost Tuning

## Overview

Reduce ClickHouse Cloud costs through storage optimization, compression tuning,
TTL policies, compute scaling, and query efficiency improvements.

## Prerequisites

- ClickHouse Cloud account with billing access
- Understanding of current data volumes and query patterns

## Instructions

### Step 1: Understand ClickHouse Cloud Pricing

| Component | Pricing Model | Key Driver |
|-----------|---------------|------------|
| Compute | Per-hour per replica | vCPU + memory tier |
| Storage | Per GB-month | Compressed data on disk |
| Network | Per GB egress | Query result sizes |
| Backups | Per GB stored | Backup retention |

**Key insight:** ClickHouse bills on **compressed** storage, and ClickHouse
compresses extremely well (often 10-20x). Your cost driver is usually compute,
not storage.

### Step 2: Analyze Storage Usage

```sql
-- Storage cost breakdown by table
SELECT
    database,
    table,
    formatReadableSize(sum(bytes_on_disk)) AS compressed_size,
    formatReadableSize(sum(data_uncompressed_bytes)) AS raw_size,
    round(sum(data_uncompressed_bytes) / sum(bytes_on_disk), 1) AS compression_ratio,
    sum(rows) AS total_rows,
    count() AS parts
FROM system.parts
WHERE active
GROUP BY database, table
ORDER BY sum(bytes_on_disk) DESC;

-- Storage by column (find bloated columns)
SELECT
    table,
    column,
    type,
    formatReadableSize(sum(column_data_compressed_bytes)) AS compressed,
    formatReadableSize(sum(column_data_uncompressed_bytes)) AS raw,
    round(sum(column_data_uncompressed_bytes) / sum(column_data_compressed_bytes), 1) AS ratio
FROM system.parts_columns
WHERE active AND database = 'analytics'
GROUP BY table, column, type
ORDER BY sum(column_data_compressed_bytes) DESC
LIMIT 30;
```

### Step 3: Improve Compression

```sql
-- Check current codec per column
SELECT name, type, compression_codec
FROM system.columns
WHERE database = 'analytics' AND table = 'events';

-- Apply better codecs to large columns
ALTER TABLE analytics.events
    MODIFY COLUMN properties String CODEC(ZSTD(3));  -- JSON blobs

ALTER TABLE analytics.events
    MODIFY COLUMN created_at DateTime CODEC(DoubleDelta, ZSTD);  -- Timestamps

ALTER TABLE analytics.events
    MODIFY COLUMN user_id UInt64 CODEC(Delta, ZSTD);  -- Sequential IDs

-- Verify improvement after next merge
OPTIMIZE TABLE analytics.events FINAL;

-- Check new compression ratio
SELECT
    column,
    formatReadableSize(sum(column_data_compressed_bytes)) AS compressed,
    round(sum(column_data_uncompressed_bytes) / sum(column_data_compressed_bytes), 1) AS ratio
FROM system.parts_columns
WHERE active AND database = 'analytics' AND table = 'events'
GROUP BY column ORDER BY sum(column_data_compressed_bytes) DESC;
```

### Step 4: TTL for Data Lifecycle

```sql
-- Expire old data automatically (reduces storage)
ALTER TABLE analytics.events
    MODIFY TTL created_at + INTERVAL 90 DAY;

-- Move old data to cheaper storage tier (ClickHouse Cloud)
ALTER TABLE analytics.events
    MODIFY TTL
        created_at + INTERVAL 30 DAY TO VOLUME 'hot',
        created_at + INTERVAL 90 DAY TO VOLUME 'cold',
        created_at + INTERVAL 365 DAY DELETE;

-- Drop entire partitions manually (fastest way to delete bulk data)
ALTER TABLE analytics.events
    DROP PARTITION '202401';   -- Drops January 2024

-- Check TTL status
SELECT database, table, result_ttl_expression
FROM system.tables
WHERE database = 'analytics';
```

### Step 5: Compute Cost Reduction

```sql
-- ClickHouse Cloud: Scale compute dynamically
-- Configure in Cloud Console:
-- - Auto-scaling: min 2 / max 8 replicas
-- - Idle timeout: 5 minutes (auto-suspend when no queries)
-- - Use "Development" tier for staging environments

-- Reduce per-query compute consumption
SET max_threads = 4;                  -- Use fewer cores per query
SET max_memory_usage = 5000000000;    -- 5GB cap per query

-- Server-side async inserts (reduces insert compute)
SET async_insert = 1;
SET async_insert_max_data_size = 10000000;  -- Flush at 10MB
SET async_insert_busy_timeout_ms = 5000;    -- or every 5 seconds
```

### Step 6: Query Efficiency = Lower Costs

```sql
-- Find the most expensive queries (by data scanned)
SELECT
    normalized_query_hash,
    count() AS executions,
    formatReadableSize(sum(read_bytes)) AS total_read,
    round(avg(query_duration_ms)) AS avg_ms,
    any(substring(query, 1, 200)) AS sample
FROM system.query_log
WHERE type = 'QueryFinish'
  AND event_time >= now() - INTERVAL 7 DAY
GROUP BY normalized_query_hash
ORDER BY sum(read_bytes) DESC
LIMIT 20;

-- Use materialized views to avoid repeated full scans
-- Instead of: SELECT count() FROM events WHERE date = today()
-- Pre-compute:
-- CREATE MATERIALIZED VIEW daily_counts_mv TO daily_counts AS
--   SELECT toDate(created_at) AS date, count() AS cnt FROM events GROUP BY date;
-- Then: SELECT cnt FROM daily_counts WHERE date = today()

-- Use PREWHERE to read less data
SELECT user_id, properties FROM analytics.events
PREWHERE event_type = 'purchase'    -- Filter first, read fewer columns
WHERE created_at >= today() - 7;
```

### Step 7: Monitor Costs

```typescript
// Track query costs in your application
async function queryWithCostTracking<T>(
  client: ReturnType<typeof import('@clickhouse/client').createClient>,
  sql: string,
): Promise<{ rows: T[]; cost: { readRows: number; readBytes: number; durationMs: number } }> {
  const start = Date.now();
  const rs = await client.query({ query: sql, format: 'JSONEachRow' });
  const rows = await rs.json<T>();
  const durationMs = Date.now() - start;

  // Log for cost analysis
  console.log({
    query: sql.slice(0, 100),
    readRows: rs.response_headers['x-clickhouse-summary']
      ? JSON.parse(rs.response_headers['x-clickhouse-summary']).read_rows
      : 'unknown',
    durationMs,
  });

  return { rows, cost: { readRows: 0, readBytes: 0, durationMs } };
}
```

## Cost Optimization Checklist

- [ ] Compression codecs applied to large columns (ZSTD, Delta, DoubleDelta)
- [ ] TTL configured for data expiration
- [ ] Auto-scaling and idle suspension enabled (Cloud)
- [ ] Development/staging on smaller tiers
- [ ] Materialized views for dashboard queries
- [ ] `max_threads` limited for non-critical queries
- [ ] `async_insert` enabled for high-frequency small inserts
- [ ] Monthly cost review with `system.query_log` analysis

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Storage growing fast | No TTL, no drops | Add TTL or schedule partition drops |
| High compute bill | Full-scan queries | Add materialized views, fix ORDER BY |
| Egress charges | Large result sets | Add LIMIT, use aggregations |
| Idle compute cost | No auto-suspend | Enable idle timeout in Cloud console |

## Resources

- [ClickHouse Cloud Pricing](https://clickhouse.com/pricing)
- [Data Compression](https://clickhouse.com/docs/sql-reference/statements/create/table#column_compression_codec)
- [TTL for Data Management](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree#table_engine-mergetree-ttl)

## Next Steps

For architecture patterns, see `clickhouse-reference-architecture`.
