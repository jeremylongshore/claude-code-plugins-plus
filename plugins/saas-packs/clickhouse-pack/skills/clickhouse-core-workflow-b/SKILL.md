---
name: clickhouse-core-workflow-b
description: |
  Insert, query, and aggregate data in ClickHouse with real SQL patterns.
  Use when writing analytical queries, inserting data at scale, building
  dashboards, or implementing materialized views for pre-aggregation.
  Trigger with "clickhouse query", "clickhouse insert", "clickhouse aggregate",
  "clickhouse materialized view", "clickhouse SQL".
allowed-tools: Read, Write, Edit, Bash(npm:*)
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
# ClickHouse Insert & Query (Core Workflow B)

## Overview

Move data into ClickHouse efficiently, then answer analytical questions with
aggregations, funnels, retention, window functions, and materialized views.
This skill covers the read/write half of the core workflow: the fast-path insert
patterns that avoid "too many parts", the parameterized query API for Node.js,
and pre-aggregation via materialized views. The high-frequency patterns live
inline below; the deep query library and advanced engine patterns are broken out
into `references/` so you can drill in only when you need them.

## Prerequisites

- Tables already created — run `clickhouse-core-workflow-a` first if not.
- `@clickhouse/client` installed and connected (`CLICKHOUSE_HOST`, `CLICKHOUSE_USER`,
  `CLICKHOUSE_PASSWORD` in the environment).
- A target database/table (examples use `analytics.events`).

## Instructions

### Step 1: Bulk insert (the fast path)

Batch rows and let the client buffer. ClickHouse writes a new "part" per INSERT,
so many tiny inserts are the number-one performance mistake.

```typescript
import { createClient } from '@clickhouse/client';

const client = createClient({
  url: process.env.CLICKHOUSE_HOST!,
  username: process.env.CLICKHOUSE_USER ?? 'default',
  password: process.env.CLICKHOUSE_PASSWORD ?? '',
});

// Insert many rows efficiently — @clickhouse/client buffers internally
await client.insert({
  table: 'analytics.events',
  values: events,   // Array of objects matching table columns
  format: 'JSONEachRow',
});
```

Streaming a file (CSV, Parquet, etc.) uses the same call with a read stream and
the matching `format` (e.g. `CSVWithNames`).

**Insert best practices:**

- Batch rows: aim for 10K-100K rows per INSERT (not one at a time).
- ClickHouse creates a new "part" per INSERT — too many small inserts cause "too many parts".
- For real-time streams, buffer 1-5 seconds then flush.

### Step 2: Analytical queries

Aggregate with `count()`, `uniqExact()`, and time filters. The canonical
"top events by tenant" shape:

```sql
SELECT tenant_id, event_type, count() AS event_count, uniqExact(user_id) AS unique_users
FROM analytics.events
WHERE created_at >= now() - INTERVAL 7 DAY
GROUP BY tenant_id, event_type
ORDER BY event_count DESC
LIMIT 100;
```

Funnel, retention, and safe parameterized-query patterns are in
[references/queries.md](references/queries.md).

### Step 3: Pre-aggregation and windowing

For dashboards, pre-aggregate on INSERT with a materialized view backed by an
`AggregatingMergeTree` target, then merge states at read time. Window functions
(`row_number()`, running totals via `OVER (PARTITION BY ...)`) and the full
function reference table are in
[references/advanced.md](references/advanced.md).

## Output

Applying this skill produces:

- **Insert code** — a batched `client.insert(...)` call (or file stream) that
  loads rows without triggering "too many parts".
- **Query results** — aggregation rows returned as JSON via `rs.json()`, ready
  to feed a dashboard or API response.
- **Materialized view + target table** — DDL that keeps a small pre-rolled table
  updated automatically on every source INSERT.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Too many parts (300)` | Frequent small inserts | Batch inserts, increase `parts_to_throw_insert` |
| `Memory limit exceeded` | Large GROUP BY / JOIN | Add WHERE filters, increase `max_memory_usage` |
| `UNKNOWN_FUNCTION` | Wrong ClickHouse version | Check `SELECT version()` |
| `Cannot parse datetime` | Wrong format | Use `YYYY-MM-DD HH:MM:SS` format |

## Examples

- **Insert a batch of events** — Step 1 above; adapt `values` to your row shape.
- **Top events / funnel / retention / parameterized queries** — full runnable
  SQL and Node.js in [references/queries.md](references/queries.md).
- **Materialized view, window functions, function reference** — the pre-aggregation
  and windowing patterns plus the common-function cheat sheet in
  [references/advanced.md](references/advanced.md).

## Resources

- [SQL Reference](https://clickhouse.com/docs/sql-reference)
- [Aggregate Functions](https://clickhouse.com/docs/sql-reference/aggregate-functions)
- [Materialized Views Guide](https://clickhouse.com/blog/using-materialized-views-in-clickhouse)

## Next Steps

For error troubleshooting once queries are running, see `clickhouse-common-errors`.
For table and schema design, revisit `clickhouse-core-workflow-a`.
