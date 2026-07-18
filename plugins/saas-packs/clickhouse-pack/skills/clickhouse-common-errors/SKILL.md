---
name: clickhouse-common-errors
description: |
  Diagnose and fix the top 15 ClickHouse errors — query failures, insert problems,
  memory limits, and merge issues.
  Use when a ClickHouse query or insert throws an exception, a server-side error
  appears in logs, or a failed query needs root-cause analysis.
  Trigger with "clickhouse error", "fix clickhouse", "clickhouse not working",
  "debug clickhouse", "clickhouse exception", "clickhouse syntax error".
allowed-tools: Read, Grep, Bash(curl:*)
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
# ClickHouse Common Errors

## Overview

Quick reference for the most common ClickHouse errors with real error codes,
diagnostic queries, and proven solutions. The three highest-frequency errors are
inline below; the full catalog of 10 errors plus system-table diagnostics lives
in [references/error-reference.md](references/error-reference.md).

## Prerequisites

- Access to a ClickHouse endpoint — either the native `clickhouse-client` or the
  HTTP interface (`curl` against `:8123`).
- Permission to read the `system.*` introspection tables (`system.parts`,
  `system.processes`, `system.query_log`, `system.columns`, `system.replicas`).
- The failing statement's text and, ideally, the raw exception string — the
  parenthetical name (e.g. `MEMORY_LIMIT_EXCEEDED`) and numeric code drive lookup.

## Instructions

Follow this loop to turn a raw ClickHouse exception into a verified fix:

1. **Capture the exception name and code.** Read the error string the client
   returned. If you only have a log file, use `Grep` to pull the matching line —
   `Grep` for `DB::Exception` or a specific token like `MEMORY_LIMIT_EXCEEDED`
   across the log to isolate the failure.
2. **Map it to a category.** Use the [Error Handling](#error-handling) code table
   to classify the error as Schema, Query, Performance, Permissions, Concurrency,
   Resources, or Insert-pattern.
3. **Apply the inline fix** for the three top errors (Too Many Parts, Memory
   Limit, Syntax) below, or open
   [references/error-reference.md](references/error-reference.md) for the other
   seven plus copy-paste diagnostic queries.
4. **Confirm with a system table.** Re-run the relevant `system.*` query (part
   count, `system.processes`, `system.query_log`) to prove the condition cleared
   rather than assuming the fix took.

### Top 3 errors (inline)

**Too Many Parts (Code 252)** — hundreds of tiny inserts outpace merges:

```sql
-- Check current part count per table
SELECT database, table, count() AS part_count
FROM system.parts WHERE active GROUP BY database, table ORDER BY part_count DESC;

-- Temporary relief; permanent fix is batching (10K+ rows per INSERT)
ALTER TABLE events MODIFY SETTING parts_to_throw_insert = 1000;  -- default 300
```

**Memory Limit Exceeded (Code 241)** — query wants more RAM than `max_memory_usage`:

```sql
SET max_memory_usage = 20000000000;             -- 20GB for this query, OR
SET max_bytes_before_external_group_by = 10000000000;  -- spill big GROUP BY to disk
```

**Syntax Error (Code 62)** — most often MySQL habits leaking in:

```sql
SELECT "user_id" FROM events;          -- double-quote (not `backtick`) identifiers
SELECT * FROM events LIMIT 10 OFFSET 20;  -- OFFSET keyword, not LIMIT 10, 20
```

See [references/error-reference.md](references/error-reference.md) for Unknown
Table, Timeout, DateTime parsing, Readonly, No Such Column, Type Mismatch, and
Distributed-table errors.

## Output

Working through this skill produces:

- A **classified diagnosis** — the error name, numeric code, and category from
  the table below.
- A **concrete remediation** — the exact `SET`, `ALTER`, or corrected SQL to run,
  plus whether it is a temporary relief valve or a permanent fix.
- A **verification query** against a `system.*` table confirming the condition
  cleared (e.g. part count back under threshold, no query stuck in
  `system.processes`).

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

If the error name is not in this table, search the raw exception text against the
[Error Codes Reference](https://clickhouse.com/docs/knowledgebase) and inspect
`system.query_log` (`WHERE type = 'ExceptionWhileProcessing'`) for the full
server-side context.

## Examples

**Diagnosing a stalled insert pipeline.** Inserts start failing with
`Too many parts (600)`. Classify as code 252 (Insert pattern), run the
`system.parts` count query to see which table is affected, raise
`parts_to_throw_insert` for immediate relief, then switch the writer to batched
inserts. Full walkthrough and the other nine errors are in
[references/error-reference.md](references/error-reference.md).

**Killing a runaway query.** A dashboard query hangs. Query `system.processes`
to find its `query_id`, then `KILL QUERY WHERE query_id = '...'`. The complete
set of diagnostic queries (running queries, recent errors, disk usage, merge
health) lives in the Diagnostic Queries section of
[references/error-reference.md](references/error-reference.md).

## Resources

- [Error Codes Reference](https://clickhouse.com/docs/knowledgebase)
- [System Tables](https://clickhouse.com/docs/operations/system-tables)
- [Query Log](https://clickhouse.com/docs/operations/system-tables/query_log)
- [references/error-reference.md](references/error-reference.md) — full 10-error
  catalog plus diagnostic queries
- For comprehensive debugging, see the `clickhouse-debug-bundle` skill.
