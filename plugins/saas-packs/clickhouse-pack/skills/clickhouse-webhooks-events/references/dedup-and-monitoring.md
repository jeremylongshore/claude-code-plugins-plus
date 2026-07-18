# Deduplication, Monitoring & Insert Best Practices

Deep reference for making ingestion idempotent, observing insert throughput and
errors, and tuning batch behavior. The main SKILL.md summarizes these; the full
DDL, monitoring queries, and the best-practices matrix live here.

## Deduplication with ReplacingMergeTree

Webhook retries and Kafka reprocessing deliver the same event more than once.
`ReplacingMergeTree` collapses rows sharing the same `ORDER BY` key, keeping the
row with the highest version — so a re-delivered `event_id` never double-counts.

```sql
-- For idempotent ingestion (webhook retries, Kafka reprocessing)
CREATE TABLE analytics.events_dedup (
    event_id    String,           -- Unique event identifier
    event_type  LowCardinality(String),
    user_id     UInt64,
    properties  String,
    created_at  DateTime,
    _version    UInt64 DEFAULT toUnixTimestamp(now())
)
ENGINE = ReplacingMergeTree(_version)
ORDER BY event_id;               -- Dedup key

-- Insert duplicate-safe: same event_id keeps latest _version
-- Query with FINAL for deduplicated results
SELECT * FROM analytics.events_dedup FINAL
WHERE created_at >= today() - 7;
```

## Insert Monitoring

`system.query_log` records every insert, so throughput and errors are queryable
without extra instrumentation.

```sql
-- Track insert throughput
SELECT
    toStartOfMinute(event_time) AS minute,
    count() AS inserts,
    sum(written_rows) AS rows_inserted,
    formatReadableSize(sum(written_bytes)) AS bytes_inserted
FROM system.query_log
WHERE type = 'QueryFinish'
  AND query_kind = 'Insert'
  AND event_time >= now() - INTERVAL 1 HOUR
GROUP BY minute
ORDER BY minute;

-- Check for insert errors
SELECT event_time, exception, substring(query, 1, 200)
FROM system.query_log
WHERE type = 'ExceptionWhileProcessing'
  AND query_kind = 'Insert'
  AND event_time >= now() - INTERVAL 1 HOUR
ORDER BY event_time DESC;
```

## Insert Best Practices

| Practice | Why |
|----------|-----|
| Batch 10K-100K rows per INSERT | Fewer parts, faster merges |
| Buffer 1-5 seconds for real-time | Balances latency vs throughput |
| Use `JSONEachRow` format | Client handles serialization |
| Compress with `ZSTD` on wire | Reduces network transfer |
| Use `ReplacingMergeTree` for retries | Handles duplicate delivery |
| Use `async_insert=1` for small batches | Server-side batching |
