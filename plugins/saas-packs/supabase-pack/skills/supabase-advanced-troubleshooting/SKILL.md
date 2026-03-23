---
name: supabase-advanced-troubleshooting
description: |
  Deep Supabase diagnostics: pg_stat_statements for slow queries, lock debugging with
  pg_locks, connection leak detection, RLS policy conflicts, Edge Function cold starts,
  and Realtime connection drop analysis.
  Use when standard troubleshooting fails, investigating performance regressions, debugging
  race conditions, or building evidence for Supabase support escalation.
  Trigger: "supabase deep debug", "supabase slow query", "supabase lock contention",
  "supabase connection leak", "supabase RLS conflict", "supabase cold start".
allowed-tools: Read, Grep, Bash(npx supabase:*), Bash(supabase:*), Bash(curl:*), Bash(psql:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, debugging, advanced, performance, troubleshooting]
---

# Supabase Advanced Troubleshooting

## Overview

When basic debugging does not reveal the root cause, you need deep PostgreSQL diagnostics: `pg_stat_statements` to find the slowest queries by cumulative execution time, `pg_locks` to detect lock contention and deadlocks, `pg_stat_activity` to find connection leaks, RLS policy conflict analysis to diagnose silent data filtering, Edge Function cold start profiling, and Realtime channel drop investigation. This skill covers every advanced diagnostic technique with real SQL queries and `createClient` from `@supabase/supabase-js`.

**When to use:** Slow query investigation, lock contention causing timeouts, connection pool exhaustion from leaks, RLS policies that silently filter or conflict, Edge Functions with unpredictable latency, or Realtime subscriptions that disconnect intermittently.

## Prerequisites

- Supabase project with `pg_stat_statements` extension enabled
- Direct database access via SQL Editor or `psql`
- `@supabase/supabase-js` v2+ installed in your project
- Supabase CLI for Edge Function logs
- Familiarity with PostgreSQL system catalogs

## Instructions

### Step 1: pg_stat_statements and Slow Query Analysis

Enable and query `pg_stat_statements` to find the most expensive queries by total execution time, calls, and rows processed.

**Enable the extension and query slow queries:**

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

**EXPLAIN ANALYZE for specific slow queries:**

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

**Monitor query performance from the SDK:**

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

### Step 2: Lock Debugging and Connection Leak Detection

Find blocked queries, detect lock contention, and identify connection leaks that exhaust the pool.

**Lock contention detection:**

```sql
-- Find blocked queries and what's blocking them
SELECT
  blocked.pid AS blocked_pid,
  blocked.usename AS blocked_user,
  age(now(), blocked.query_start)::text AS blocked_duration,
  left(blocked.query, 100) AS blocked_query,
  blocking.pid AS blocking_pid,
  blocking.usename AS blocking_user,
  left(blocking.query, 100) AS blocking_query,
  bl.mode AS lock_mode
FROM pg_stat_activity blocked
JOIN pg_locks bl ON bl.pid = blocked.pid AND NOT bl.granted
JOIN pg_locks kl ON kl.locktype = bl.locktype
  AND kl.database IS NOT DISTINCT FROM bl.database
  AND kl.relation IS NOT DISTINCT FROM bl.relation
  AND kl.page IS NOT DISTINCT FROM bl.page
  AND kl.tuple IS NOT DISTINCT FROM bl.tuple
  AND kl.pid != bl.pid
  AND kl.granted
JOIN pg_stat_activity blocking ON blocking.pid = kl.pid
WHERE blocked.state = 'active';

-- Check all locks on a specific table
SELECT
  l.locktype, l.mode, l.granted, l.pid,
  a.usename, a.state,
  age(now(), a.query_start)::text AS duration,
  left(a.query, 80) AS query
FROM pg_locks l
JOIN pg_stat_activity a ON a.pid = l.pid
WHERE l.relation = 'orders'::regclass
ORDER BY l.granted, a.query_start;

-- Detect potential deadlocks
SELECT
  l1.pid AS pid1, l2.pid AS pid2,
  l1.mode AS lock1, l2.mode AS lock2,
  l1.relation::regclass AS table1,
  l2.relation::regclass AS table2
FROM pg_locks l1
JOIN pg_locks l2 ON l1.pid != l2.pid
  AND l1.relation = l2.relation
  AND NOT l1.granted AND l2.granted
WHERE l1.locktype = 'relation';
```

