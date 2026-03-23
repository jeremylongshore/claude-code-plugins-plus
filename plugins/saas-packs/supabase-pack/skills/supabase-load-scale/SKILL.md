---
name: supabase-load-scale
description: |
  Scale Supabase projects for production load: read replicas, connection pooling
  tuning via Supavisor, compute size upgrades, CDN caching for Storage,
  Edge Function regional deployment, and database table partitioning.
  Use when preparing for traffic spikes, optimizing connection limits,
  setting up read replicas for analytics queries, or partitioning large tables.
  Trigger with phrases like "supabase scale", "supabase read replica",
  "supabase connection pooling", "supabase compute upgrade",
  "supabase CDN storage", "supabase edge function regions",
  "supabase partitioning", "supavisor", "supabase pool mode".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Bash(psql:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, scaling, performance, connection-pooling, read-replicas, partitioning]
---

# Supabase Load & Scale

## Overview

Supabase scaling operates at six layers: **read replicas** (offload analytics and reporting queries), **connection pooling** (Supavisor pgBouncer replacement with transaction/session modes), **compute upgrades** (vCPU/RAM tiers), **CDN for Storage** (cache public bucket assets at the edge), **Edge Function regions** (deploy functions closer to users), and **table partitioning** (split billion-row tables for query performance). This skill covers each layer with real `createClient` configuration, SQL, and CLI commands.

## Prerequisites

- Supabase project on a Pro plan or higher (read replicas require Pro+)
- `@supabase/supabase-js` v2+ installed
- `supabase` CLI installed and linked to your project
- Database access via `psql` or Supabase SQL Editor
- TypeScript project with generated database types

## Step 1 — Read Replicas and Connection Pooling

Read replicas let you route read-heavy queries (dashboards, reports, search) to replica databases while keeping writes on the primary. Supabase uses **Supavisor** (their pgBouncer replacement) for connection pooling with two modes: **transaction** (default, shares connections between requests) and **session** (holds a connection per client session, needed for prepared statements).

### Configure the Read Replica Client

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

// Primary client — handles all writes and real-time subscriptions
export const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// Read replica client — use for analytics, dashboards, search
// The read replica URL is available in Dashboard > Settings > Database
export const supabaseReadOnly = createClient<Database>(
  process.env.SUPABASE_READ_REPLICA_URL!,  // e.g., https://<project-ref>-ro.supabase.co
  process.env.SUPABASE_ANON_KEY!,          // same anon key works for replicas
  {
    db: { schema: 'public' },
    // Replicas may have slight lag (typically <100ms)
    // Do NOT use for reads-after-writes in the same request
  }
)

// Server-side admin client with connection pooling via Supavisor
// Use the pooled connection string (port 6543) instead of direct (port 5432)
export const supabaseAdmin = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    auth: { autoRefreshToken: false, persistSession: false },
    db: { schema: 'public' },
  }
)
```

### Direct Postgres Connections via Supavisor Pooling

```bash
# Transaction mode (default, port 6543) — best for serverless/short-lived connections
# Shares connections across clients. Cannot use prepared statements.
psql "postgresql://postgres.[project-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

# Session mode (port 5432 via pooler) — needed for prepared statements, LISTEN/NOTIFY
# One-to-one connection mapping per client.
psql "postgresql://postgres.[project-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres"

# Direct connection (no pooling) — for migrations and admin tasks only
psql "postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
```

### Route Queries to the Right Target

```typescript
// services/analytics.ts
import { supabaseReadOnly } from '../lib/supabase'

// Heavy analytics queries go to the read replica
export async function getDashboardMetrics(orgId: string) {
  const { data, error } = await supabaseReadOnly
    .from('events')
    .select('event_type, count:id.count()')
    .eq('org_id', orgId)
    .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())

  if (error) throw new Error(`Dashboard query failed: ${error.message}`)
  return data
}

// services/orders.ts
import { supabase } from '../lib/supabase'

