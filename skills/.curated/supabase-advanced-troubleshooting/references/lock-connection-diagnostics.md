# Lock Debugging and Connection Leak Detection

Find blocked queries, detect lock contention, and identify connection leaks that exhaust the pool.

## Lock contention detection

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

## Connection leak detection

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

## Connection pool monitoring from the SDK

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
