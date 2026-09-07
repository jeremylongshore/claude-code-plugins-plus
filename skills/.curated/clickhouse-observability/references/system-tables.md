# System Table Queries & Reference

ClickHouse exposes its full operational state through `system.*` tables. These
queries are the foundation of monitoring — run them directly or wrap them in a
scrape/exporter. No external dependency is required beyond `system.*` read
access.

## Key Metrics from System Tables

```sql
-- Real-time server health snapshot
SELECT
    (SELECT count() FROM system.processes) AS running_queries,
    (SELECT value FROM system.metrics WHERE metric = 'MemoryTracking') AS memory_bytes,
    (SELECT value FROM system.metrics WHERE metric = 'Query') AS concurrent_queries,
    (SELECT count() FROM system.merges) AS active_merges,
    (SELECT value FROM system.asynchronous_metrics WHERE metric = 'Uptime') AS uptime_sec;

-- Query throughput (last hour, per minute)
SELECT
    toStartOfMinute(event_time) AS minute,
    count() AS queries,
    countIf(exception_code != 0) AS errors,
    round(avg(query_duration_ms)) AS avg_ms,
    round(quantile(0.95)(query_duration_ms)) AS p95_ms,
    formatReadableSize(sum(read_bytes)) AS total_read
FROM system.query_log
WHERE type IN ('QueryFinish', 'ExceptionWhileProcessing')
  AND event_time >= now() - INTERVAL 1 HOUR
GROUP BY minute ORDER BY minute;

-- Insert throughput (last hour)
SELECT
    toStartOfMinute(event_time) AS minute,
    count() AS inserts,
    sum(written_rows) AS rows_written,
    formatReadableSize(sum(written_bytes)) AS bytes_written
FROM system.query_log
WHERE type = 'QueryFinish' AND query_kind = 'Insert'
  AND event_time >= now() - INTERVAL 1 HOUR
GROUP BY minute ORDER BY minute;

-- Part count per table (merge health indicator)
SELECT database, table, count() AS parts, sum(rows) AS rows,
       formatReadableSize(sum(bytes_on_disk)) AS size
FROM system.parts WHERE active
GROUP BY database, table
HAVING parts > 50
ORDER BY parts DESC;
```

## Key System Tables for Monitoring

| Table | What to Monitor | Frequency |
|-------|-----------------|-----------|
| `system.processes` | Running queries, memory usage | Every 10s |
| `system.query_log` | Query performance history | Every 1m |
| `system.parts` | Part count, merge health | Every 1m |
| `system.merges` | Active merge progress | Every 30s |
| `system.metrics` | Server-wide gauges (connections, memory) | Every 10s |
| `system.events` | Cumulative counters | Every 1m |
| `system.replicas` | Replication lag | Every 30s |
| `system.disks` | Disk space | Every 5m |