**Connection leak detection:**

```sql
-- Connections that have been idle for too long (likely leaks)
SELECT
  pid, usename, client_addr, state,
  age(now(), state_change)::text AS idle_time,
  age(now(), backend_start)::text AS connection_age,
  left(query, 100) AS last_query
FROM pg_stat_activity
WHERE state = 'idle'
  AND age(now(), state_change) > interval '5 minutes'
  AND datname = current_database()
ORDER BY state_change;

-- Connections stuck in "idle in transaction" (the worst kind of leak)
SELECT
  pid, usename, client_addr,
  age(now(), xact_start)::text AS transaction_duration,
  age(now(), state_change)::text AS idle_in_tx_time,
  left(query, 100) AS last_query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
ORDER BY xact_start;

-- Connection usage by application/user
SELECT
  usename,
  client_addr,
  state,
  count(*) AS connections
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY usename, client_addr, state
ORDER BY connections DESC;

-- Kill leaked connections (batch)
-- SELECT pg_terminate_backend(pid)
-- FROM pg_stat_activity
-- WHERE state = 'idle in transaction'
--   AND age(now(), state_change) > interval '10 minutes';
```

**Connection pool monitoring from the SDK:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

// Monitor connection pool health
async function checkConnectionPool() {
  const { data, error } = await supabase.rpc('get_connection_health');
  if (error) {
    console.error('Connection health check failed:', error.message);
    return;
  }

  const health = data as {
    active: number;
    idle: number;
    idle_in_transaction: number;
    total: number;
    max_connections: number;
  };

  const utilization = (health.total / health.max_connections) * 100;

  console.log('Connection pool:', {
    ...health,
    utilization: `${utilization.toFixed(1)}%`,
  });

  if (health.idle_in_transaction > 0) {
    console.warn(`WARNING: ${health.idle_in_transaction} idle-in-transaction connections (likely leaks)`);
  }

  if (utilization > 80) {
    console.warn(`WARNING: Connection pool at ${utilization.toFixed(1)}% capacity`);
  }
}

// Database function for the RPC call:
// CREATE OR REPLACE FUNCTION get_connection_health()
// RETURNS json AS $$
//   SELECT json_build_object(
//     'active', (SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND datname = current_database()),
//     'idle', (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle' AND datname = current_database()),
//     'idle_in_transaction', (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction' AND datname = current_database()),
//     'total', (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()),
//     'max_connections', (SELECT setting::int FROM pg_settings WHERE name = 'max_connections')
//   );
// $$ LANGUAGE sql SECURITY DEFINER;
```

### Step 3: RLS Conflicts, Edge Function Cold Starts, and Realtime Drops

Diagnose RLS policy conflicts that cause unexpected access patterns, profile Edge Function cold starts, and investigate Realtime connection drops.

**RLS policy conflict analysis:**

```sql
-- List ALL policies on a table to find conflicts
SELECT
  pol.polname AS policy_name,
  CASE pol.polcmd
    WHEN 'r' THEN 'SELECT'
    WHEN 'a' THEN 'INSERT'
    WHEN 'w' THEN 'UPDATE'
    WHEN 'd' THEN 'DELETE'
    WHEN '*' THEN 'ALL'
  END AS command,
  CASE pol.polpermissive
    WHEN true THEN 'PERMISSIVE'
    ELSE 'RESTRICTIVE'
  END AS type,
  pg_get_expr(pol.polqual, pol.polrelid) AS using_clause,
  pg_get_expr(pol.polwithcheck, pol.polrelid) AS with_check_clause,
  ARRAY(SELECT rolname FROM pg_roles WHERE oid = ANY(pol.polroles)) AS applies_to_roles
