# Slow Query Analysis — pg_stat_statements, EXPLAIN, and SDK timing

Enable and query `pg_stat_statements` to find the most expensive queries by total execution time, calls, and rows processed.

## Enable the extension and query slow queries

```sql
-- Enable pg_stat_statements (run once)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top 10 slowest queries by total execution time
SELECT
  queryid,
  calls,
  round(total_exec_time::numeric, 2) AS total_ms,
  round(mean_exec_time::numeric, 2) AS avg_ms,
  round(max_exec_time::numeric, 2) AS max_ms,
  rows AS total_rows,
  round(100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0), 2) AS cache_hit_pct,
  left(query, 150) AS query_preview
FROM pg_stat_statements
WHERE userid = (SELECT usesysid FROM pg_user WHERE usename = current_user)
ORDER BY total_exec_time DESC
LIMIT 10;

-- Top queries by frequency (most called)
SELECT
  queryid,
  calls,
  round(mean_exec_time::numeric, 2) AS avg_ms,
  rows / nullif(calls, 0) AS rows_per_call,
  left(query, 150) AS query_preview
FROM pg_stat_statements
WHERE calls > 100
ORDER BY calls DESC
LIMIT 10;

-- Queries with poor cache hit ratio (reading from disk)
SELECT
  queryid,
  calls,
  shared_blks_hit,
  shared_blks_read,
  round(100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0), 2) AS cache_hit_pct,
  left(query, 150) AS query_preview
FROM pg_stat_statements
WHERE shared_blks_read > 100
ORDER BY shared_blks_read DESC
LIMIT 10;

-- Reset statistics after optimization (to measure improvement)
-- SELECT pg_stat_statements_reset();
```

## EXPLAIN ANALYZE for specific slow queries

```sql
-- Run EXPLAIN ANALYZE on the suspicious query
EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT TEXT)
SELECT p.*, count(o.id) AS order_count
FROM profiles p
LEFT JOIN orders o ON o.user_id = p.id
WHERE p.created_at > now() - interval '30 days'
GROUP BY p.id
ORDER BY order_count DESC
LIMIT 50;

-- What to look for in the output:
-- 1. Seq Scan on large table → needs an index
-- 2. Nested Loop with high actual rows → consider Hash Join
-- 3. Sort with "Sort Method: external merge" → increase work_mem or add index
-- 4. Buffers read >> shared hit → data not cached, optimize query or increase shared_buffers

-- Create a targeted index based on EXPLAIN output
CREATE INDEX CONCURRENTLY idx_profiles_created_at
  ON profiles(created_at DESC);

CREATE INDEX CONCURRENTLY idx_orders_user_id
  ON orders(user_id);
```

## Monitor query performance from the SDK

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

// Wrapper that measures and logs query performance
async function timedQuery<T>(
  label: string,
  queryFn: () => Promise<{ data: T | null; error: any }>
): Promise<T | null> {
  const start = performance.now();
  const { data, error } = await queryFn();
  const duration = Math.round(performance.now() - start);

  if (duration > 500) {
    console.warn(`[SLOW QUERY] ${label}: ${duration}ms`);
  }

  if (error) {
    console.error(`[QUERY ERROR] ${label}:`, error.message);
    return null;
  }

  return data;
}

// Usage
const profiles = await timedQuery('recent-profiles', () =>
  supabase
    .from('profiles')
    .select('*, orders(count)')
    .gte('created_at', new Date(Date.now() - 30 * 86400000).toISOString())
    .order('created_at', { ascending: false })
    .limit(50)
);
```
