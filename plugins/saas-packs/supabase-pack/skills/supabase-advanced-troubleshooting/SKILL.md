---
name: supabase-advanced-troubleshooting
description: |
  Apply advanced Supabase debugging: query plan analysis, RLS policy debugging,
  connection leak detection, lock contention, and support escalation with evidence.
  Use when standard troubleshooting fails, investigating race conditions,
  or preparing evidence for Supabase support.
  Trigger with phrases like "supabase hard bug", "supabase mystery error",
  "supabase deep debug", "supabase explain analyze", "supabase support escalation".
allowed-tools: Read, Grep, Bash(supabase:*), Bash(curl:*), Bash(psql:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, debugging, advanced]

---
# Supabase Advanced Troubleshooting

## Overview
Advanced debugging techniques for hard-to-diagnose Supabase issues: query plan analysis with EXPLAIN ANALYZE, RLS policy debugging, connection pool inspection, lock contention detection, and building evidence bundles for Supabase support.

## Prerequisites
- Access to Supabase SQL Editor or psql
- `pg_stat_statements` enabled
- Familiarity with PostgreSQL internals

## Instructions

### Technique 1: EXPLAIN ANALYZE for Slow Queries

```sql
-- Run EXPLAIN ANALYZE to see actual execution plan
explain (analyze, buffers, timing, format text)
select t.*, p.name as project_name
from tasks t
join projects p on p.id = t.project_id
where t.assigned_to = 'user-uuid-here'
  and t.status = 'in_progress'
order by t.due_date asc
limit 20;

-- Look for:
-- - Seq Scan (missing index — add one on the filtered column)
-- - Nested Loop with high row estimates (consider a Hash Join hint)
-- - Sort with high memory usage (add index matching the ORDER BY)
-- - Buffers read >> shared hit (data not in cache — increase shared_buffers or optimize query)

-- Fix: add a composite index for this query pattern
create index concurrently idx_tasks_assigned_status
  on tasks (assigned_to, status, due_date)
  where status != 'cancelled';
```

### Technique 2: Debug RLS Policies Step by Step

```sql
-- Step 1: Test as a specific user (simulates their JWT)
set request.jwt.claim.sub = 'target-user-uuid';
set request.jwt.claim.role = 'authenticated';

-- Step 2: Run the failing query
select * from todos where user_id = 'target-user-uuid';
-- If empty: RLS is filtering. If returns rows: RLS is fine, issue is elsewhere.

-- Step 3: Check which policies exist
select policyname, cmd, permissive, qual, with_check
from pg_policies
where tablename = 'todos';

-- Step 4: Test each policy condition individually
select auth.uid();  -- verify this returns the expected user ID
select auth.jwt();  -- check the full JWT claims

-- Step 5: Compare with service role (bypasses RLS)
-- Use the admin client in application code to verify data exists

-- Reset after testing
reset request.jwt.claim.sub;
reset request.jwt.claim.role;
```

### Technique 3: Connection Pool Analysis

```sql
-- Current connections by state
select state, count(*), max(age(now(), state_change))::text as max_wait
from pg_stat_activity
where datname = current_database()
group by state;

-- Identify connection leaks (idle connections held too long)
select pid, usename, state, age(now(), state_change) as idle_time,
       query_start, left(query, 80) as last_query
from pg_stat_activity
where state = 'idle'
  and age(now(), state_change) > interval '5 minutes'
order by state_change;

-- Find queries holding connections open
select pid, usename, state, wait_event_type, wait_event,
       age(now(), query_start) as query_duration,
       left(query, 100) as query
from pg_stat_activity
where state = 'active'
  and age(now(), query_start) > interval '10 seconds'
order by query_start;

-- Kill a specific stuck connection (use with caution)
-- select pg_terminate_backend(<pid>);
```

### Technique 4: Lock Contention Detection

