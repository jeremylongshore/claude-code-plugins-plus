---
name: clickhouse-debug-bundle
description: |
  Collect ClickHouse diagnostic data — system tables, query logs, merge status,
  and server metrics for support tickets and troubleshooting.
  Use when investigating persistent issues, preparing debug artifacts,
  or collecting evidence for ClickHouse support.
  Trigger with "clickhouse debug", "clickhouse diagnostics",
  "clickhouse support bundle", "collect clickhouse logs",
  "clickhouse system tables".
allowed-tools: Read, Bash(curl:*), Bash(tar:*)
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
# ClickHouse Debug Bundle

## Overview

Collect comprehensive diagnostic data from ClickHouse `system.*` tables for
troubleshooting performance issues, merge problems, or support escalation. The
skill runs a graduated set of queries — server health, disk and table health,
query performance, and merge/mutation status — then packages the output into a
single artifact you can attach to a support ticket.

## Prerequisites

- Access to a ClickHouse server with `SELECT` permission on `system.*` tables
  (grant `SELECT ON system.*` to a restricted user if needed).
- Either `curl` (for the HTTP interface, port 8123) or `clickhouse-client`.
- Connection settings exported as environment variables so no credentials are
  hardcoded: `CLICKHOUSE_HOST`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`.
- For deep query-log analysis, `log_queries = 1` must be enabled on the server.

## Instructions

Work through the four diagnostic areas below. For an interactive investigation,
run the query for the symptom you are chasing; to produce a full artifact, run
the automated collector in Step 5. The complete query set for every step lives
in [references/diagnostic-queries.md](references/diagnostic-queries.md).

### Step 1: Server health overview

Confirm the server version, uptime, and current-load gauges first — this frames
every later finding.

```sql
SELECT
    version()                       AS version,
    uptime()                        AS uptime_seconds,
    formatReadableTimeDelta(uptime()) AS uptime_human,
    currentDatabase()               AS current_db;
```

Then snapshot `system.metrics` for the key gauges (`Query`, `Merge`,
`MemoryTracking`, connection counts). Full metric list in the reference.

### Step 2: Disk and table health

Find the largest tables and any table under merge pressure (too many active
parts). The full query set covers per-table disk usage, the `parts > 100`
merge-pressure check, and per-disk free space from `system.disks`.

```sql
-- Tables with too many parts (merge pressure)
SELECT database, table, count() AS parts
FROM system.parts WHERE active
GROUP BY database, table
HAVING parts > 100
ORDER BY parts DESC;
```

### Step 3: Query performance analysis

Pull the slowest queries, failed queries, and normalized query patterns from
`system.query_log` over the last 24 hours. See the reference for the slow-query,
exception, and `normalized_query_hash` aggregation queries.

### Step 4: Merge and mutation status

Inspect `system.merges`, pending `system.mutations`, and `system.replicas` to
spot stuck merges, long-running mutations, or replicas that have fallen behind.
Full queries in the reference.

### Step 5: Run the automated collector

For a one-shot artifact, use the bash or Node.js collector in
[references/collectors.md](references/collectors.md). Both authenticate from the
environment variables above and write one file per diagnostic area:

```bash
CLICKHOUSE_HOST=http://localhost:8123 \
CLICKHOUSE_USER=default \
CLICKHOUSE_PASSWORD=secret \
  ./clickhouse-debug-bundle.sh
```

## Output

The automated collector produces a timestamped gzipped tarball
`ch-debug-YYYYMMDD-HHMMSS.tar.gz` containing one TSV/TXT file per diagnostic
area:

| File | Contents |
|------|----------|
| `version.txt` | Server version, uptime, current database |
| `metrics.tsv` | Full `system.metrics` snapshot (gauges) |
| `events.tsv` | Full `system.events` snapshot (cumulative counters) |
| `tables.tsv` | Per-table parts, rows, and on-disk size |
| `merges.tsv` | Currently running merges |
| `errors.tsv` | Exceptions from `system.query_log` (last hour) |
| `replicas.tsv` | Replication status (best-effort; empty if not replicated) |

An interactive run instead returns the result set of each query directly. The
Node.js collector returns a single JSON object keyed by diagnostic area, with a
per-key `{ error }` entry when an individual query fails.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `system.query_log` empty | Logging disabled | Set `log_queries = 1` |
| Permission denied on system tables | Restricted user | Grant `SELECT ON system.*` |
| Bundle too large | Too much history | Narrow the `INTERVAL` time window |
| `system.replicas` errors | Table not replicated | Expected — collector ignores it (`\|\| true`) |
| `curl: (7) connection refused` | Wrong host/port | Verify `CLICKHOUSE_HOST` (HTTP interface is 8123) |

## Examples

**Investigate a slow dashboard (interactive).** Run Step 1 to confirm the server
is healthy, then Step 3's slow-query select to find the offending queries and
Step 2's merge-pressure check to rule out a table with 100+ parts starving the
merge pool.

**Prepare a support ticket (artifact).** Export the three connection variables
and run the Step 5 bash collector. Attach the resulting
`ch-debug-YYYYMMDD-HHMMSS.tar.gz` to the ticket — it gives ClickHouse support
the version, metrics, table sizes, active merges, and recent exceptions in one
file.

**Collect from application code.** Import `collectDebugBundle` from
[references/collectors.md](references/collectors.md), pass it an authenticated
`@clickhouse/client` handle, and persist the returned JSON object alongside the
error you are triaging.

Full, runnable query text and both collector scripts:
[references/diagnostic-queries.md](references/diagnostic-queries.md) and
[references/collectors.md](references/collectors.md).

## Resources

- [System Tables Reference](https://clickhouse.com/docs/operations/system-tables)
- [Query Log](https://clickhouse.com/docs/operations/system-tables/query_log)
- [Server Metrics](https://clickhouse.com/docs/operations/system-tables/metrics)
- [references/diagnostic-queries.md](references/diagnostic-queries.md) — every diagnostic query, grouped by area
- [references/collectors.md](references/collectors.md) — bash + Node.js bundle collectors with auth notes

## Next Steps

For connection and concurrency issues that show up as failed queries or
exhausted connection gauges in this bundle, follow up with the
`clickhouse-rate-limits` skill.
