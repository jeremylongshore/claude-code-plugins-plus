# ClickHouse Rate Limits — Monitoring & Worked Examples

Concrete monitoring queries and end-to-end usage scenarios that build on the
patterns in [implementation.md](implementation.md).

## Monitor Concurrency

```sql
-- Currently running queries
SELECT user, count() AS running_queries, sum(memory_usage) AS total_memory
FROM system.processes
GROUP BY user;

-- Query queue depth (if queries are waiting)
SELECT metric, value FROM system.metrics
WHERE metric IN ('Query', 'MaxConcurrentQueries', 'TCPConnection', 'HTTPConnection');

-- Historical peak concurrency
SELECT
    toStartOfMinute(event_time) AS minute,
    max(ProfileEvents['ConcurrentQuery']) AS peak_concurrent
FROM system.query_log
WHERE event_time >= now() - INTERVAL 1 HOUR
GROUP BY minute
ORDER BY minute;
```

## Example 1: Cap a Reporting Service at 5 Concurrent Queries

A dashboard backend fans out many queries when a user loads a page. Wrap every
query in the `p-queue` limiter so the app never exceeds 5 in-flight queries,
regardless of how many dashboard tiles render at once.

```typescript
// Every tile calls this — the queue serializes beyond concurrency: 5
const rows = await rateLimitedQuery<{ ts: string; value: number }>(
  `SELECT toStartOfHour(event_time) AS ts, count() AS value
   FROM events WHERE event_time >= now() - INTERVAL 24 HOUR
   GROUP BY ts ORDER BY ts`,
);
```

Pair this with a server-side `max_concurrent_queries_for_user = 10` so a
misbehaving client still cannot starve other users.

## Example 2: Survive a Concurrency Spike with Retry + Backoff

During a traffic burst the server returns `TOO_MANY_SIMULTANEOUS_QUERIES`
(code 202). `queryWithRetry` retries with exponential backoff + jitter, so
transient spikes self-heal instead of surfacing as user-facing 500s.

```typescript
const result = await queryWithRetry<{ id: string }>(
  `SELECT id FROM orders WHERE status = 'pending' LIMIT 100`,
);
// Retries up to 3 times on 202 / TIMEOUT_EXCEEDED / NETWORK_ERROR,
// then rethrows so the caller can fail cleanly.
```

## Example 3: High-Throughput Ingest Without "Too Many Parts"

A firehose of events would create one part per insert and trip
`TOO_MANY_PARTS` (code 252). `InsertBuffer` batches rows and flushes every
10,000 rows or 5 seconds, turning thousands of tiny inserts into a few large
ones.

```typescript
const buffer = new InsertBuffer(client, 'events', 10_000, 5_000);
for await (const event of eventStream) {
  await buffer.add(event);   // auto-flushes on size or interval
}
await buffer.flush();        // drain the tail on shutdown
```

## Verify Your Limits Are Applied

After creating a quota and profile, confirm they bind to the user:

```sql
SHOW QUOTAS;
SHOW CREATE QUOTA app_quota;
SELECT * FROM system.quota_usage WHERE quota_name = 'app_quota';
```
