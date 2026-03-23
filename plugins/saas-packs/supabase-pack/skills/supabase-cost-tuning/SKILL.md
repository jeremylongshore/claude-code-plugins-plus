---
name: supabase-cost-tuning
description: |
  Optimize Supabase costs through plan selection, database tuning, storage cleanup,
  connection pooling, and Edge Function optimization.
  Use when analyzing Supabase billing, reducing costs, right-sizing compute,
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

Reduce Supabase spend by auditing usage against plan limits, eliminating database and storage waste, and right-sizing compute resources. The three biggest levers: database optimization (vacuum, index cleanup, archival), storage lifecycle management (compress before upload, orphan cleanup), and connection pooling to reduce compute add-on requirements.

## Prerequisites

- Supabase project with Dashboard access (Settings > Billing)
- `@supabase/supabase-js` installed: `npm install @supabase/supabase-js`
- Service role key for admin operations (storage audit, cleanup scripts)
- SQL editor access (Dashboard > SQL Editor or `psql` connection)

## Pricing Reference

| Resource | Free Tier | Pro ($25/mo) | Team ($599/mo) |
|----------|-----------|--------------|----------------|
| Database | 500 MB | 8 GB included, $0.125/GB extra | 8 GB included |
| Storage | 1 GB | 100 GB included, $0.021/GB extra | 100 GB included |
| Bandwidth | 5 GB | 250 GB included, $0.09/GB extra | 250 GB included |
| Edge Functions | 500K invocations | 2M invocations, $2/million extra | 2M invocations |
| Realtime | 200 concurrent | 500 concurrent | 500 concurrent |
| Auth MAU | 50,000 | 100,000 | 100,000 |

**Compute add-ons** (Pro and above):

| Instance | vCPUs | RAM | Price |
|----------|-------|-----|-------|
| Micro | 2 | 1 GB | Included with Pro |
| Small | 2 | 2 GB | $25/mo |
| Medium | 2 | 4 GB | $50/mo |
| Large | 4 | 8 GB | $100/mo |
| XL | 8 | 16 GB | $200/mo |
| 2XL | 16 | 32 GB | $400/mo |

**Decision framework:** Read replicas ($25/mo each) beat scaling up when reads dominate and you need geographic distribution. Connection pooling (Supavisor, free) reduces compute pressure from idle connections.

## Instructions

### Step 1: Audit Current Usage and Identify Cost Drivers

Run these queries in the SQL Editor to understand where your database budget is going:

```sql
-- Total database size
select pg_size_pretty(pg_database_size(current_database())) as total_db_size;

-- Database size by table (find the biggest offenders)
select
  relname as table_name,
  pg_size_pretty(pg_total_relation_size(relid)) as total_size,
  pg_size_pretty(pg_relation_size(relid)) as table_size,
  pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size,
  n_live_tup as row_count
from pg_stat_user_tables
order by pg_total_relation_size(relid) desc
limit 20;

-- Find unused indexes consuming space (zero scans since last stats reset)
select
  schemaname || '.' || indexrelname as index_name,
  pg_size_pretty(pg_relation_size(indexrelid)) as size,
  idx_scan as scans_since_reset
from pg_stat_user_indexes
where idx_scan = 0
  and schemaname = 'public'
order by pg_relation_size(indexrelid) desc
limit 10;

-- Check dead tuple bloat (high ratio means VACUUM is needed)
select
  relname,
  n_dead_tup,
  n_live_tup,
  round(n_dead_tup::numeric / greatest(n_live_tup, 1) * 100, 1) as dead_pct
from pg_stat_user_tables
where n_dead_tup > 1000
order by n_dead_tup desc;

-- Connection count (high count may indicate pooling issues)
select count(*) as active_connections,
  max_conn as max_allowed
from pg_stat_activity,
  (select setting::int as max_conn from pg_settings where name = 'max_connections') mc
group by max_conn;
```

Audit storage usage programmatically:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseAdmin = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

// List storage usage per bucket
const { data: buckets } = await supabaseAdmin.storage.listBuckets()

for (const bucket of buckets ?? []) {
  const { data: files } = await supabaseAdmin.storage
    .from(bucket.name)
    .list('', { limit: 1000 })

  const totalSize = files?.reduce((sum, f) => sum + (f.metadata?.size || 0), 0) ?? 0
  console.log(`${bucket.name}: ${(totalSize / 1024 / 1024).toFixed(1)} MB`)
}
```

Check your current spend: **Dashboard > Settings > Billing** shows usage against plan limits with a breakdown by resource category.

### Step 2: Optimize Database, Storage, and Bandwidth

**Database optimization — reclaim space and reduce bloat:**

```sql
-- Archive old data before deleting (preserve for compliance/analytics)
create table if not exists public.events_archive (like public.events including all);

insert into public.events_archive
select * from public.events
where created_at < now() - interval '6 months';

