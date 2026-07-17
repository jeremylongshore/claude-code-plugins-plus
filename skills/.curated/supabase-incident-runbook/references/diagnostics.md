# Supabase Incident Diagnostics — Full Command Reference

This reference holds the complete diagnostic commands and code for each step of
the incident runbook. Follow the workflow in `SKILL.md`; drill in here for the
full copy-paste blocks.

## Step 1 — Triage: Platform vs. Application

### Check Supabase platform status

```bash
# Check official status page
curl -sf https://status.supabase.com/api/v2/status.json | jq '{
  indicator: .status.indicator,
  description: .status.description
}'
# Expected: { "indicator": "none", "description": "All Systems Operational" }

# Check for active incidents
curl -sf https://status.supabase.com/api/v2/incidents/unresolved.json | jq '.incidents[] | {
  name: .name,
  status: .status,
  impact: .impact,
  created_at: .created_at
}'
```

### Verify SDK client connectivity from your application

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Quick health check — select 1 from a small table
async function healthCheck(): Promise<{
  status: 'healthy' | 'degraded' | 'down';
  latencyMs: number;
  error?: string;
}> {
  const start = performance.now();
  try {
    const { data, error } = await supabase
      .from('_health_check')
      .select('id')
      .limit(1)
      .maybeSingle();

    const latencyMs = Math.round(performance.now() - start);

    if (error) {
      return { status: 'degraded', latencyMs, error: error.message };
    }

    return {
      status: latencyMs > 2000 ? 'degraded' : 'healthy',
      latencyMs,
    };
  } catch (err) {
    return {
      status: 'down',
      latencyMs: Math.round(performance.now() - start),
      error: err instanceof Error ? err.message : 'Unknown error',
    };
  }
}

// Create a minimal health check table (run once)
// CREATE TABLE _health_check (id int PRIMARY KEY DEFAULT 1);
// INSERT INTO _health_check VALUES (1);
// ALTER TABLE _health_check ENABLE ROW LEVEL SECURITY;
// CREATE POLICY "allow_anon_read" ON _health_check FOR SELECT USING (true);
```

### Decision tree

```
Is status.supabase.com showing an incident?
├─ YES → Supabase platform issue
│   ├─ Enable fallback/cache layer
│   ├─ Monitor status page for resolution
│   └─ Skip to Step 3 for connection pool protection
└─ NO → Application-level issue
    ├─ Does healthCheck() return 'healthy'?
    │   ├─ YES → Issue is in your queries/RLS/Edge Functions → Step 2
    │   └─ NO → Connection or auth issue → Step 2 + Step 3
    └─ Check error codes: 401=auth, 429=rate limit, 500=server error
```

## Step 2 — Database Diagnostics with pg_stat_activity

Connect directly to the database to inspect active connections, find stuck
queries, and detect connection leaks. These queries run via `psql` or the
Supabase SQL Editor.

### Connection pool status

```sql
-- Current connections grouped by state
SELECT state, count(*) AS connections,
       max(extract(epoch FROM age(now(), state_change)))::int AS max_idle_seconds
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state
ORDER BY connections DESC;

-- Expected healthy output:
-- state  | connections | max_idle_seconds
-- idle   | 3           | 12
-- active | 1           | 0
--        | 2           | (null)  ← background workers

-- WARNING: If idle > 20 or idle_in_transaction > 0, you have a leak
```

### Find long-running and stuck queries

```sql
-- Queries running longer than 10 seconds
SELECT pid, usename, state,
       age(now(), query_start)::text AS duration,
       wait_event_type, wait_event,
       left(query, 120) AS query_preview
FROM pg_stat_activity
WHERE state = 'active'
  AND query NOT LIKE '%pg_stat_activity%'
  AND age(now(), query_start) > interval '10 seconds'
ORDER BY query_start;

-- Idle-in-transaction connections (connection leak indicator)
SELECT pid, usename,
       age(now(), state_change)::text AS idle_duration,
       left(query, 100) AS last_query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
ORDER BY state_change;

-- Kill a specific stuck query (use with caution)
-- SELECT pg_cancel_backend(<pid>);       -- graceful cancel
-- SELECT pg_terminate_backend(<pid>);    -- force kill
```

### Check connection limits

```sql
-- Are we near the connection limit?
SELECT
  max_conn,
  used,
  max_conn - used AS available,
  round(100.0 * used / max_conn, 1) AS pct_used
FROM (SELECT count(*) AS used FROM pg_stat_activity) t,
     (SELECT setting::int AS max_conn FROM pg_settings WHERE name = 'max_connections') s;

