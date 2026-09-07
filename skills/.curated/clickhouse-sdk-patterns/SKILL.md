---
name: clickhouse-sdk-patterns
description: |
  Production-ready patterns for @clickhouse/client — streaming inserts, typed
  queries, error handling, and connection management.
  Use when building robust ClickHouse integrations, implementing streaming
  inserts or low-memory streaming reads, or establishing team coding standards.
  Trigger with "clickhouse SDK patterns", "clickhouse client patterns",
  "clickhouse best practices", "clickhouse streaming insert".
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
# ClickHouse SDK Patterns

## Overview

Production patterns for `@clickhouse/client` — typed queries, streaming inserts,
error handling, and connection lifecycle management. Start from the typed query
helper below, then drill into `references/implementation.md` for the streaming,
batching, and lifecycle patterns.

## Prerequisites

- `@clickhouse/client` installed and authenticated (see `clickhouse-install-auth`)
- Node.js 18+ with a `CLICKHOUSE_HOST` / `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD` env set
- Familiarity with async/await and Node.js streams (backpressure, `drain`, `Readable`)

## Instructions

Apply the pattern that fits your workload. Steps 2–7 live in
[references/implementation.md](references/implementation.md) with full,
copy-pasteable code; the core typed-query skeleton stays here.

1. **Typed query helper** — the foundation every other pattern builds on. Define
   a generic `query<T>` wrapper that returns parsed rows (skeleton below).
2. **Streaming insert (backpressure-safe)** — stream large inserts through a
   `Readable` instead of buffering in memory; honor `drain`.
3. **Batch insert with retry** — chunk rows (default 10k) with exponential-backoff
   retries, returning `{ inserted, errors }`.
4. **Streaming SELECT (low memory)** — consume large result sets as an
   `AsyncGenerator` so you never load the full set into RAM.
5. **Error handling** — distinguish server-side `ClickHouseError` (code + message)
   from network/client errors and normalize into a structured result.
6. **Connection lifecycle** — flush pending inserts on `SIGTERM` via
   `client.close()`; expose a `ping()`-based health check.
7. **Per-query settings** — override `max_threads`, `max_memory_usage`,
   `max_execution_time`, and `max_result_rows` for heavy queries.

### Skeleton: Typed Query Helper

```typescript
import { createClient } from '@clickhouse/client';

const client = createClient({
  url: process.env.CLICKHOUSE_HOST!,
  username: process.env.CLICKHOUSE_USER ?? 'default',
  password: process.env.CLICKHOUSE_PASSWORD ?? '',
});

// Generic typed query — returns parsed JSON rows
async function query<T>(sql: string, params?: Record<string, unknown>): Promise<T[]> {
  const rs = await client.query({
    query: sql,
    query_params: params,
    format: 'JSONEachRow',
  });
  return rs.json<T>();
}
```

**Note on parameterized queries:** ClickHouse uses `{name:Type}` syntax for
parameters, not `$1` or `?`. Always use typed parameters to prevent SQL injection.

## Output

Applying these patterns produces:

- A single reusable `client` instance plus a generic `query<T>` helper that
  returns typed, parsed rows.
- Streaming insert/read paths that keep memory flat regardless of dataset size.
- A batch-insert result object `{ inserted: number; errors: Error[] }` you can act
  on programmatically.
- Normalized error results (`CH-<code>: <message>` for server-side failures) rather
  than raw thrown exceptions.
- Graceful shutdown that flushes pending inserts before the process exits.

## Error Handling

Map common ClickHouse server error codes to a corrective action:

| Error Code | Meaning | Action |
|------------|---------|--------|
| `SYNTAX_ERROR (62)` | Bad SQL | Fix query syntax |
| `UNKNOWN_TABLE (60)` | Table doesn't exist | Check table name, database |
| `TOO_MANY_SIMULTANEOUS_QUERIES (202)` | Connection overload | Reduce concurrency or pool |
| `MEMORY_LIMIT_EXCEEDED (241)` | Query uses too much RAM | Add filters, use streaming |
| `TIMEOUT_EXCEEDED (159)` | Query too slow | Optimize ORDER BY, add indexes |

Full `safeQuery` wrapper (server-vs-client error discrimination) is in
[references/implementation.md](references/implementation.md) under Pattern 5.

## Examples

Worked, runnable usage of each helper is in
[references/examples.md](references/examples.md). Quick look — a typed aggregation
query with named parameters:

```typescript
interface EventCount {
  event_type: string;
  cnt: string;  // ClickHouse JSON returns numbers as strings
}

const rows = await query<EventCount>(
  'SELECT event_type, count() AS cnt FROM events WHERE user_id = {user_id:UInt64} GROUP BY event_type',
  { user_id: 42 }
);
```

See [references/examples.md](references/examples.md) for streaming reads and
structured error-result usage.

## Resources

- [references/implementation.md](references/implementation.md) — full code for patterns 2–7 + format table
- [references/examples.md](references/examples.md) — worked, runnable usage examples
- [Node.js Client Docs](https://clickhouse.com/docs/integrations/javascript)
- [Client Examples (GitHub)](https://github.com/ClickHouse/clickhouse-js/tree/main/examples)
- [Query Settings Reference](https://clickhouse.com/docs/operations/settings/settings)

## Next Steps

Apply these patterns in `clickhouse-core-workflow-a` for real data modeling, then
tune query cost and concurrency with `clickhouse-cost-tuning` and
`clickhouse-performance-tuning`.