delete from public.events
where created_at < now() - interval '6 months';

-- Run VACUUM ANALYZE to reclaim space and update query planner stats
vacuum (verbose, analyze) public.events;

-- Drop confirmed-unused indexes (verify idx_scan = 0 from Step 1)
-- WARNING: always confirm the index is unused before dropping
drop index if exists idx_events_legacy_status;

-- Remove soft-deleted records past retention period
delete from public.orders
where deleted_at is not null
  and deleted_at < now() - interval '90 days';

vacuum (analyze) public.orders;
```

**Storage optimization — compress before upload, clean orphans:**

```typescript
// Compress images before upload (reduces storage + bandwidth)
async function uploadCompressed(
  bucket: string,
  path: string,
  file: File
): Promise<string> {
  // Use client-side compression before uploading
  const compressed = await compressImage(file, { maxWidth: 1920, quality: 0.8 })

  const { data, error } = await supabaseAdmin.storage
    .from(bucket)
    .upload(path, compressed, {
      contentType: file.type,
      upsert: true,
    })

  if (error) throw error
  return data.path
}

// Clean orphaned files older than 30 days
async function cleanOrphanedUploads() {
  const cutoff = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()

  const { data: orphans } = await supabaseAdmin
    .from('storage.objects')
    .select('name, created_at')
    .eq('bucket_id', 'uploads')
    .lt('created_at', cutoff)

  if (orphans?.length) {
    const paths = orphans.map(o => o.name)
    // Delete in batches of 100
    for (let i = 0; i < paths.length; i += 100) {
      await supabaseAdmin.storage
        .from('uploads')
        .remove(paths.slice(i, i + 100))
    }
    console.log(`Cleaned ${orphans.length} orphaned files`)
  }
}
```

**Bandwidth reduction — select only what you need:**

```typescript
// BAD: transfers entire row (wastes bandwidth)
const { data } = await supabase.from('products').select('*')

// GOOD: request only needed columns
const { data } = await supabase.from('products').select('id, name, price')

// Use count queries for totals (head: true = zero data transferred)
const { count } = await supabase
  .from('orders')
  .select('*', { count: 'exact', head: true })

// Paginate large result sets
const { data } = await supabase
  .from('logs')
  .select('id, message, created_at')
  .order('created_at', { ascending: false })
  .range(0, 49)  // 50 rows per page
```

### Step 3: Right-Size Compute and Reduce Edge Function Costs

**Connection pooling with Supavisor** (reduces need for compute upgrades):

```typescript
// Use the pooler connection string instead of direct connection
// Dashboard > Settings > Database > Connection string > Mode: Transaction

// In your app, use the pooled connection URL (port 6543)
// Direct:   postgresql://postgres:pw@db.xxx.supabase.co:5432/postgres
// Pooled:   postgresql://postgres:pw@db.xxx.supabase.co:6543/postgres

// For @supabase/supabase-js, connection pooling is handled automatically
// For direct pg connections (migrations, ORMs), use pooled URL:
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,  // Use pooler URL
  max: 10,  // Limit client-side pool size too
})
```

**Edge Function cold start reduction:**

```typescript
// Minimize cold starts — keep imports lightweight
// BAD: importing heavy libraries unconditionally
import { parse } from 'some-huge-csv-library'

// GOOD: dynamic import only when needed
Deno.serve(async (req) => {
  const { action } = await req.json()

  if (action === 'parse-csv') {
    const { parse } = await import('some-huge-csv-library')
    return new Response(JSON.stringify(parse(data)))
  }

  // Fast path: no heavy import needed
  return new Response(JSON.stringify({ status: 'ok' }))
})

// Cache expensive computations across invocations
// Deno Deploy isolates persist for ~60 seconds between requests
const _cache = new Map<string, { data: unknown; ts: number }>()

function cached<T>(key: string, ttlMs: number, fn: () => T): T {
  const entry = _cache.get(key)
  if (entry && Date.now() - entry.ts < ttlMs) return entry.data as T
  const data = fn()
  _cache.set(key, { data, ts: Date.now() })
  return data
}
```

**Usage monitoring — track spend with a lightweight counter:**

```sql
-- Create usage tracking table
create table public.api_usage (
  id bigint generated always as identity primary key,
  endpoint text not null,
  method text not null,
  user_id uuid references auth.users(id),
  response_bytes int default 0,
  created_at timestamptz default now()
);

-- Create partitioned index for efficient time-range queries
create index idx_api_usage_created on public.api_usage (created_at desc);

-- Materialized view for daily cost estimation
create materialized view public.daily_usage_summary as
select
  date_trunc('day', created_at) as day,
  endpoint,
  count(*) as requests,
  sum(response_bytes) as total_bytes
from public.api_usage
group by 1, 2;

