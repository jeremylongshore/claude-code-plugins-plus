# ClickHouse Diagnostic Queries

The full set of `system.*` queries the debug bundle runs, grouped by
investigation area. Run them in order for a complete health snapshot, or jump
to the section matching the symptom you are chasing.

## Step 1: Server Health Overview

```sql
-- Server version and uptime
SELECT
    version()                       AS version,
    uptime()                        AS uptime_seconds,
    formatReadableTimeDelta(uptime()) AS uptime_human,
    currentDatabase()               AS current_db;

-- Global metrics snapshot
SELECT metric, value, description
FROM system.metrics
WHERE metric IN (
    'Query', 'Merge', 'PartMutation', 'ReplicatedFetch',
    'TCPConnection', 'HTTPConnection', 'MemoryTracking',
    'BackgroundMergesAndMutationsPoolTask'
);
```

## Step 2: Disk and Table Health

```sql
-- Disk usage by table (top 20)
SELECT
    database,
    table,
    formatReadableSize(sum(bytes_on_disk))  AS disk_size,
    sum(rows)                               AS total_rows,
    count()                                 AS active_parts,
    max(modification_time)                  AS last_modified
FROM system.parts
WHERE active
GROUP BY database, table
ORDER BY sum(bytes_on_disk) DESC
LIMIT 20;

-- Tables with too many parts (merge pressure)
SELECT database, table, count() AS parts
FROM system.parts WHERE active
GROUP BY database, table
HAVING parts > 100
ORDER BY parts DESC;

-- Disk space per disk
SELECT
    name,
    path,
    formatReadableSize(total_space)     AS total,
    formatReadableSize(free_space)      AS free,
    round(free_space / total_space * 100, 1) AS free_pct
FROM system.disks;
```

## Step 3: Query Performance Analysis

```sql
-- Slowest queries in the last 24 hours
SELECT
    event_time,
    query_duration_ms,
    read_rows,
    read_bytes,
    result_rows,
    memory_usage,
    substring(query, 1, 200) AS query_preview
FROM system.query_log
WHERE type = 'QueryFinish'
  AND event_time >= now() - INTERVAL 24 HOUR
ORDER BY query_duration_ms DESC
LIMIT 20;

-- Failed queries (last 24h)
SELECT
    event_time,
    exception_code,
    exception,
    substring(query, 1, 200) AS query_preview
FROM system.query_log
WHERE type = 'ExceptionWhileProcessing'
  AND event_time >= now() - INTERVAL 24 HOUR
ORDER BY event_time DESC
LIMIT 20;

-- Query patterns (group by normalized query)
SELECT
    normalized_query_hash,
    count()                          AS executions,
    avg(query_duration_ms)           AS avg_ms,
    max(query_duration_ms)           AS max_ms,
    sum(read_rows)                   AS total_rows_read,
    formatReadableSize(sum(read_bytes)) AS total_read,
    any(substring(query, 1, 150))    AS sample_query
FROM system.query_log
WHERE type = 'QueryFinish'
  AND event_time >= now() - INTERVAL 24 HOUR
GROUP BY normalized_query_hash
ORDER BY sum(query_duration_ms) DESC
LIMIT 20;
```

## Step 4: Merge and Mutation Status

```sql
-- Active merges
SELECT
    database, table, elapsed, progress,
    num_parts, result_part_name,
    formatReadableSize(total_size_bytes_compressed) AS size
FROM system.merges;

-- Pending mutations
SELECT database, table, mutation_id, command, create_time, is_done
FROM system.mutations
WHERE NOT is_done
ORDER BY create_time DESC;

-- Replication health (if using ReplicatedMergeTree)
SELECT
    database, table,
    is_leader, total_replicas, active_replicas,
    queue_size, inserts_in_queue, merges_in_queue
FROM system.replicas
WHERE active_replicas < total_replicas OR queue_size > 0;
```

## Key System Tables

| Table | Purpose |
|-------|---------|
| `system.parts` | Data parts per table (size, rows, merge status) |
| `system.query_log` | Query history with timing and errors |
| `system.metrics` | Real-time server metrics (gauges) |
| `system.events` | Cumulative server counters |
| `system.merges` | Currently running merges |
| `system.mutations` | ALTER TABLE mutations (UPDATE/DELETE) |
| `system.replicas` | Replication status per table |
| `system.processes` | Currently executing queries |
| `system.disks` | Disk space and health |
