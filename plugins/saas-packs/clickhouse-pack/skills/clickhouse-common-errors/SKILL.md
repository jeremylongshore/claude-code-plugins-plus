---
name: clickhouse-common-errors
description: |
  Diagnose and fix the top 15 ClickHouse errors — query failures, insert problems,
  memory limits, and merge issues.
  Use when encountering ClickHouse exceptions, debugging failed queries,
  or troubleshooting server-side errors.
  Trigger: "clickhouse error", "fix clickhouse", "clickhouse not working",
  "debug clickhouse", "clickhouse exception", "clickhouse syntax error".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Common Errors

## Overview

Quick reference for the most common ClickHouse errors with real error codes,
diagnostic queries, and proven solutions.

## Prerequisites

- Access to ClickHouse (client or HTTP interface)
- Ability to query `system.*` tables

## Error Reference

### 1. Too Many Parts (Code 252)

```
DB::Exception: Too many parts (600). Merges are processing significantly slower than inserts.
```

**Cause:** Each INSERT creates a new data part. Hundreds of tiny inserts per second
overwhelm the merge process.

**Fix:**
```sql
-- Check current part count per table
SELECT database, table, count() AS part_count
FROM system.parts WHERE active GROUP BY database, table ORDER BY part_count DESC;

-- Temporary: raise the limit
ALTER TABLE events MODIFY SETTING parts_to_throw_insert = 1000;

-- Permanent: batch your inserts (10K+ rows per INSERT)
-- See clickhouse-sdk-patterns for batching code
```

### 2. Memory Limit Exceeded (Code 241)

```
DB::Exception: Memory limit (for query) exceeded: ... (MEMORY_LIMIT_EXCEEDED)
```

**Cause:** Query allocates more RAM than `max_memory_usage` (default ~10GB).

**Fix:**
```sql
-- Check what's consuming memory
SELECT query, memory_usage, peak_memory_usage
FROM system.processes ORDER BY peak_memory_usage DESC;

-- Option A: Increase limit for this query
SET max_memory_usage = 20000000000;  -- 20GB

-- Option B: Reduce data scanned
SELECT ... FROM events
WHERE created_at >= today() - 7  -- Add time filters
LIMIT 10000;                      -- Cap result size

-- Option C: Enable disk spill for large sorts/GROUP BY
SET max_bytes_before_external_sort = 10000000000;
SET max_bytes_before_external_group_by = 10000000000;
```

### 3. Syntax Error (Code 62)

```
DB::Exception: Syntax error: ... Expected ... before ... (SYNTAX_ERROR)
```

**Common causes:**
```sql
-- Wrong: using backticks for identifiers (MySQL habit)
SELECT `user_id` FROM events;
-- Fix: use double-quotes or no quotes
SELECT "user_id" FROM events;
SELECT user_id FROM events;

-- Wrong: LIMIT with OFFSET keyword
SELECT * FROM events LIMIT 10, 20;
-- Fix: use LIMIT ... OFFSET
SELECT * FROM events LIMIT 10 OFFSET 20;

-- Wrong: using != in older versions
WHERE status != 'active';
-- Fix: use <>
WHERE status <> 'active';
```

### 4. Unknown Table (Code 60)

```
DB::Exception: Table default.events does not exist. (UNKNOWN_TABLE)
```

**Fix:**
```sql
-- List all tables in the database
SHOW TABLES FROM default;

-- Check all databases
SHOW DATABASES;

-- The table might be in a different database
SELECT database, name FROM system.tables WHERE name LIKE '%events%';
```

### 5. Timeout Exceeded (Code 159)

```
DB::Exception: Timeout exceeded: elapsed ... seconds, max ... (TIMEOUT_EXCEEDED)
```

**Fix:**
```sql
-- Increase timeout for this query
SET max_execution_time = 120;  -- seconds

-- Find slow queries in history
SELECT
    query,
    query_duration_ms,
    read_rows,
    result_rows,
    memory_usage
FROM system.query_log
WHERE type = 'QueryFinish'
ORDER BY query_duration_ms DESC
LIMIT 10;
```

