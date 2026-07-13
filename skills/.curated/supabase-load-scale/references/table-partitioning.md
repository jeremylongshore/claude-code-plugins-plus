## Database Table Partitioning

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