// Writes always go to the primary
export async function createOrder(order: OrderInsert) {
  const { data, error } = await supabase
    .from('orders')
    .insert(order)
    .select('id, status, total, created_at')
    .single()

  if (error) throw new Error(`Order creation failed: ${error.message}`)
  return data
}
```

### Monitor Connection Pool Usage

```sql
-- Check active connections by source (run in SQL Editor)
SELECT
  usename,
  application_name,
  client_addr,
  state,
  count(*) AS connections
FROM pg_stat_activity
WHERE datname = 'postgres'
GROUP BY usename, application_name, client_addr, state
ORDER BY connections DESC;

-- Check connection limits for your compute tier
SHOW max_connections;
-- Micro: 60, Small: 90, Medium: 120, Large: 160, XL: 240, 2XL: 380, 4XL: 480
```

## Step 2 — Compute Upgrades, CDN for Storage, and Edge Function Regions

### Compute Size Selection Guide

| Tier | vCPU | RAM | Max Connections | Best For |
|------|------|-----|----------------|----------|
| Micro (Free) | 2 shared | 1 GB | 60 | Development, prototypes |
| Small (Pro) | 2 dedicated | 2 GB | 90 | Low-traffic production |
| Medium | 2 dedicated | 4 GB | 120 | Growing apps, moderate traffic |
| Large | 4 dedicated | 8 GB | 160 | High-traffic, complex queries |
| XL | 8 dedicated | 16 GB | 240 | Large datasets, concurrent users |
| 2XL | 16 dedicated | 32 GB | 380 | Enterprise, heavy analytics |
| 4XL | 32 dedicated | 64 GB | 480 | Mission-critical, max throughput |

```bash
# Upgrade compute via CLI (requires Pro plan)
supabase projects update --experimental --compute-size small  # or medium, large, xl, 2xl, 4xl

# Check current compute size
supabase projects list
```

### CDN Caching for Storage Buckets

Public buckets are automatically served through Supabase's CDN. Optimize cache behavior with proper headers and transforms.

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// Upload with cache-control headers for CDN optimization
async function uploadPublicAsset(
  bucket: string,
  path: string,
  file: File
) {
  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, file, {
      cacheControl: '31536000',  // 1 year cache for immutable assets
      upsert: false,             // prevent accidental overwrites
      contentType: file.type,
    })

  if (error) throw new Error(`Upload failed: ${error.message}`)

  // Get the CDN-cached public URL
  const { data: { publicUrl } } = supabase.storage
    .from(bucket)
    .getPublicUrl(path, {
      transform: {
        width: 800,        // Image transforms are cached at the CDN edge
        quality: 80,
        format: 'webp',
      },
    })

  return { path: data.path, publicUrl }
}

// Bust cache by uploading to a new path (content-addressed)
import { createHash } from 'crypto'

async function uploadVersionedAsset(bucket: string, file: Buffer, ext: string) {
  const hash = createHash('sha256').update(file).digest('hex').slice(0, 12)
  const path = `assets/${hash}.${ext}`

  const { error } = await supabase.storage
    .from(bucket)
    .upload(path, file, {
      cacheControl: '31536000',
      upsert: false,
    })

  if (error && error.message !== 'The resource already exists') {
    throw new Error(`Versioned upload failed: ${error.message}`)
  }

  return supabase.storage.from(bucket).getPublicUrl(path).data.publicUrl
}
```

### Edge Function Regional Deployment

```bash
# Deploy to a specific region (closer to your users)
supabase functions deploy my-function --region us-east-1
supabase functions deploy my-function --region eu-west-1
supabase functions deploy my-function --region ap-southeast-1

# List available regions
supabase functions list

# Deploy all functions to a region
supabase functions deploy --region us-east-1
```

```typescript
// supabase/functions/geo-router/index.ts
// Edge Function that runs in the region closest to the user
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

Deno.serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Edge Functions automatically run in the nearest region
  // Use this for latency-sensitive operations
  const { data, error } = await supabase
    .from('products')
    .select('id, name, price')
    .eq('region', req.headers.get('x-region') ?? 'us')
    .limit(20)

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }

  return new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=60',  // CDN caches the response
    },
  })
})
```

## Step 3 — Database Table Partitioning

For tables with millions/billions of rows, partitioning splits data into smaller physical chunks. Supabase supports PostgreSQL native partitioning (range, list, hash). Queries that include the partition key only scan relevant partitions.

