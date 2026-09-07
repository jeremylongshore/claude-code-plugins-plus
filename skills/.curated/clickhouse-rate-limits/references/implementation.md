# ClickHouse Rate Limits — Client & Server Implementation

Full detail for configuring server-side quotas and building client-side
concurrency controls. The SKILL.md carries the high-level workflow and the
essential skeletons; this file carries the complete, copy-pasteable code.

## Server-Side Limits Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `max_concurrent_queries` | 100 | Max queries running simultaneously |
| `max_connections` | 4096 | Max TCP/HTTP connections |
| `max_memory_usage` | ~10GB | Per-query memory limit |
| `max_execution_time` | 0 (unlimited) | Per-query timeout in seconds |
| `max_threads` | CPU cores | Threads per query |

**ClickHouse Cloud API limit:** The Cloud management API (not the query interface)
is limited to 10 requests per 10 seconds.

## Per-User Quotas and Settings Profiles

```sql
-- Create a quota that limits query resources per user
CREATE QUOTA IF NOT EXISTS app_quota
    FOR INTERVAL 1 HOUR MAX
        queries = 10000,
        result_rows = 100000000,
        read_rows = 1000000000,
        execution_time = 3600
    TO app_user;

-- Create a profile with resource limits
CREATE SETTINGS PROFILE IF NOT EXISTS app_profile
    SETTINGS
        max_memory_usage = 5000000000,      -- 5GB per query
        max_execution_time = 30,             -- 30s timeout
        max_threads = 4,                     -- 4 threads per query
        max_concurrent_queries_for_user = 10 -- 10 parallel queries
    TO app_user;
```

## Client-Side Connection Pooling

```typescript
import { createClient } from '@clickhouse/client';

// The @clickhouse/client manages HTTP keep-alive connections internally
const client = createClient({
  url: process.env.CLICKHOUSE_HOST!,
  username: process.env.CLICKHOUSE_USER!,
  password: process.env.CLICKHOUSE_PASSWORD!,
  max_open_connections: 10,   // Connection pool size
  request_timeout: 30_000,    // 30s per request
  compression: {
    request: true,            // Compress request bodies (saves bandwidth)
    response: true,           // Decompress responses
  },
});
```

## Application-Level Concurrency Control

```typescript
import PQueue from 'p-queue';

// Limit concurrent ClickHouse queries from your app
const queryQueue = new PQueue({
  concurrency: 5,          // Max 5 concurrent queries
  timeout: 30_000,         // 30s timeout per query
  throwOnTimeout: true,
});

async function rateLimitedQuery<T>(sql: string): Promise<T[]> {
  return queryQueue.add(async () => {
    const rs = await client.query({ query: sql, format: 'JSONEachRow' });
    return rs.json<T>();
  });
}
```

## Retry on Concurrency Errors

```typescript
async function queryWithRetry<T>(
  sql: string,
  maxRetries = 3,
): Promise<T[]> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const rs = await client.query({ query: sql, format: 'JSONEachRow' });
      return await rs.json<T>();
    } catch (err: any) {
      const msg = err.message ?? '';
      const isRetryable =
        msg.includes('TOO_MANY_SIMULTANEOUS_QUERIES') ||
        msg.includes('TIMEOUT_EXCEEDED') ||
        msg.includes('NETWORK_ERROR');

      if (!isRetryable || attempt === maxRetries) throw err;

      const delay = 1000 * Math.pow(2, attempt) + Math.random() * 500;
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Insert Throttling

```typescript
// Buffer inserts to avoid "too many parts"
class InsertBuffer<T extends Record<string, unknown>> {
  private buffer: T[] = [];
  private timer: NodeJS.Timeout | null = null;

  constructor(
    private client: ReturnType<typeof import('@clickhouse/client').createClient>,
    private table: string,
    private batchSize = 10_000,
    private flushIntervalMs = 5_000,
  ) {}

  async add(row: T) {
    this.buffer.push(row);
    if (this.buffer.length >= this.batchSize) {
      await this.flush();
    } else if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), this.flushIntervalMs);
    }
  }

  async flush() {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    if (this.buffer.length === 0) return;

    const batch = this.buffer.splice(0);
    await this.client.insert({ table: this.table, values: batch, format: 'JSONEachRow' });
  }
}
```