FROM pg_policy pol
JOIN pg_class cls ON cls.oid = pol.polrelid
WHERE cls.relname = 'your_table_name'
ORDER BY pol.polcmd, pol.polpermissive DESC;

-- Common conflict: PERMISSIVE policies are OR'd together
-- If you have two SELECT policies, a row is visible if EITHER matches
-- RESTRICTIVE policies are AND'd — all must pass

-- Test a specific user's access
SET request.jwt.claim.sub = 'user-uuid';
SET request.jwt.claim.role = 'authenticated';
SET request.jwt.claims = '{"sub": "user-uuid", "role": "authenticated", "app_metadata": {"role": "editor", "org_id": "org-123"}}';

-- Check what they can see
SELECT count(*) FROM your_table_name;

-- Check the auth functions
SELECT auth.uid(), auth.jwt(), auth.role();

RESET ALL;
```

**RLS conflict debugging from the SDK:**

```typescript
import { createClient } from '@supabase/supabase-js';

// Compare results across permission levels
async function debugRLSConflict(table: string, filters: Record<string, string>) {
  const anonClient = createClient(url, anonKey);
  const authedClient = createClient(url, anonKey);
  const adminClient = createClient(url, serviceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  // Sign in as a test user
  await authedClient.auth.signInWithPassword({
    email: 'test@example.com',
    password: 'test-password',
  });

  let query = (client: any) => {
    let q = client.from(table).select('*', { count: 'exact' });
    for (const [key, value] of Object.entries(filters)) {
      q = q.eq(key, value);
    }
    return q;
  };

  const [anonResult, authedResult, adminResult] = await Promise.all([
    query(anonClient),
    query(authedClient),
    query(adminClient),
  ]);

  console.log(`RLS debug for "${table}":`, {
    anon: { count: anonResult.count, error: anonResult.error?.message },
    authenticated: { count: authedResult.count, error: authedResult.error?.message },
    admin: { count: adminResult.count, error: adminResult.error?.message },
  });

  if (adminResult.count !== authedResult.count) {
    console.warn(
      `RLS filtering: admin sees ${adminResult.count} rows, user sees ${authedResult.count}`
    );
  }
}
```

**Edge Function cold start profiling:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, anonKey);

// Measure cold start vs warm invocation times
async function profileEdgeFunction(
  functionName: string,
  iterations = 5,
  coldStartDelayMs = 60000
) {
  const results: { iteration: number; durationMs: number; isColdStart: boolean }[] = [];

  for (let i = 0; i < iterations; i++) {
    // Wait before first call to ensure cold start
    if (i === 0) {
      console.log(`Waiting ${coldStartDelayMs / 1000}s for cold start...`);
      await new Promise((r) => setTimeout(r, coldStartDelayMs));
    }

    const start = performance.now();
    const { data, error } = await supabase.functions.invoke(functionName, {
      body: { action: 'ping', timestamp: Date.now() },
    });
    const duration = Math.round(performance.now() - start);

    results.push({
      iteration: i + 1,
      durationMs: duration,
      isColdStart: i === 0 || duration > 1000,
    });

    console.log(`Invocation ${i + 1}: ${duration}ms ${i === 0 ? '(cold start)' : '(warm)'}`);
  }

  const coldStarts = results.filter((r) => r.isColdStart);
  const warmStarts = results.filter((r) => !r.isColdStart);

  console.log('Summary:', {
    coldStartAvgMs: coldStarts.length > 0
      ? Math.round(coldStarts.reduce((s, r) => s + r.durationMs, 0) / coldStarts.length)
      : 'N/A',
    warmStartAvgMs: warmStarts.length > 0
      ? Math.round(warmStarts.reduce((s, r) => s + r.durationMs, 0) / warmStarts.length)
      : 'N/A',
  });
}
```

```bash
# Check Edge Function logs for cold start indicators
npx supabase functions logs my-function --project-ref <ref> 2>&1 | head -50

# Look for patterns:
# - First invocation after deploy: high latency
# - "Worker booted" or "Isolate created" messages
# - Memory/CPU spikes on first request

# Reduce cold starts:
# 1. Minimize imports (lazy-load heavy dependencies)
# 2. Keep function payload small
# 3. Use scheduled warm-up pings via pg_cron
```

**Realtime connection drop investigation:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, anonKey);

