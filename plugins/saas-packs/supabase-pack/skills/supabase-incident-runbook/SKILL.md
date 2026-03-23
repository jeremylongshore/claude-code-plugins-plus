---
name: supabase-incident-runbook
description: |
  Execute Supabase incident response: dashboard health checks, connection pool status,
  pg_stat_activity queries, RLS debugging, Edge Function logs, storage health, and escalation.
  Use when responding to Supabase outages, investigating production errors, debugging
  connection issues, or preparing evidence for Supabase support escalation.
  Trigger: "supabase incident", "supabase outage", "supabase down", "supabase on-call",
  "supabase emergency", "supabase broken", "supabase connection issues".
allowed-tools: Read, Grep, Bash(npx supabase:*), Bash(supabase:*), Bash(curl:*), Bash(psql:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, incident-response, debugging, operations, runbook]
---

# Supabase Incident Runbook

## Overview

When a Supabase-backed application experiences failures, you need a structured response: verify the Supabase platform status, check your connection pool, inspect `pg_stat_activity` for stuck queries, debug RLS policies that silently filter data, review Edge Function execution logs, verify storage bucket health, and escalate to Supabase support with a complete evidence bundle. This runbook covers every layer from the SDK client through the database to platform services.

**When to use:** Production errors involving Supabase, degraded API response times, connection pool exhaustion, silent data filtering from RLS, Edge Function cold start failures, or storage upload/download errors.

## Prerequisites

- Supabase project with dashboard access at [supabase.com/dashboard](https://supabase.com/dashboard)
- `@supabase/supabase-js` v2+ installed in your project
- Supabase CLI installed for Edge Function log access
- Direct database connection string (for `psql` diagnostics)
- Access to [status.supabase.com](https://status.supabase.com) for platform health

## Instructions

### Step 1: Triage — Platform vs. Application

Determine whether the issue is a Supabase platform incident or an application-level bug. Check platform status first, then verify your SDK client connectivity.

**Check Supabase platform status:**

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

**Verify SDK client connectivity from your application:**

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

**Decision tree:**

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

### Step 2: Database Diagnostics with pg_stat_activity

Connect directly to the database to inspect active connections, find stuck queries, and detect connection leaks. These queries run via `psql` or the Supabase SQL Editor.

**Connection pool status:**

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

**Find long-running and stuck queries:**

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

**Check connection limits:**

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

**Application-side connection monitoring:**

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

### Step 3: RLS Debugging, Edge Functions, and Storage

Debug silent data filtering from Row Level Security policies, inspect Edge Function execution, and verify storage bucket health.

**RLS policy debugging:**

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

**RLS debugging from the SDK:**

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

**Edge Function log inspection:**

```bash
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

**Edge Function health check from SDK:**

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

**Storage bucket health:**

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

## Output

After running this incident runbook, you will have:

- **Platform status assessment** — confirmed whether the issue is Supabase-side or application-side
- **SDK health check** — latency measurement and connectivity verification via `createClient`
- **Connection pool analysis** — `pg_stat_activity` showing active, idle, and leaked connections
- **Long-running query identification** — stuck queries with PIDs ready for cancellation
- **RLS policy diagnosis** — side-by-side comparison of anon vs. service role query results
- **Edge Function status** — deployment status, cold start detection, and log inspection
- **Storage health report** — bucket accessibility and upload/download verification
- **Evidence bundle** — complete diagnostic data for Supabase support escalation

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `FetchError: request failed` | Supabase API unreachable | Check status.supabase.com; verify network/DNS |
| `connection refused` on port 5432 | Direct DB access blocked or wrong credentials | Use pooler URL (port 6543) or check dashboard connection strings |
| `too many clients already` | Connection pool exhausted | Kill idle-in-transaction connections; enable Supavisor pooling |
| `permission denied for table` | RLS blocking or wrong role | Check policies with `pg_policy`; verify JWT claims |
| `WORKER_LIMIT` in Edge Function | Memory/CPU exceeded | Reduce function payload size; optimize imports |
| `JWT expired` | Token not refreshing | Verify `autoRefreshToken: true` in `createClient` options |
| `storage/object-not-found` | File deleted or wrong path | Check bucket policies; verify path with service role client |
| `rate limit exceeded` (429) | Too many API requests | Implement exponential backoff; contact Supabase for limit increase |

## Examples

**Example 1 — Quick triage script:**

```typescript
import { createClient } from '@supabase/supabase-js';

async function triageSupabase() {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );

  // 1. Database connectivity
  const { error: dbError } = await supabase.from('_health_check').select('id').limit(1);
  console.log('Database:', dbError ? `ERROR: ${dbError.message}` : 'OK');

  // 2. Auth service
  const { data: authData, error: authError } = await supabase.auth.getSession();
  console.log('Auth service:', authError ? `ERROR: ${authError.message}` : 'OK');

  // 3. Storage service
  const { error: storageError } = await supabase.storage.listBuckets();
  console.log('Storage:', storageError ? `ERROR: ${storageError.message}` : 'OK');

  // 4. Realtime service
  const channel = supabase.channel('health');
  channel.subscribe((status) => {
    console.log('Realtime:', status);
    channel.unsubscribe();
  });
}
```

**Example 2 — Connection leak detector:**

```sql
-- Run this during an incident to find leaked connections
WITH connection_summary AS (
  SELECT usename, state,
         count(*) AS conn_count,
         max(age(now(), state_change)) AS max_age
  FROM pg_stat_activity
  WHERE datname = current_database()
  GROUP BY usename, state
)
SELECT usename, state, conn_count,
       max_age::text AS max_idle_time,
       CASE
         WHEN state = 'idle in transaction' THEN 'LEAK - kill these'
         WHEN state = 'idle' AND max_age > interval '10 minutes' THEN 'STALE - review'
         ELSE 'OK'
       END AS assessment
FROM connection_summary
ORDER BY conn_count DESC;
```

**Example 3 — Escalation evidence bundle:**

```typescript
import { createClient } from '@supabase/supabase-js';

async function buildEvidenceBundle() {
  const supabase = createClient(url, serviceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  const evidence = {
    timestamp: new Date().toISOString(),
    projectRef: process.env.SUPABASE_PROJECT_REF,
    symptoms: [],
    diagnostics: {},
  };

  // Collect connection stats
  const { data: connStats } = await supabase.rpc('get_connection_stats');
  evidence.diagnostics['connections'] = connStats;

  // Collect recent errors from your error tracking
  evidence.symptoms.push('Describe the user-facing symptoms here');

  // Include request IDs from failed API calls
  // The x-request-id header from Supabase responses identifies specific requests

  console.log('Evidence bundle for Supabase support:');
  console.log(JSON.stringify(evidence, null, 2));
  // Submit at: https://supabase.com/dashboard/support
}
```

## Resources

- [Supabase Status Page](https://status.supabase.com)
- [Supabase Support Portal](https://supabase.com/dashboard/support)
- [Database Health — Supabase Docs](https://supabase.com/docs/guides/database/inspect)
- [RLS Debugging — Supabase Docs](https://supabase.com/docs/guides/troubleshooting/rls-simplified-BJTcS8)
- [Edge Functions Logs — Supabase Docs](https://supabase.com/docs/guides/functions/logging)
- [Connection Pooling with Supavisor](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [pg_stat_activity — PostgreSQL Docs](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW)

## Next Steps

- For GDPR compliance and data handling, see `supabase-data-handling`
- For performance tuning and query optimization, see `supabase-performance-tuning`
- For observability and monitoring setup, see `supabase-observability`
- For common error patterns and fixes, see `supabase-common-errors`