-- If pct_used > 80%, you need connection pooling via Supavisor
-- Dashboard → Project Settings → Database → Connection Pooling
```

### Application-side connection monitoring

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

// Monitor connection health from the application
async function getConnectionStats() {
  const { data, error } = await supabase.rpc('get_connection_stats');
  if (error) throw error;
  return data;
}

// Create this function in your database:
// CREATE OR REPLACE FUNCTION get_connection_stats()
// RETURNS json AS $$
//   SELECT json_build_object(
//     'active', (SELECT count(*) FROM pg_stat_activity WHERE state = 'active'),
//     'idle', (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle'),
//     'idle_in_tx', (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction'),
//     'total', (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()),
//     'max', (SELECT setting::int FROM pg_settings WHERE name = 'max_connections')
//   );
// $$ LANGUAGE sql SECURITY DEFINER;
```

## Step 3 — RLS Debugging, Edge Functions, and Storage

### RLS policy debugging

```sql
-- List all RLS policies on a table
SELECT policyname, cmd, permissive,
       pg_get_expr(qual, polrelid) AS using_expression,
       pg_get_expr(with_check, polrelid) AS with_check_expression
FROM pg_policy
JOIN pg_class ON pg_class.oid = polrelid
WHERE relname = 'your_table_name';

-- Test as a specific user (simulates their JWT in SQL Editor)
SET request.jwt.claim.sub = 'target-user-uuid';
SET request.jwt.claim.role = 'authenticated';

-- Run the query that's failing
SELECT * FROM your_table_name WHERE user_id = 'target-user-uuid';
-- If empty but data exists → RLS is filtering incorrectly

-- Verify what auth.uid() resolves to
SELECT auth.uid();
SELECT auth.jwt();

-- Compare with service role (bypasses RLS)
-- Use service_role key in createClient to confirm data exists

-- Reset after testing
RESET request.jwt.claim.sub;
RESET request.jwt.claim.role;
```

### RLS debugging from the SDK

```typescript
import { createClient } from '@supabase/supabase-js';

// Anon client — respects RLS
const anonClient = createClient(url, anonKey);

// Service role client — bypasses RLS
const adminClient = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

async function debugRLS(table: string, userId: string) {
  // Query with RLS (what the user sees)
  const { data: rlsData, error: rlsError } = await anonClient
    .from(table)
    .select('*')
    .eq('user_id', userId);

  // Query without RLS (what actually exists)
  const { data: adminData, error: adminError } = await adminClient
    .from(table)
    .select('*')
    .eq('user_id', userId);

  console.log('With RLS:', rlsData?.length ?? 0, 'rows', rlsError?.message ?? 'OK');
  console.log('Without RLS:', adminData?.length ?? 0, 'rows', adminError?.message ?? 'OK');

  if ((adminData?.length ?? 0) > (rlsData?.length ?? 0)) {
    console.warn('RLS is filtering rows — check policies on', table);
  }
}
```

### Edge Function log inspection

```text
# View recent Edge Function logs
npx supabase functions logs my-function --project-ref <project-ref>

# Tail logs in real-time during debugging
npx supabase functions serve my-function --debug --env-file .env.local

# Check function deployment status
npx supabase functions list --project-ref <project-ref>

# Common Edge Function issues:
# - Cold starts > 1s: function needs warm-up or is too large
# - WORKER_LIMIT error: function exceeded memory/CPU
# - ImportError: missing dependency in import_map.json
```

### Edge Function health check from SDK

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, anonKey);

async function checkEdgeFunction(functionName: string) {
  const start = performance.now();
  const { data, error } = await supabase.functions.invoke(functionName, {
    body: { action: 'health-check' },
  });
  const duration = Math.round(performance.now() - start);

  console.log(`Edge Function "${functionName}":`, {
    status: error ? 'error' : 'ok',
    durationMs: duration,
    coldStart: duration > 1000,
    error: error?.message,
  });
}
```

### Storage bucket health

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

async function checkStorageHealth() {
  // List all buckets
  const { data: buckets, error: listError } = await supabase.storage.listBuckets();
  if (listError) {
    console.error('Cannot list buckets:', listError.message);
    return;
  }

  for (const bucket of buckets ?? []) {
    // Try listing files in each bucket
    const { data: files, error: filesError } = await supabase.storage
      .from(bucket.name)
      .list('', { limit: 1 });

    console.log(`Bucket "${bucket.name}":`, {
      public: bucket.public,
      accessible: !filesError,
      error: filesError?.message,
    });
  }

  // Test upload/download cycle
  const testFile = new Blob(['health-check'], { type: 'text/plain' });
  const testPath = `_health_check/${Date.now()}.txt`;

  const { error: uploadError } = await supabase.storage
    .from('test-bucket')
    .upload(testPath, testFile);

  if (!uploadError) {
    await supabase.storage.from('test-bucket').remove([testPath]);
    console.log('Storage upload/download: OK');
  } else {
    console.error('Storage upload failed:', uploadError.message);
  }
}
```