// Debug Realtime connection stability
function monitorRealtimeChannel(table: string) {
  const channel = supabase
    .channel(`debug-${table}`)
    .on('system', {}, (payload) => {
      console.log(`[SYSTEM] ${new Date().toISOString()}:`, payload);
      // Watch for: CHANNEL_ERROR, TIMED_OUT, TOKEN_EXPIRED
    })
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table },
      (payload) => {
        console.log(`[CHANGE] ${payload.eventType}:`, payload.new);
      }
    )
    .subscribe((status, err) => {
      console.log(`[STATUS] ${new Date().toISOString()}: ${status}`, err ?? '');

      if (status === 'CHANNEL_ERROR') {
        console.error('Channel error — will auto-reconnect');
      }
      if (status === 'TIMED_OUT') {
        console.error('Connection timed out — check network/firewall');
      }
    });

  // Monitor connection health periodically
  const healthInterval = setInterval(() => {
    const state = channel.state;
    console.log(`[HEALTH] Channel state: ${state}`);
    if (state !== 'joined') {
      console.warn(`[HEALTH] Channel not joined, current state: ${state}`);
    }
  }, 30000);

  return {
    channel,
    stop: () => {
      clearInterval(healthInterval);
      channel.unsubscribe();
    },
  };
}
```

```sql
-- Verify table is in the Realtime publication
SELECT schemaname, tablename
FROM pg_publication_tables
WHERE pubname = 'supabase_realtime'
ORDER BY tablename;

-- Add a missing table to the publication
ALTER PUBLICATION supabase_realtime ADD TABLE public.your_table;

-- Check Realtime connection limits
-- Supabase free plan: 200 concurrent connections
-- Pro plan: 500 concurrent connections
-- You can check current count in the Supabase dashboard → Realtime → Connections
```

## Output

After completing this skill, you will have:

- **Slow query identification** — `pg_stat_statements` queries ranking by total time, frequency, and cache hit ratio
- **EXPLAIN ANALYZE proficiency** — reading execution plans and creating targeted indexes
- **Lock contention diagnosis** — blocked/blocking query pairs with lock modes
- **Connection leak detection** — idle and idle-in-transaction connections with kill commands
- **Connection pool monitoring** — SDK-based health check RPC with utilization alerts
- **RLS conflict analysis** — policy listing with permissive/restrictive classification and multi-level comparison
- **Edge Function profiling** — cold start vs warm invocation measurement
- **Realtime debugging** — channel state monitoring with system event logging

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `pg_stat_statements` not available | Extension not enabled | Run `CREATE EXTENSION pg_stat_statements;` |
| Seq Scan on large table | Missing index on filter column | Create index with `CREATE INDEX CONCURRENTLY` |
| `deadlock detected` | Circular lock dependency | Ensure consistent lock ordering across transactions |
| All connections in `idle in transaction` | Application not closing transactions | Add connection timeout; review ORM connection pool settings |
| RLS returns empty for authenticated user | JWT claims don't match policy | Check `auth.jwt()` output; verify `app_metadata` is set |
| Edge Function > 2s cold start | Large dependency bundle | Lazy-import heavy modules; reduce function size |
| Realtime `TIMED_OUT` | Network/firewall blocking WebSocket | Check port 443 is open; verify no proxy strips `Upgrade` header |
| `CHANNEL_ERROR` on subscribe | Table not in Realtime publication | Run `ALTER PUBLICATION supabase_realtime ADD TABLE ...` |

## Examples

**Example 1 — Quick performance audit:**

```sql
-- Run this query to get a snapshot of database health
SELECT
  'Connections' AS metric,
  count(*)::text AS value
