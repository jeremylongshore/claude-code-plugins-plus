---
name: clickhouse-cost-tuning
description: |
  Optimize ClickHouse Cloud costs — compute scaling, storage tiering, compression,
  and query efficiency for lower bills.
  Use when analyzing ClickHouse Cloud bills, reducing storage costs, or optimizing
  compute utilization.
  Trigger with "clickhouse cost", "clickhouse billing", "reduce clickhouse spend",
  "clickhouse pricing", "clickhouse expensive", "clickhouse storage cost".
allowed-tools: Read
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
# ClickHouse Cost Tuning

## Overview

Reduce ClickHouse Cloud costs through storage optimization, compression tuning,
TTL policies, compute scaling, and query efficiency improvements. This skill walks
the bill from top driver to fix: identify what you actually pay for, then apply the
codec, TTL, compute, and query changes that move the number.

Deep copy-paste queries for every step live in
[references/implementation.md](references/implementation.md); end-to-end scenarios
live in [references/examples.md](references/examples.md).

## Prerequisites

- ClickHouse Cloud account with billing access
- Understanding of current data volumes and query patterns

## Instructions

### Step 1: Understand what you pay for

ClickHouse Cloud bills on four axes — and the biggest one is usually **compute**,
not storage, because ClickHouse compresses data 10-20x.

| Component | Pricing Model | Key Driver |
|-----------|---------------|------------|
| Compute | Per-hour per replica | vCPU + memory tier |
| Storage | Per GB-month | Compressed data on disk |
| Network | Per GB egress | Query result sizes |
| Backups | Per GB stored | Backup retention |

### Step 2: Find the top cost driver

Break storage down by table, then by column, to find bloated data. The starter
query — full breakdowns in [references/implementation.md](references/implementation.md):

```sql
SELECT database, table,
    formatReadableSize(sum(bytes_on_disk)) AS compressed_size,
    round(sum(data_uncompressed_bytes) / sum(bytes_on_disk), 1) AS compression_ratio
FROM system.parts WHERE active
GROUP BY database, table ORDER BY sum(bytes_on_disk) DESC;
```

A column with a low compression ratio (e.g. 2x on a text/JSON blob) is your lever.

### Step 3: Improve compression

Apply codecs matched to the data shape — `ZSTD(3)` for JSON/text, `Delta, ZSTD`
for sequential IDs, `DoubleDelta, ZSTD` for timestamps — then `OPTIMIZE ... FINAL`
to re-merge. Full codec cheat sheet and verification queries in
[references/implementation.md](references/implementation.md).

### Step 4: Expire and tier old data with TTL

Add TTL to delete or move cold data automatically, or drop whole partitions for an
immediate one-time reclaim. See the tiered hot/cold/delete TTL pattern in
[references/implementation.md](references/implementation.md).

### Step 5: Cut compute cost

Enable auto-scaling and idle suspension in the Cloud Console, cap per-query cores
and memory (`max_threads`, `max_memory_usage`), and batch small writes with
`async_insert`. Exact settings in [references/implementation.md](references/implementation.md).

### Step 6: Make queries cheaper

Find the most-scanned queries in `system.query_log`, replace repeated full scans
with materialized views, and use `PREWHERE` to read fewer columns. Queries in
[references/implementation.md](references/implementation.md).

### Step 7: Monitor going forward

Track per-query read bytes/rows and duration in your application so cost regressions
surface early. TypeScript cost-tracking wrapper in
[references/implementation.md](references/implementation.md).

## Output

Applying this skill produces:

- A ranked storage breakdown (by table and column) identifying the top cost drivers.
- Concrete `ALTER TABLE ... MODIFY COLUMN ... CODEC(...)` statements for bloated columns.
- A TTL / partition-drop plan for cold data.
- Cloud compute settings (auto-scale bounds, idle timeout, per-query limits).
- A shortlist of the most expensive queries from `system.query_log` with materialized-view or `PREWHERE` fixes.
- The completed cost-optimization checklist in [references/implementation.md](references/implementation.md).

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Storage growing fast | No TTL, no drops | Add TTL or schedule partition drops |
| High compute bill | Full-scan queries | Add materialized views, fix ORDER BY |
| Egress charges | Large result sets | Add LIMIT, use aggregations |
| Idle compute cost | No auto-suspend | Enable idle timeout in Cloud console |

## Examples

Three worked scenarios take a real symptom through diagnosis → fix → verification —
see [references/examples.md](references/examples.md):

- **Storage bill doubled** — trace it to a poorly-compressed JSON column and cut the
  table ~60% with a `ZSTD(3)` codec.
- **Compute is the real driver** — replace a 30-second full-`count()` dashboard query
  with a materialized view and enable idle suspension.
- **Old data you never query** — add tiered hot/cold/delete TTL and drop stale
  partitions for an immediate reclaim.

## Resources

- [ClickHouse Cloud Pricing](https://clickhouse.com/pricing)
- [Data Compression](https://clickhouse.com/docs/sql-reference/statements/create/table#column_compression_codec)
- [TTL for Data Management](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree#table_engine-mergetree-ttl)

## Next Steps

For broader design patterns — schema layout, ingestion pipelines, and replica
topology that keep costs low by construction — see the
`clickhouse-reference-architecture` skill in this pack.
