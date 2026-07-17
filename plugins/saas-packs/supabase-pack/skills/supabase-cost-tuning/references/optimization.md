# Optimization — Database, Storage, Bandwidth, Compute, Edge Functions

Full code for Step 2 (optimize database, storage, and bandwidth) and Step 3
(right-size compute and reduce Edge Function costs).

## Step 2: Optimize database, storage, and bandwidth

### Database optimization — reclaim space and reduce bloat

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

### Storage optimization — compress before upload, clean orphans

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

### Bandwidth reduction — select only what you need

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

## Step 3: Right-size compute and reduce Edge Function costs

### Connection pooling with Supavisor (reduces need for compute upgrades)

```typescript
// Use the pooler connection string instead of direct connection
// Dashboard > Settings > Database > Connection string > Mode: Transaction

// In your app, use the pooled connection URL (port 6543)
// Direct:   postgresql://postgres:pw@db.xxx.supabase.co:5432/postgres
// Pooled:   postgresql://postgres:pw@db.xxx.supabase.co:6543/postgres
// (Supavisor listens on 6543; the direct Postgres port is 5432.)

// For @supabase/supabase-js, connection pooling is handled automatically
// For direct pg connections (migrations, ORMs), use pooled URL:
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,  // Use pooler URL
  max: 10,  // Limit client-side pool size too
})
```

### Edge Function cold start reduction

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

### Usage monitoring — track spend with a lightweight counter

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