### Range Partitioning by Date (Most Common)

```sql
-- Create the partitioned parent table
CREATE TABLE public.events (
  id         bigint GENERATED ALWAYS AS IDENTITY,
  org_id     uuid NOT NULL REFERENCES public.organizations(id),
  event_type text NOT NULL,
  payload    jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, created_at)  -- partition key must be in PK
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE public.events_2025_01 PARTITION OF public.events
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE public.events_2025_02 PARTITION OF public.events
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
CREATE TABLE public.events_2025_03 PARTITION OF public.events
  FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
-- ... create partitions for each month

-- Default partition catches anything that doesn't match
CREATE TABLE public.events_default PARTITION OF public.events DEFAULT;

-- Index each partition (PostgreSQL auto-creates on child tables from parent index)
CREATE INDEX idx_events_org_created ON public.events (org_id, created_at);
CREATE INDEX idx_events_type ON public.events (event_type);

-- Enable RLS on the parent table (policies apply to all partitions)
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own org events" ON public.events
  FOR SELECT USING (
    org_id IN (
      SELECT org_id FROM public.org_members WHERE user_id = auth.uid()
    )
  );
```

### Automate Partition Creation

```sql
-- Function to auto-create next month's partition
CREATE OR REPLACE FUNCTION public.create_monthly_partition()
RETURNS void AS $$
DECLARE
  next_month date := date_trunc('month', now() + interval '1 month');
  partition_name text;
  start_date text;
  end_date text;
BEGIN
  partition_name := 'events_' || to_char(next_month, 'YYYY_MM');
  start_date := to_char(next_month, 'YYYY-MM-DD');
  end_date := to_char(next_month + interval '1 month', 'YYYY-MM-DD');

  -- Skip if partition already exists
  IF NOT EXISTS (
    SELECT 1 FROM pg_class WHERE relname = partition_name
  ) THEN
    EXECUTE format(
      'CREATE TABLE public.%I PARTITION OF public.events FOR VALUES FROM (%L) TO (%L)',
      partition_name, start_date, end_date
    );
    RAISE NOTICE 'Created partition: %', partition_name;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Schedule via pg_cron (runs on the 25th of each month)
SELECT cron.schedule(
  'create-events-partition',
  '0 0 25 * *',
  $$SELECT public.create_monthly_partition()$$
);
```

### Query Partitioned Tables from the SDK

```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// IMPORTANT: Always include the partition key in your WHERE clause
// Without it, Postgres scans ALL partitions (defeats the purpose)

// GOOD: partition key (created_at) in the filter — scans only 1 partition
async function getRecentEvents(orgId: string) {
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()

  const { data, error } = await supabase
    .from('events')
    .select('id, event_type, payload, created_at')
    .eq('org_id', orgId)
    .gte('created_at', thirtyDaysAgo)   // <-- partition key filter
    .order('created_at', { ascending: false })
    .limit(100)

  if (error) throw new Error(`Events query failed: ${error.message}`)
  return data
}

// BAD: no partition key — scans every partition
async function getAllEvents(orgId: string) {
  const { data, error } = await supabase
    .from('events')
    .select('id, event_type, payload, created_at')
    .eq('org_id', orgId)  // no created_at filter = full table scan across all partitions
  // This query gets slower as more partitions are added
}

// Verify partition pruning with EXPLAIN
// Run in SQL Editor:
// EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM events WHERE org_id = '...' AND created_at > '2025-03-01';
// Look for "Partitions removed: N" in the output
```

### Drop Old Partitions (Data Retention)

```sql
-- Drop partitions older than 12 months (instant, no vacuum needed)
CREATE OR REPLACE FUNCTION public.drop_old_partitions(retention_months int DEFAULT 12)
RETURNS void AS $$
DECLARE
  cutoff date := date_trunc('month', now() - (retention_months || ' months')::interval);
  partition record;
BEGIN
  FOR partition IN
    SELECT inhrelid::regclass::text AS name
    FROM pg_inherits
    WHERE inhparent = 'public.events'::regclass
    AND inhrelid::regclass::text ~ 'events_\d{4}_\d{2}'
  LOOP
    -- Extract date from partition name and compare
    IF substring(partition.name FROM 'events_(\d{4}_\d{2})')::date < cutoff THEN
      EXECUTE format('DROP TABLE %s', partition.name);
      RAISE NOTICE 'Dropped old partition: %', partition.name;
    END IF;
  END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly cleanup
SELECT cron.schedule('drop-old-partitions', '0 2 1 * *',
  $$SELECT public.drop_old_partitions(12)$$
);
```