### 6. Cannot Parse DateTime

```
DB::Exception: Cannot parse datetime ... (CANNOT_PARSE_DATETIME)
```

**Fix:**
```sql
-- ClickHouse expects: YYYY-MM-DD HH:MM:SS
-- Wrong: ISO 8601 with T and Z
INSERT INTO events (created_at) VALUES ('2025-01-15T10:30:00Z');

-- Fix: strip T and Z
INSERT INTO events (created_at) VALUES ('2025-01-15 10:30:00');

-- Or parse it explicitly
SELECT parseDateTimeBestEffort('2025-01-15T10:30:00Z');
```

### 7. Readonly Mode (Code 164)

```
DB::Exception: ... is in readonly mode (READONLY)
```

**Cause:** User lacks write permissions or server is in readonly mode.

**Fix:**
```sql
-- Check user permissions
SHOW GRANTS FOR CURRENT_USER;

-- Check server setting
SELECT name, value FROM system.settings WHERE name = 'readonly';
```

### 8. No Such Column (Code 16)

```
DB::Exception: Missing columns: 'user_name' ... (NO_SUCH_COLUMN_IN_TABLE)
```

**Fix:**
```sql
-- Inspect actual column names
DESCRIBE TABLE events;

-- Check column types too
SELECT name, type, default_kind, default_expression
FROM system.columns WHERE database = 'default' AND table = 'events';
```

### 9. Type Mismatch on Insert

```
DB::Exception: Cannot convert ... to UInt64 (TYPE_MISMATCH)
```

**Fix:**
```sql
-- Check expected types
DESCRIBE TABLE events;

-- Cast in your INSERT if needed
INSERT INTO events (user_id) VALUES (toUInt64('12345'));

-- In Node.js, ensure numeric types:
await client.insert({
  table: 'events',
  values: [{ user_id: 42 }],  // number, not "42"
  format: 'JSONEachRow',
});
```

### 10. Distributed Table Errors

```
DB::Exception: All connection tries failed. ... (ALL_CONNECTION_TRIES_FAILED)
```

**Fix:**
```sql
-- Check cluster health
SELECT * FROM system.clusters;

-- Check replica status
SELECT database, table, is_leader, total_replicas, active_replicas
FROM system.replicas;
```

## Diagnostic Queries

```sql
-- Currently running queries
SELECT query_id, user, query, elapsed, read_rows, memory_usage
FROM system.processes;

-- Kill a stuck query
KILL QUERY WHERE query_id = 'abc-123';

-- Recent errors from query log
SELECT event_time, query, exception_code, exception
FROM system.query_log
WHERE type = 'ExceptionWhileProcessing'
ORDER BY event_time DESC
LIMIT 20;

-- Disk usage by table
SELECT
    database, table,
    formatReadableSize(sum(bytes_on_disk)) AS size,
    sum(rows) AS total_rows,
    count() AS parts
FROM system.parts WHERE active
GROUP BY database, table
ORDER BY sum(bytes_on_disk) DESC;

-- Merge health
SELECT database, table, progress, elapsed, num_parts
FROM system.merges;
```

## Error Handling

| Error Code | Name | Category |
|------------|------|----------|
| 16 | NO_SUCH_COLUMN_IN_TABLE | Schema |
| 60 | UNKNOWN_TABLE | Schema |
| 62 | SYNTAX_ERROR | Query |
| 159 | TIMEOUT_EXCEEDED | Performance |
| 164 | READONLY | Permissions |
| 202 | TOO_MANY_SIMULTANEOUS_QUERIES | Concurrency |
| 241 | MEMORY_LIMIT_EXCEEDED | Resources |
| 252 | TOO_MANY_PARTS | Insert pattern |

## Resources

- [Error Codes Reference](https://clickhouse.com/docs/knowledgebase)
- [System Tables](https://clickhouse.com/docs/operations/system-tables)
- [Query Log](https://clickhouse.com/docs/operations/system-tables/query_log)

## Next Steps

For comprehensive debugging, see `clickhouse-debug-bundle`.
