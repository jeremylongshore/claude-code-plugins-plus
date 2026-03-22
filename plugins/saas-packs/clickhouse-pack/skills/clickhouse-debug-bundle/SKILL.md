---
name: clickhouse-debug-bundle
description: |
  Collect ClickHouse diagnostic data — system tables, query logs, merge status,
  and server metrics for support tickets and troubleshooting.
  Use when investigating persistent issues, preparing debug artifacts,
  or collecting evidence for ClickHouse support.
  Trigger: "clickhouse debug", "clickhouse diagnostics", "clickhouse support bundle",
  "collect clickhouse logs", "clickhouse system tables".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Debug Bundle

## Overview

Collect comprehensive diagnostic data from ClickHouse system tables for
troubleshooting performance issues, merge problems, or support escalation.

## Prerequisites

- Access to ClickHouse with `system.*` table read permissions
- `curl` or `clickhouse-client` available

## Instructions

### Step 1: Server Health Overview

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

### Step 2: Disk and Table Health

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

### Step 3: Query Performance Analysis

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

### Step 4: Merge and Mutation Status

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

### Step 5: Automated Debug Script

```bash
#!/bin/bash
# clickhouse-debug-bundle.sh
set -euo pipefail

CH_HOST="${CLICKHOUSE_HOST:-http://localhost:8123}"
CH_USER="${CLICKHOUSE_USER:-default}"
CH_PASS="${CLICKHOUSE_PASSWORD:-}"
BUNDLE="ch-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

ch_query() {
  curl -sS "${CH_HOST}" \
    --user "${CH_USER}:${CH_PASS}" \
    --data-binary "$1" 2>&1
}

echo "Collecting ClickHouse diagnostics..."

ch_query "SELECT version(), uptime(), currentDatabase()" > "$BUNDLE/version.txt"
ch_query "SELECT * FROM system.metrics FORMAT TabSeparatedWithNames" > "$BUNDLE/metrics.tsv"
ch_query "SELECT * FROM system.events FORMAT TabSeparatedWithNames" > "$BUNDLE/events.tsv"
ch_query "SELECT database, table, count() AS parts, sum(rows) AS rows, \
  formatReadableSize(sum(bytes_on_disk)) AS size FROM system.parts \
  WHERE active GROUP BY database, table ORDER BY sum(bytes_on_disk) DESC \
  FORMAT TabSeparatedWithNames" > "$BUNDLE/tables.tsv"
ch_query "SELECT * FROM system.merges FORMAT TabSeparatedWithNames" > "$BUNDLE/merges.tsv"
ch_query "SELECT * FROM system.query_log WHERE type IN ('ExceptionWhileProcessing') \
  AND event_time >= now() - INTERVAL 1 HOUR ORDER BY event_time DESC LIMIT 50 \
  FORMAT TabSeparatedWithNames" > "$BUNDLE/errors.tsv"
ch_query "SELECT * FROM system.replicas FORMAT TabSeparatedWithNames" > "$BUNDLE/replicas.tsv" 2>/dev/null || true

tar -czf "${BUNDLE}.tar.gz" "$BUNDLE"
rm -rf "$BUNDLE"
echo "Bundle created: ${BUNDLE}.tar.gz"
```

### Step 6: Node.js Debug Collector

```typescript
import { createClient } from '@clickhouse/client';

async function collectDebugBundle(client: ReturnType<typeof createClient>) {
  const queries = {
    version: 'SELECT version() AS ver, uptime() AS up',
    tables: `SELECT database, table, count() AS parts, sum(rows) AS rows
             FROM system.parts WHERE active GROUP BY database, table
             ORDER BY sum(bytes_on_disk) DESC LIMIT 20`,
    slow: `SELECT query_duration_ms, substring(query,1,200) AS q
           FROM system.query_log WHERE type='QueryFinish'
           AND event_time >= now() - INTERVAL 1 HOUR
           ORDER BY query_duration_ms DESC LIMIT 10`,
    errors: `SELECT exception_code, exception, substring(query,1,200) AS q
             FROM system.query_log WHERE type='ExceptionWhileProcessing'
             AND event_time >= now() - INTERVAL 1 HOUR LIMIT 10`,
    merges: 'SELECT * FROM system.merges',
  };

  const bundle: Record<string, unknown> = {};
  for (const [key, sql] of Object.entries(queries)) {
    try {
      const rs = await client.query({ query: sql, format: 'JSONEachRow' });
      bundle[key] = await rs.json();
    } catch (e) {
      bundle[key] = { error: (e as Error).message };
    }
  }

  return bundle;
}
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

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `system.query_log` empty | Logging disabled | Set `log_queries = 1` |
| Permission denied on system tables | Restricted user | Grant `SELECT ON system.*` |
| Bundle too large | Too much history | Narrow time window |

## Resources

- [System Tables Reference](https://clickhouse.com/docs/operations/system-tables)
- [Query Log](https://clickhouse.com/docs/operations/system-tables/query_log)
- [Server Metrics](https://clickhouse.com/docs/operations/system-tables/metrics)

## Next Steps

For connection and concurrency issues, see `clickhouse-rate-limits`.