```sql
-- Find blocked queries
select
  blocked.pid as blocked_pid,
  age(now(), blocked.query_start) as blocked_duration,
  left(blocked.query, 80) as blocked_query,
  blocking.pid as blocking_pid,
  left(blocking.query, 80) as blocking_query
from pg_stat_activity blocked
join pg_locks bl on bl.pid = blocked.pid and not bl.granted
join pg_locks kl on kl.locktype = bl.locktype
  and kl.database is not distinct from bl.database
  and kl.relation is not distinct from bl.relation
  and kl.page is not distinct from bl.page
  and kl.tuple is not distinct from bl.tuple
  and kl.pid != bl.pid
  and kl.granted
join pg_stat_activity blocking on blocking.pid = kl.pid
where blocked.state = 'active';

-- Check lock types on a specific table
select locktype, mode, granted, pid
from pg_locks
where relation = 'todos'::regclass;
```

### Technique 5: Realtime Debugging

```typescript
// Debug Realtime subscription issues
const channel = supabase.channel('debug-channel', {
  config: { broadcast: { self: true } },
})

channel
  .on('system', {}, (payload) => {
    console.log('[SYSTEM]', payload)
    // Look for: SUBSCRIBED, CHANNEL_ERROR, TIMED_OUT
  })
  .on('postgres_changes', { event: '*', schema: 'public', table: 'todos' }, (payload) => {
    console.log('[CHANGE]', payload.eventType, payload.new)
  })
  .subscribe((status, err) => {
    console.log('[STATUS]', status, err ?? '')
  })

// Check if Realtime is enabled on the table
// SQL: select * from pg_publication_tables where pubname = 'supabase_realtime';
```

```sql
-- Verify table is in the Realtime publication
select * from pg_publication_tables
where pubname = 'supabase_realtime';

-- Add table to Realtime publication if missing
alter publication supabase_realtime add table public.todos;
```

### Technique 6: Edge Function Debugging

```bash
# Check Edge Function logs
supabase functions logs process-order --linked

# Test locally with verbose output
supabase functions serve process-order --debug --env-file .env.local

# Check function status
supabase functions list --linked
```

### Technique 7: Build Support Evidence Bundle

```sql
-- Collect evidence for Supabase support ticket
-- Save each output to a file

-- 1. Postgres version and settings
select version();
show shared_buffers;
show max_connections;
show statement_timeout;

-- 2. Table and index sizes
select relname, pg_size_pretty(pg_total_relation_size(relid)) as size
from pg_stat_user_tables order by pg_total_relation_size(relid) desc limit 20;

-- 3. Slow query stats
select query, calls, mean_exec_time::numeric(10,2) as avg_ms
from pg_stat_statements order by mean_exec_time desc limit 10;

-- 4. RLS policies
select tablename, policyname, cmd, qual from pg_policies where schemaname = 'public';

-- 5. Extensions
select extname, extversion from pg_extension order by extname;
```

## Output
- Query plans analyzed with specific index recommendations
- RLS policies debugged by simulating specific user JWTs
- Connection leaks and idle connections identified
- Lock contention detected with blocking query identification
- Realtime publication membership verified
- Support evidence bundle collected with all diagnostic data

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Seq Scan on large table | Missing index | Add index on filter/join columns |
| All connections in `idle` state | Connection leak | Review connection pool settings; add idle timeout |
| Lock contention causing timeouts | Long-running transaction | Kill blocking query or optimize transaction scope |
| Realtime events not arriving | Table not in publication | `ALTER PUBLICATION supabase_realtime ADD TABLE ...` |

## Resources
- [PostgreSQL EXPLAIN Documentation](https://www.postgresql.org/docs/current/sql-explain.html)
- [Supabase Performance Advisor](https://supabase.com/docs/guides/database/inspect)
- [RLS Debugging](https://supabase.com/docs/guides/troubleshooting/rls-simplified-BJTcS8)
- [Supabase Support](https://supabase.com/support)

## Next Steps
For load testing and scaling, see `supabase-load-scale`.
