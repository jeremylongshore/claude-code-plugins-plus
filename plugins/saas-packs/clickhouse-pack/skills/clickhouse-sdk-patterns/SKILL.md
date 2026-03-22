---
name: clickhouse-sdk-patterns
description: |
  Production-ready patterns for @clickhouse/client — streaming inserts, typed queries,
  error handling, and connection management.
  Use when building robust ClickHouse integrations, implementing streaming,
  or establishing team coding standards.
  Trigger: "clickhouse SDK patterns", "clickhouse client patterns",
  "clickhouse best practices", "clickhouse streaming insert".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse SDK Patterns

## Overview

Production patterns for `@clickhouse/client` — typed queries, streaming inserts,
error handling, and connection lifecycle management.

## Prerequisites

- `@clickhouse/client` installed (see `clickhouse-install-auth`)
- Familiarity with async/await and Node.js streams

## Instructions

### Pattern 1: Typed Query Helper

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

// Usage
interface EventCount {
  event_type: string;
  cnt: string;  // ClickHouse JSON returns numbers as strings
}

const rows = await query<EventCount>(
  'SELECT event_type, count() AS cnt FROM events WHERE user_id = {user_id:UInt64} GROUP BY event_type',
  { user_id: 42 }
);
```

**Note on parameterized queries:** ClickHouse uses `{name:Type}` syntax for parameters,
not `$1` or `?`. Always use typed parameters to prevent SQL injection.

### Pattern 2: Streaming Insert (Backpressure-Safe)

```typescript
import { createClient } from '@clickhouse/client';
import { Readable } from 'stream';

// For large inserts, stream data instead of buffering in memory
async function streamInsert(rows: AsyncIterable<Record<string, unknown>>) {
  const stream = new Readable({
    objectMode: true,
    read() {},  // push-based
  });

  const insertPromise = client.insert({
    table: 'events',
    values: stream,
    format: 'JSONEachRow',
  });

  for await (const row of rows) {
    // Backpressure: if push returns false, wait for drain
    if (!stream.push(row)) {
      await new Promise<void>((resolve) => stream.once('drain', resolve));
    }
  }
  stream.push(null);  // Signal end of stream

  await insertPromise;
}
```

### Pattern 3: Batch Insert with Retry

```typescript
async function batchInsert<T extends Record<string, unknown>>(
  table: string,
  rows: T[],
  batchSize = 10_000,
  maxRetries = 3,
): Promise<{ inserted: number; errors: Error[] }> {
  let inserted = 0;
  const errors: Error[] = [];

  for (let i = 0; i < rows.length; i += batchSize) {
    const batch = rows.slice(i, i + batchSize);
    let attempt = 0;

    while (attempt < maxRetries) {
      try {
        await client.insert({
          table,
          values: batch,
          format: 'JSONEachRow',
        });
        inserted += batch.length;
        break;
      } catch (err) {
        attempt++;
        if (attempt === maxRetries) {
          errors.push(err as Error);
        } else {
          await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt)));
        }
      }
    }
  }

  return { inserted, errors };
}
```

### Pattern 4: Streaming SELECT (Low Memory)

```typescript
// For large result sets, stream rows instead of loading all into memory
async function* streamQuery<T>(sql: string): AsyncGenerator<T> {
  const rs = await client.query({ query: sql, format: 'JSONEachRow' });
  const stream = rs.stream();

  for await (const rows of stream) {
    // Each chunk is an array of rows (typically ~8KB worth)
    for (const row of rows) {
      yield (row as { json: () => T }).json();
    }
  }
}

// Usage
for await (const event of streamQuery<{ event_type: string }>('SELECT * FROM events')) {
  process.stdout.write(`${event.event_type}\n`);
}
```

### Pattern 5: Error Handling

```typescript
import { ClickHouseError } from '@clickhouse/client';

async function safeQuery<T>(sql: string): Promise<{ data: T[] | null; error: string | null }> {
  try {
    const rs = await client.query({ query: sql, format: 'JSONEachRow' });
    return { data: await rs.json<T>(), error: null };
  } catch (err) {
    if (err instanceof ClickHouseError) {
      // ClickHouse server-side error (syntax, permissions, etc.)
      console.error(`ClickHouse error ${err.code}: ${err.message}`);
      return { data: null, error: `CH-${err.code}: ${err.message}` };
    }
    // Network or client-side error
    console.error('Client error:', (err as Error).message);
    return { data: null, error: (err as Error).message };
  }
}
```

### Pattern 6: Connection Lifecycle

```typescript
// Graceful shutdown — important for flush of pending inserts
process.on('SIGTERM', async () => {
  console.log('Closing ClickHouse connection...');
  await client.close();
  process.exit(0);
});

// Health check
async function isHealthy(): Promise<boolean> {
  try {
    const { success } = await client.ping();
    return success;
  } catch {
    return false;
  }
}
```

### Pattern 7: ClickHouse Settings Per Query

```typescript
// Override server settings for specific queries
const rs = await client.query({
  query: 'SELECT * FROM huge_table',
  format: 'JSONEachRow',
  clickhouse_settings: {
    max_threads: 4,                    // Limit parallelism
    max_memory_usage: 1_000_000_000,   // 1GB memory limit
    max_execution_time: 30,            // 30s timeout
    max_result_rows: 100_000,          // Cap result size
  },
});
```

## Format Reference

| Format | Use Case | Streaming |
|--------|----------|-----------|
| `JSONEachRow` | Standard JSON rows (NDJSON) | Yes |
| `JSONCompactEachRow` | Arrays instead of objects (smaller) | Yes |
| `CSV` | Export/import | Yes |
| `TabSeparated` | CLI-compatible output | Yes |
| `Parquet` | Analytics interchange | Yes |
| `Native` | Fastest binary format | Yes |

## Error Handling

| Error Code | Meaning | Action |
|------------|---------|--------|
| `SYNTAX_ERROR (62)` | Bad SQL | Fix query syntax |
| `UNKNOWN_TABLE (60)` | Table doesn't exist | Check table name, database |
| `TOO_MANY_SIMULTANEOUS_QUERIES (202)` | Connection overload | Reduce concurrency or pool |
| `MEMORY_LIMIT_EXCEEDED (241)` | Query uses too much RAM | Add filters, use streaming |
| `TIMEOUT_EXCEEDED (159)` | Query too slow | Optimize ORDER BY, add indexes |

## Resources

- [Node.js Client Docs](https://clickhouse.com/docs/integrations/javascript)
- [Client Examples (GitHub)](https://github.com/ClickHouse/clickhouse-js/tree/main/examples)
- [Query Settings Reference](https://clickhouse.com/docs/operations/settings/settings)

## Next Steps

Apply these patterns in `clickhouse-core-workflow-a` for real data modeling.