-- Auto-refresh via pg_cron (enable extension first)
select cron.schedule(
  'refresh-usage-summary',
  '0 1 * * *',
  'refresh materialized view concurrently public.daily_usage_summary;'
);
```

## Output

After completing all three steps, you will have:

- Database size audit with table-level breakdown and dead tuple analysis
- Unused indexes identified and dropped to reclaim storage
- Old data archived and vacuumed to free database space
- Storage orphans cleaned and upload compression implemented
- Bandwidth reduced through column selection and pagination
- Connection pooling configured to avoid unnecessary compute upgrades
- Edge Function cold starts minimized with dynamic imports and caching
- Usage monitoring table and daily summary view for spend visibility

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Database approaching 500 MB (Free) or 8 GB (Pro) | Data growth without archival | Archive old records, VACUUM, drop unused indexes |
| Storage costs climbing monthly | Orphaned uploads accumulating | Schedule cleanup job for files not linked to records |
| Unexpected bandwidth spike | `select('*')` on large tables | Use specific column lists; add `.range()` pagination |
| Edge Function billing spike | Retry loops or heavy imports | Add circuit breaker with max 3 retries; dynamic imports |
| Connection limit errors | Too many direct connections | Switch to pooler URL (port 6543); reduce client pool size |
| Spend cap reached | Usage exceeded Pro included resources | Enable spend cap in Dashboard > Settings > Billing to prevent overage |
| VACUUM not reclaiming space | Long-running transactions holding locks | Check `pg_stat_activity` for idle-in-transaction; terminate stale sessions |

## Examples

**Quick cost check for a growing project:**

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

// Check database size against plan limit
const { data: dbSize } = await supabase.rpc('get_db_size')
// CREATE FUNCTION get_db_size() RETURNS text AS $$
//   SELECT pg_size_pretty(pg_database_size(current_database()));
// $$ LANGUAGE sql;

console.log(`Database size: ${dbSize}`)

// Check if you're approaching storage limits
const { data: buckets } = await supabase.storage.listBuckets()
console.log(`Storage buckets: ${buckets?.length ?? 0}`)
```

**Monthly cost estimation script:**

```typescript
function estimateMonthlyCost(usage: {
  dbSizeGb: number
  storageGb: number
  bandwidthGb: number
  edgeFnInvocations: number
  mau: number
}) {
  const pro = {
    base: 25,
    dbOverage: Math.max(0, usage.dbSizeGb - 8) * 0.125,
    storageOverage: Math.max(0, usage.storageGb - 100) * 0.021,
    bandwidthOverage: Math.max(0, usage.bandwidthGb - 250) * 0.09,
    edgeFnOverage: Math.max(0, usage.edgeFnInvocations - 2_000_000) / 1_000_000 * 2,
  }

  const total = pro.base + pro.dbOverage + pro.storageOverage
    + pro.bandwidthOverage + pro.edgeFnOverage

  console.log('Estimated monthly cost breakdown:')
  console.log(`  Base Pro plan:     $${pro.base}`)
  console.log(`  DB overage:        $${pro.dbOverage.toFixed(2)}`)
  console.log(`  Storage overage:   $${pro.storageOverage.toFixed(2)}`)
  console.log(`  Bandwidth overage: $${pro.bandwidthOverage.toFixed(2)}`)
  console.log(`  Edge Fn overage:   $${pro.edgeFnOverage.toFixed(2)}`)
  console.log(`  TOTAL:             $${total.toFixed(2)}/mo`)

  return total
}

// Example: project with 12GB DB, 150GB storage, 300GB bandwidth
estimateMonthlyCost({
  dbSizeGb: 12,
  storageGb: 150,
  bandwidthGb: 300,
  edgeFnInvocations: 1_500_000,
  mau: 80_000,
})
// Base Pro plan:     $25
// DB overage:        $0.50
// Storage overage:   $1.05
// Bandwidth overage: $4.50
// Edge Fn overage:   $0.00
// TOTAL:             $31.05/mo
```

## Resources

- [Supabase Pricing](https://supabase.com/pricing) — plan comparison and calculator
- [Compute Add-ons](https://supabase.com/docs/guides/platform/compute-add-ons) — instance sizing guide
- [Spend Cap](https://supabase.com/docs/guides/platform/spend-cap) — prevent unexpected overage charges
- [Database Disk Usage](https://supabase.com/docs/guides/platform/database-size) — monitoring and management
- [Connection Pooling (Supavisor)](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler) — reduce connection overhead
- [Edge Functions Best Practices](https://supabase.com/docs/guides/functions/best-practices) — cold start and performance tips
- [supabase-js Reference](https://supabase.com/docs/reference/javascript/introduction) — `createClient` and SDK patterns

## Next Steps

For architecture patterns, see `supabase-reference-architecture`.
For performance tuning beyond cost, see `supabase-performance-tuning`.
