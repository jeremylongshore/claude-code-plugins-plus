---
name: supabase-performance-tuning
description: |
  Optimize Supabase performance with indexes, connection pooling, query optimization,
  caching, and RLS policy performance.
  Use when experiencing slow queries, high latency, connection exhaustion,
  or needing to optimize Supabase for production traffic.
  Trigger with phrases like "supabase performance", "supabase slow",
  "supabase latency", "supabase caching", "optimize supabase", "supabase index".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, performance, optimization]

---
# Supabase Performance Tuning

## Overview
Optimize Supabase from database to client: PostgreSQL indexing, query optimization, connection pooling via Supavisor, RLS policy performance, and client-side caching strategies.

## Prerequisites
- Supabase project with production data
- `pg_stat_statements` extension enabled
- Access to Supabase Dashboard Performance Advisor

## Instructions

### Step 1: Identify Bottlenecks

```sql
-- Enable pg_stat_statements if not already
create extension if not exists pg_stat_statements;

-- Top 10 slowest queries by average execution time
select
  query,
  calls,
  mean_exec_time::numeric(10,2) as avg_ms,
  total_exec_time::numeric(10,2) as total_ms,
  rows
from pg_stat_statements
order by mean_exec_time desc
limit 10;

-- Top 10 most frequently called queries
select query, calls, mean_exec_time::numeric(10,2) as avg_ms
from pg_stat_statements
order by calls desc
limit 10;

-- Active connections and their state
select state, count(*), max(age(now(), state_change)) as max_age
from pg_stat_activity
where datname = current_database()
group by state;
```

### Step 2: Optimize Indexes

```sql
-- Find missing indexes on foreign keys
select
  tc.table_name,
  kcu.column_name as fk_column,
  'CREATE INDEX idx_' || tc.table_name || '_' || kcu.column_name
    || ' ON public.' || tc.table_name || '(' || kcu.column_name || ');' as fix
from information_schema.table_constraints tc
join information_schema.key_column_usage kcu
  on tc.constraint_name = kcu.constraint_name
left join pg_indexes i
  on i.tablename = tc.table_name
  and i.indexdef like '%' || kcu.column_name || '%'
where tc.constraint_type = 'FOREIGN KEY'
  and tc.table_schema = 'public'
  and i.indexname is null;

-- Find unused indexes (candidates for removal)
select schemaname, relname, indexrelname, idx_scan
from pg_stat_user_indexes
where idx_scan = 0
  and schemaname = 'public'
order by pg_relation_size(indexrelid) desc;

-- Analyze a specific query plan
explain (analyze, buffers, format text)
select * from todos
where user_id = '...' and is_complete = false
order by inserted_at desc
limit 20;

-- Create composite index for common filter + sort pattern
create index concurrently idx_todos_user_incomplete
  on public.todos (user_id, inserted_at desc)
  where is_complete = false;
```

### Step 3: Optimize RLS Policies

```sql
-- BAD: subquery in RLS runs for every row
create policy "slow_policy" on public.tasks for select
  using (
    project_id in (
      select p.id from projects p
      join members m on m.organization_id = p.organization_id
      where m.user_id = auth.uid()
    )
  );

-- GOOD: use a security definer function (cached per statement)
create or replace function public.user_project_ids()
returns setof uuid as $$
  select p.id from public.projects p
  join public.members m on m.organization_id = p.organization_id
  where m.user_id = auth.uid()
$$ language sql security definer stable;

create policy "fast_policy" on public.tasks for select
  using (project_id in (select public.user_project_ids()));

-- BETTER: use an EXISTS check (often faster than IN)
create policy "fastest_policy" on public.tasks for select
  using (
    exists (
      select 1 from public.members m
      join public.projects p on p.organization_id = m.organization_id
      where p.id = tasks.project_id
      and m.user_id = auth.uid()
    )
  );
```

### Step 4: Connection Pooling

```typescript
// Use the pooled connection string for serverless deployments
// Transaction mode (Supavisor) — recommended for serverless
const DATABASE_URL = 'postgres://postgres.[ref]:[pwd]@aws-0-[region].pooler.supabase.com:6543/postgres'

// For the JS SDK, connection pooling is automatic via the REST API
// No changes needed — PostgREST manages its own pool

// For direct Postgres connections (Prisma, Drizzle, etc.):
// Use the pooled connection string and set pool size low
const pool = new Pool({
  connectionString: DATABASE_URL,
  max: 5,  // keep low in serverless; Supavisor handles the rest
  idleTimeoutMillis: 10000,
})
```

### Step 5: Client-Side Query Optimization

```typescript
// BAD: fetching all columns
const { data } = await supabase.from('users').select('*')

// GOOD: only fetch needed columns
const { data } = await supabase.from('users').select('id, name, avatar_url')

// BAD: N+1 queries
for (const project of projects) {
  const { data: tasks } = await supabase
    .from('tasks')
    .select('*')
    .eq('project_id', project.id)
}

// GOOD: join in a single query
const { data } = await supabase
  .from('projects')
  .select(`
    id, name,
    tasks (id, title, status)
  `)
  .eq('organization_id', orgId)

// GOOD: use .in() for batch lookups
const { data } = await supabase
  .from('tasks')
  .select('id, title, project_id')
  .in('project_id', projectIds)
```

### Step 6: Caching Strategy

```typescript
// Simple in-memory cache with TTL
const cache = new Map<string, { data: any; expires: number }>()

async function cachedQuery<T>(
  key: string,
  queryFn: () => Promise<T>,
  ttlMs = 60_000
): Promise<T> {
  const cached = cache.get(key)
  if (cached && cached.expires > Date.now()) return cached.data as T

  const data = await queryFn()
  cache.set(key, { data, expires: Date.now() + ttlMs })
  return data
}

// Usage
const profile = await cachedQuery(
  `profile:${userId}`,
  async () => {
    const { data } = await supabase
      .from('profiles')
      .select('id, username, avatar_url')
      .eq('id', userId)
      .single()
    return data
  },
  30_000  // 30 second TTL
)
```

## Output
- Slow queries identified via `pg_stat_statements`
- Missing indexes created (especially on foreign keys)
- RLS policies optimized with security definer functions
- Connection pooling configured for deployment environment
- Client queries optimized (select specific columns, use joins)
- Caching layer for frequently accessed data

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `PGRST000: connection pool exhausted` | Too many concurrent connections | Use pooled connection string; reduce `max` pool size |
| Slow RLS policies | Subqueries on every row | Use `security definer` functions; add indexes on join columns |
| High P99 latency | Missing index | Run `explain analyze` and add appropriate index |
| Stale cache data | TTL too long | Reduce TTL or use Realtime to invalidate |

## Resources
- [Performance Advisor](https://supabase.com/docs/guides/database/inspect)
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [RLS Performance](https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv)
- [Query Optimization](https://supabase.com/docs/guides/database/postgres/indexes)

## Next Steps
For cost optimization, see `supabase-cost-tuning`.