## Output

- Read replica client configured for analytics/dashboard queries, primary for writes
- Connection pooling mode selected (transaction vs session) with correct port
- Compute tier matched to traffic requirements
- Storage uploads optimized with CDN cache headers and image transforms
- Edge Functions deployed to the region closest to users
- Large tables partitioned by date range with automated partition management
- Data retention policy via partition drops

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `too many connections for role` | Exceeded Supavisor pool limit | Use transaction mode (port 6543), reduce idle connections, upgrade compute |
| Read replica returns stale data | Replication lag (typically <100ms) | Do not read-after-write on replica; use primary for consistency-critical reads |
| `no partition of relation "events" found for row` | Insert date outside any partition range | Create a DEFAULT partition or pre-create future partitions |
| Storage CDN returns old file | Cached at edge | Use content-addressed paths (`hash.ext`) or set shorter `cacheControl` |
| Edge Function cold start | First request to a region | Use `keep-alive` cron ping or accept ~200ms cold start |
| `prepared statement already exists` | Transaction mode doesn't support prepared statements | Switch to session mode (port 5432) or disable prepared statements in your ORM |

## Examples

### Quick Connection Pool Check

```bash
# Check how many connections are in use right now
psql "$DATABASE_URL" -c "SELECT count(*) AS active_connections FROM pg_stat_activity WHERE state = 'active';"
```

### Switch an Existing Table to Partitioned

```sql
-- You cannot ALTER an existing table to be partitioned.
-- Instead: create partitioned table, migrate data, swap names.

-- 1. Create new partitioned table
CREATE TABLE public.events_partitioned (LIKE public.events INCLUDING ALL)
  PARTITION BY RANGE (created_at);

-- 2. Create partitions for existing data range
CREATE TABLE public.events_p_2025_01 PARTITION OF public.events_partitioned
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
-- ... more partitions

-- 3. Copy data (do this during low traffic)
INSERT INTO public.events_partitioned SELECT * FROM public.events;

-- 4. Swap tables in a transaction
BEGIN;
  ALTER TABLE public.events RENAME TO events_old;
  ALTER TABLE public.events_partitioned RENAME TO events;
COMMIT;

-- 5. Verify, then drop old table
DROP TABLE public.events_old;
```

### Test Read Replica Lag

```typescript
import { supabase, supabaseReadOnly } from '../lib/supabase'

async function measureReplicaLag() {
  // Write to primary
  const { data: written } = await supabase
    .from('health_checks')
    .insert({ timestamp: new Date().toISOString() })
    .select('id, timestamp')
    .single()

  // Immediately read from replica
  const start = Date.now()
  let found = false

  while (!found && Date.now() - start < 5000) {
    const { data } = await supabaseReadOnly
      .from('health_checks')
      .select('id')
      .eq('id', written!.id)
      .maybeSingle()

    if (data) {
      found = true
      console.log(`Replica lag: ${Date.now() - start}ms`)
    } else {
      await new Promise(r => setTimeout(r, 10))
    }
  }

  if (!found) console.warn('Replica lag exceeds 5 seconds')
}
```

## Resources

- [Supabase Read Replicas](https://supabase.com/docs/guides/platform/read-replicas)
- [Supabase Connection Pooling (Supavisor)](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Supabase Compute Add-ons](https://supabase.com/docs/guides/platform/compute-add-ons)
- [Supabase Storage CDN](https://supabase.com/docs/guides/storage/cdn/fundamentals)
- [Supabase Edge Functions](https://supabase.com/docs/guides/functions)
- [PostgreSQL Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)

## Next Steps

For reliability patterns (circuit breakers, offline queues, graceful degradation), see `supabase-reliability-patterns`.
