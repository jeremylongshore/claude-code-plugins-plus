---
name: clickhouse-performance-tuning
description: |
  Optimize ClickHouse query performance with indexing, projections, settings
  tuning, and query analysis using system tables.
  Use when queries are slow, investigating performance bottlenecks, or tuning
  ClickHouse server settings.
  Trigger with "clickhouse performance", "optimize clickhouse query",
  "clickhouse slow query", "clickhouse indexing", "clickhouse tuning",
  "clickhouse projections".
allowed-tools: Read, Write, Edit
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
# ClickHouse Performance Tuning

## Overview

Diagnose and fix ClickHouse performance issues using query analysis, proper indexing,
projections, materialized views, and server settings tuning. Work top-down: measure
first with `system.query_log`, then apply the single highest-leverage fix (usually the
ORDER BY key), then re-measure to confirm.

## Prerequisites

- ClickHouse tables with data (see `clickhouse-core-workflow-a`)
- Access to `system.query_log` and `system.parts`

## Instructions

The tuning workflow is seven independent steps. Diagnose first, then reach for the fix
that matches the bottleneck. Each step's full SQL lives in
[references/implementation.md](references/implementation.md) — start there for the
complete, copy-paste commands.

1. **Diagnose slow queries** — rank the last 24h of `system.query_log` by
   `query_duration_ms`, then inspect a suspect query with `EXPLAIN PLAN` /
   `EXPLAIN PIPELINE`.
2. **ORDER BY key optimization** — the primary lever. Filtering on the ORDER BY prefix
   skips whole granules; a mismatched key forces a full scan.
3. **Data skipping indexes** — `bloom_filter` for high-cardinality lookups, `set` for
   low-cardinality columns, `minmax` for range filters on non-key columns.
4. **Projections** — automatic pre-aggregation ClickHouse picks transparently when a
   query matches the projection's shape.
5. **Server settings** — `max_threads`, external sort/group-by spill, `async_insert`,
   and friends, set per-query or per-session.
6. **Materialized views** — pre-aggregate on INSERT into an `AggregatingMergeTree` so
   dashboard reads hit milliseconds, not seconds.
7. **Query patterns** — `PREWHERE`, `LIMIT BY`, and avoiding `FINAL`.

The essential first move — find the slowest queries:

```sql
SELECT event_time, query_duration_ms, read_rows, read_bytes,
       substring(query, 1, 300) AS query_preview
FROM system.query_log
WHERE type = 'QueryFinish'
  AND event_time >= now() - INTERVAL 24 HOUR
  AND query_duration_ms > 1000   -- > 1 second
ORDER BY query_duration_ms DESC
LIMIT 20;
```

## Output

Applying this workflow produces:

- A ranked list of the slowest queries with their `read_rows` / `read_bytes` cost.
- One or more concrete schema/query changes: a corrected `ORDER BY` key, added data
  skipping indexes, a projection, a materialized view, or tuned session settings.
- A before/after measurement from `system.query_log` proving the change reduced
  `read_rows`, `read_bytes`, `query_duration_ms`, or `memory_usage`.

## Error Handling

| Issue | Indicator | Solution |
|-------|-----------|----------|
| Full table scan | `read_rows` = total rows | Fix ORDER BY to match filters |
| Memory exceeded | Error 241 | Add LIMIT, use streaming, increase limit |
| Slow GROUP BY | High `read_bytes` | Add materialized view or projection |
| Merge backlog | Parts > 300 | Reduce insert frequency, increase merge threads |

## Examples

Worked before/after scenarios — full-scan → ORDER BY fix, slow GROUP BY → projection,
confirming a skipping index fires, and the query-cost measurement query — are in
[references/examples.md](references/examples.md). The core measurement, run right after
any query you are tuning:

```sql
SELECT query_duration_ms, read_rows,
       formatReadableSize(read_bytes) AS read_size,
       formatReadableSize(memory_usage) AS memory
FROM system.query_log
WHERE query_id = currentQueryId() AND type = 'QueryFinish';
```

## Resources

- [references/implementation.md](references/implementation.md) — full 7-step SQL walkthrough
- [references/examples.md](references/examples.md) — worked before/after tuning examples
- [Projections](https://clickhouse.com/docs/sql-reference/statements/alter/projection)
- [Data Skipping Indexes](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree#table_engine-mergetree-data_skipping-indexes)
- [MergeTree Settings](https://clickhouse.com/docs/operations/settings/merge-tree-settings)

## Next Steps

For cost optimization, see `clickhouse-cost-tuning`.
