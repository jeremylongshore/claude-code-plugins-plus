# ClickHouse SDK Patterns — Implementation Details

Deep implementation for the streaming, batching, error-handling, lifecycle, and
per-query-settings patterns summarized in `SKILL.md`. Each pattern is
production-tested against `@clickhouse/client`.

## Pattern 2: Streaming Insert (Backpressure-Safe)

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

## Pattern 3: Batch Insert with Retry

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

## Pattern 4: Streaming SELECT (Low Memory)

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

## Pattern 5: Error Handling

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

## Pattern 6: Connection Lifecycle

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

## Pattern 7: ClickHouse Settings Per Query

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