FROM pg_stat_activity WHERE datname = current_database()
UNION ALL
SELECT 'Cache hit ratio',
  round(100.0 * sum(heap_blks_hit) / nullif(sum(heap_blks_hit + heap_blks_read), 0), 2)::text || '%'
FROM pg_statio_user_tables
UNION ALL
SELECT 'Table bloat (dead tuples)',
  sum(n_dead_tup)::text
FROM pg_stat_user_tables
UNION ALL
SELECT 'Longest running query',
  coalesce(max(age(now(), query_start))::text, 'none')
FROM pg_stat_activity WHERE state = 'active' AND query NOT LIKE '%pg_stat%';
```

**Example 2 — Build a diagnostic bundle for support:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

async function buildDiagnosticBundle() {
  const bundle: Record<string, any> = {
    timestamp: new Date().toISOString(),
    projectRef: process.env.SUPABASE_PROJECT_REF,
  };

  // Connection stats
  const { data: connHealth } = await supabase.rpc('get_connection_health');
  bundle.connections = connHealth;

  // Table sizes
  const { data: tableSizes } = await supabase.rpc('get_table_sizes');
  bundle.tableSizes = tableSizes;

  // Recent errors from application logs
  const { data: recentErrors } = await supabase
    .from('error_logs')
    .select('message, count, last_seen')
    .order('last_seen', { ascending: false })
    .limit(10);
  bundle.recentErrors = recentErrors;

  console.log(JSON.stringify(bundle, null, 2));
  // Submit with your support ticket at https://supabase.com/dashboard/support
}
```

**Example 3 — Automated slow query alert:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

async function checkSlowQueries(thresholdMs = 1000) {
  const { data: slowQueries } = await supabase.rpc('get_slow_queries', {
    threshold_ms: thresholdMs,
  });

  if (slowQueries && slowQueries.length > 0) {
    console.warn(`Found ${slowQueries.length} queries averaging > ${thresholdMs}ms`);
    for (const q of slowQueries) {
      console.warn(`  [${q.avg_ms}ms avg, ${q.calls} calls] ${q.query_preview}`);
    }
  }
}

// Database function:
// CREATE OR REPLACE FUNCTION get_slow_queries(threshold_ms numeric DEFAULT 1000)
// RETURNS TABLE(queryid bigint, avg_ms numeric, calls bigint, query_preview text) AS $$
//   SELECT queryid, round(mean_exec_time::numeric, 2), calls, left(query, 150)
//   FROM pg_stat_statements
//   WHERE mean_exec_time > threshold_ms AND calls > 10
//   ORDER BY mean_exec_time DESC LIMIT 10;
// $$ LANGUAGE sql SECURITY DEFINER;
```

## Resources

- [pg_stat_statements — PostgreSQL Docs](https://www.postgresql.org/docs/current/pgstatstatements.html)
- [EXPLAIN ANALYZE — PostgreSQL Docs](https://www.postgresql.org/docs/current/sql-explain.html)
- [Supabase Performance Advisor](https://supabase.com/docs/guides/database/inspect)
- [RLS Debugging — Supabase Docs](https://supabase.com/docs/guides/troubleshooting/rls-simplified-BJTcS8)
- [Edge Functions Logging — Supabase Docs](https://supabase.com/docs/guides/functions/logging)
- [Realtime Debugging — Supabase Docs](https://supabase.com/docs/guides/realtime/debugging)
- [pg_locks — PostgreSQL Docs](https://www.postgresql.org/docs/current/view-pg-locks.html)
- [Connection Pooling with Supavisor](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)

## Next Steps

- For load testing and scaling patterns, see `supabase-load-scale`
- For incident response procedures, see `supabase-incident-runbook`
- For performance tuning and index optimization, see `supabase-performance-tuning`
- For common error patterns and quick fixes, see `supabase-common-errors`
