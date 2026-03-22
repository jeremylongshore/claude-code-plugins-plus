---
name: supabase-cost-tuning
description: |
  Optimize Supabase costs through plan selection, usage monitoring, storage cleanup,
  and Edge Function optimization.
  Use when analyzing Supabase billing, reducing costs,
  or implementing usage tracking and budget alerts.
  Trigger with phrases like "supabase cost", "supabase billing",
  "reduce supabase costs", "supabase pricing", "supabase expensive", "supabase budget".
allowed-tools: Read, Write, Edit, Grep, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, cost-optimization]

---
# Supabase Cost Tuning

## Overview
Understand Supabase pricing, identify cost drivers, and implement optimizations across database, storage, bandwidth, and Edge Functions to stay within budget.

## Prerequisites
- Access to Supabase Dashboard billing page
- Understanding of current usage patterns

## Instructions

### Supabase Pricing Breakdown

| Resource | Free Tier | Pro ($25/mo) | Team ($599/mo) |
|----------|-----------|-------------|----------------|
| Database | 500 MB | 8 GB included, $0.125/GB | 8 GB included |
| Storage | 1 GB | 100 GB included, $0.021/GB | 100 GB included |
| Bandwidth | 5 GB | 250 GB included, $0.09/GB | 250 GB included |
| Edge Functions | 500K invocations | 2M invocations, $2/M | 2M invocations |
| Realtime | 200 concurrent | 500 concurrent | 500 concurrent |
| Auth MAU | 50,000 | 100,000 | 100,000 |

### Step 1: Audit Current Usage

```sql
-- Database size by table
select
  relname as table_name,
  pg_size_pretty(pg_total_relation_size(relid)) as total_size,
  pg_size_pretty(pg_relation_size(relid)) as table_size,
  pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size,
  n_live_tup as rows
from pg_stat_user_tables
order by pg_total_relation_size(relid) desc;

-- Total database size
select pg_size_pretty(pg_database_size(current_database())) as total_db_size;

-- Find large unused indexes
select
  indexrelname,
  pg_size_pretty(pg_relation_size(indexrelid)) as size,
  idx_scan as scans_since_reset
from pg_stat_user_indexes
where idx_scan = 0
order by pg_relation_size(indexrelid) desc
limit 10;
```

### Step 2: Reduce Database Size

```sql
-- Remove old soft-deleted records
delete from public.orders
where status = 'deleted' and updated_at < now() - interval '90 days';

-- Archive old data to a separate table
create table public.orders_archive (like public.orders including all);

insert into public.orders_archive
select * from public.orders
where created_at < now() - interval '1 year';

delete from public.orders
where created_at < now() - interval '1 year';

-- Vacuum to reclaim space (runs automatically, but can trigger manually)
vacuum (verbose, analyze) public.orders;

-- Drop unused indexes to save space
drop index if exists idx_never_used;
```

### Step 3: Optimize Storage Costs

```typescript
// List storage usage per bucket
const { data: buckets } = await supabaseAdmin.storage.listBuckets()

for (const bucket of buckets ?? []) {
  const { data: files } = await supabaseAdmin.storage
    .from(bucket.name)
    .list('', { limit: 1000 })

  const totalSize = files?.reduce((sum, f) => sum + (f.metadata?.size || 0), 0) ?? 0
  console.log(`${bucket.name}: ${(totalSize / 1024 / 1024).toFixed(1)} MB`)
}

// Clean up orphaned files (uploaded but never associated with a record)
const { data: orphans } = await supabaseAdmin
  .from('storage.objects')
  .select('name, created_at')
  .eq('bucket_id', 'uploads')
  .lt('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString())

// Delete orphaned files
if (orphans?.length) {
  await supabaseAdmin.storage
    .from('uploads')
    .remove(orphans.map(o => o.name))
}
```

### Step 4: Reduce Bandwidth

```typescript
// Select only needed columns (reduces response size)
// BAD: transfers entire row
const { data } = await supabase.from('products').select('*')

// GOOD: transfers only needed fields
const { data } = await supabase.from('products').select('id, name, price')

// Use count queries instead of fetching data you don't display
const { count } = await supabase
  .from('orders')
  .select('*', { count: 'exact', head: true })  // head: true = no data transferred

// Paginate large result sets
const { data } = await supabase
  .from('logs')
  .select('id, message, created_at')
  .order('created_at', { ascending: false })
  .range(0, 49)  // 50 rows per page
```

### Step 5: Optimize Edge Functions

```typescript
// Minimize cold starts by keeping functions lightweight
// BAD: importing heavy libraries at the top level
import { parse } from 'some-huge-csv-library'

// GOOD: dynamic import only when needed
serve(async (req) => {
  if (needsCsvParsing) {
    const { parse } = await import('some-huge-csv-library')
  }
})

// Cache expensive computations across invocations
// Edge Functions reuse the same isolate for ~60 seconds
const _cache: Map<string, { data: any; ts: number }> = new Map()

function cached<T>(key: string, ttl: number, fn: () => T): T {
  const entry = _cache.get(key)
  if (entry && Date.now() - entry.ts < ttl) return entry.data
  const data = fn()
  _cache.set(key, { data, ts: Date.now() })
  return data
}
```

### Step 6: Usage Monitoring

```typescript
// Track API usage with a lightweight counter table
// supabase/migrations/<ts>_create_usage_tracking.sql
```

```sql
create table public.api_usage (
  id bigint generated always as identity primary key,
  endpoint text not null,
  method text not null,
  user_id uuid references auth.users(id),
  created_at timestamptz default now()
);

-- Create a summary view for daily usage
create materialized view public.daily_usage as
select
  date_trunc('day', created_at) as day,
  endpoint,
  count(*) as requests
from public.api_usage
group by 1, 2;

-- Refresh daily via a cron job (pg_cron extension)
select cron.schedule('refresh-usage', '0 1 * * *',
  'refresh materialized view public.daily_usage;'
);
```

## Output
- Database size audit with table-level breakdown
- Unused indexes identified and removed
- Storage cleanup for orphaned files
- Bandwidth reduced through column selection and pagination
- Edge Function cold starts minimized
- Usage monitoring table and daily summary view

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected bandwidth spike | `select *` on large tables | Use specific column lists |
| Storage costs growing | Orphaned uploads | Implement cleanup job |
| Database approaching limit | Data growth without archival | Archive old records |
| Edge Function billing spike | Infinite retry loop | Add circuit breaker; cap retries |

## Resources
- [Supabase Pricing](https://supabase.com/pricing)
- [Spend Cap Settings](https://supabase.com/docs/guides/platform/going-into-prod#spend-cap)
- [Database Size Management](https://supabase.com/docs/guides/database/inspect)

## Next Steps
For architecture patterns, see `supabase-reference-architecture`.
