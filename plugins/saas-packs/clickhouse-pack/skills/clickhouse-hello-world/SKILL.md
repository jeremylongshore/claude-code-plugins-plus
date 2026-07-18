---
name: clickhouse-hello-world
description: |
  Create your first ClickHouse table, insert data, and run analytical queries.
  Use when starting a new ClickHouse project, learning MergeTree basics,
  or testing your ClickHouse connection with real operations.
  Trigger with "clickhouse hello world", "first clickhouse table",
  "clickhouse quick start", "create clickhouse table", "clickhouse example".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Hello World

## Overview

Create a MergeTree table, insert rows with JSONEachRow, and run your first
analytical query -- all using the official `@clickhouse/client`. This is the
smoke test that proves your connection works and teaches the four MergeTree
concepts (`ORDER BY`, `PARTITION BY`, `TTL`, `LowCardinality`) reused in every
real schema.

## Prerequisites

- `@clickhouse/client` installed and connected (see the `clickhouse-install-auth`
  skill for connection setup).
- A reachable ClickHouse server (local Docker, ClickHouse Cloud, or self-hosted)
  with `CLICKHOUSE_HOST` / `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD` set as
  environment variables.

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

For the full engine menu (`ReplacingMergeTree`, `SummingMergeTree`, etc.) and the
column-type table, see [MergeTree engines & data types](references/mergetree-and-types.md).

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

### Step 4: Explore System Tables (optional)

Once data lands, inspect on-disk size and part counts via `system.parts` to
confirm your partitioning is healthy. Full query and column reference:
[exploring system tables](references/system-tables.md).

## Output

Running the three core steps against a fresh table produces:

- **Step 1** -- `Table "events" created.` (idempotent via `IF NOT EXISTS`).
- **Step 2** -- `Inserted 5 events.`
- **Step 3** -- one aggregated row per `event_type`, sorted by count descending:

```
page_view: 3 events, 3 users
click: 1 events, 1 users
purchase: 1 events, 1 users
```

ClickHouse returns numeric aggregates as JSON strings, so cast `total` /
`unique_users` before doing arithmetic in TypeScript.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Table already exists` | Re-running CREATE | Use `IF NOT EXISTS` |
| `Unknown column` | Typo in column name | Check `DESCRIBE TABLE events` |
| `Type mismatch` | Wrong data type in insert | Match types to schema |
| `Memory limit exceeded` | Query too broad | Add WHERE clauses, use LIMIT |

## Examples

Steps 1-3 form the canonical end-to-end example: create → insert → aggregate.
Two extensions live in the reference files:

- **Different engine or column types** -- swap `MergeTree` for
  `ReplacingMergeTree` (upserts) or add a `Decimal(18,2)` column:
  [MergeTree engines & data types](references/mergetree-and-types.md).
- **Verifying on-disk layout** -- the `system.parts` size/part-count query:
  [exploring system tables](references/system-tables.md).

## Resources

- [MergeTree Engine Docs](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree)
- [Data Types Reference](https://clickhouse.com/docs/sql-reference/data-types)
- [CREATE TABLE Syntax](https://clickhouse.com/docs/sql-reference/statements/create/table)

## Next Steps

Proceed to the `clickhouse-local-dev-loop` skill for Docker-based local
development and an iterative schema-editing workflow.
