---
name: clickhouse-hello-world
description: |
  Create your first ClickHouse table, insert data, and run analytical queries.
  Use when starting a new ClickHouse project, learning MergeTree basics,
  or testing your ClickHouse connection with real operations.
  Trigger: "clickhouse hello world", "first clickhouse table",
  "clickhouse quick start", "create clickhouse table", "clickhouse example".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Hello World

## Overview

Create a MergeTree table, insert rows with JSONEachRow, and run your first
analytical query -- all using the official `@clickhouse/client`.

## Prerequisites

- `@clickhouse/client` installed and connected (see `clickhouse-install-auth`)

## Instructions

### Step 1: Create a MergeTree Table

```typescript
import { createClient } from '@clickhouse/client';

const client = createClient({
  url: process.env.CLICKHOUSE_HOST ?? 'http://localhost:8123',
  username: process.env.CLICKHOUSE_USER ?? 'default',
  password: process.env.CLICKHOUSE_PASSWORD ?? '',
});

await client.command({
  query: `
    CREATE TABLE IF NOT EXISTS events (
      event_id    UUID DEFAULT generateUUIDv4(),
      event_type  LowCardinality(String),
      user_id     UInt64,
      payload     String,
      created_at  DateTime DEFAULT now()
    )
    ENGINE = MergeTree()
    ORDER BY (event_type, created_at)
    PARTITION BY toYYYYMM(created_at)
    TTL created_at + INTERVAL 90 DAY
  `,
});
console.log('Table "events" created.');
```

**Key concepts:**
- `MergeTree()` -- the foundational ClickHouse engine for analytics
- `ORDER BY` -- defines the primary index (sort key); pick columns you filter/group on
- `PARTITION BY` -- splits data into parts by month for efficient pruning
- `TTL` -- automatic data expiration
- `LowCardinality(String)` -- dictionary-encoded string, ideal for columns with < 10K distinct values

### Step 2: Insert Data with JSONEachRow

```typescript
await client.insert({
  table: 'events',
  values: [
    { event_type: 'page_view', user_id: 1001, payload: '{"url":"/home"}' },
    { event_type: 'click',     user_id: 1001, payload: '{"button":"signup"}' },
    { event_type: 'page_view', user_id: 1002, payload: '{"url":"/pricing"}' },
    { event_type: 'purchase',  user_id: 1002, payload: '{"amount":49.99}' },
    { event_type: 'page_view', user_id: 1003, payload: '{"url":"/docs"}' },
  ],
  format: 'JSONEachRow',
});
console.log('Inserted 5 events.');
```

### Step 3: Query the Data

```typescript
// Count events by type
const rs = await client.query({
  query: `
    SELECT
      event_type,
      count()          AS total,
      uniqExact(user_id) AS unique_users
    FROM events
    GROUP BY event_type
    ORDER BY total DESC
  `,
  format: 'JSONEachRow',
});

const rows = await rs.json<{
  event_type: string;
  total: string;        // ClickHouse returns numbers as strings in JSON
  unique_users: string;
}>();

for (const row of rows) {
  console.log(`${row.event_type}: ${row.total} events, ${row.unique_users} users`);
}
```

**Expected output:**
```
page_view: 3 events, 3 users
click: 1 events, 1 users
purchase: 1 events, 1 users
```

### Step 4: Explore System Tables

```typescript
// Check table size and row count
const stats = await client.query({
  query: `
    SELECT
      table,
      formatReadableSize(sum(bytes_on_disk)) AS disk_size,
      sum(rows) AS row_count,
      count() AS part_count
    FROM system.parts
    WHERE active AND database = currentDatabase() AND table = 'events'
    GROUP BY table
  `,
  format: 'JSONEachRow',
});
console.log('Table stats:', await stats.json());
```

## MergeTree Engine Quick Reference

| Engine | Use Case |
|--------|----------|
| `MergeTree` | General-purpose analytics |
| `ReplacingMergeTree` | Upserts (dedup by ORDER BY key) |
| `SummingMergeTree` | Auto-sum numeric columns on merge |
| `AggregatingMergeTree` | Pre-aggregated materialized views |
| `CollapsingMergeTree` | State changes / versioned rows |

## Common Data Types

| Type | Example | Notes |
|------|---------|-------|
| `UInt8/16/32/64` | `user_id UInt64` | Unsigned integers |
| `Int8/16/32/64` | `delta Int32` | Signed integers |
| `Float32/64` | `price Float64` | IEEE 754 |
| `Decimal(P,S)` | `amount Decimal(18,2)` | Exact decimal |
| `String` | `name String` | Variable-length bytes |
| `DateTime` | `created_at DateTime` | Unix timestamp (seconds) |
| `DateTime64(3)` | `ts DateTime64(3)` | Millisecond precision |
| `UUID` | `id UUID` | 128-bit UUID |
| `Array(T)` | `tags Array(String)` | Variable-length array |
| `LowCardinality(T)` | `status LowCardinality(String)` | Dictionary encoding |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Table already exists` | Re-running CREATE | Use `IF NOT EXISTS` |
| `Unknown column` | Typo in column name | Check `DESCRIBE TABLE events` |
| `Type mismatch` | Wrong data type in insert | Match types to schema |
| `Memory limit exceeded` | Query too broad | Add WHERE clauses, use LIMIT |

## Resources

- [MergeTree Engine Docs](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree)
- [Data Types Reference](https://clickhouse.com/docs/sql-reference/data-types)
- [CREATE TABLE Syntax](https://clickhouse.com/docs/sql-reference/statements/create/table)

## Next Steps

Proceed to `clickhouse-local-dev-loop` for Docker-based local development.
