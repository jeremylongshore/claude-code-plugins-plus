# Audit Queries — Find Cost Drivers

Full query and script set for Step 1 (audit current usage and identify cost
drivers). Run the SQL in the Dashboard SQL Editor; run the storage audit with a
service-role client.

## Database audit (SQL Editor)

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

## Storage audit (service-role script)

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

Check current spend in **Dashboard > Settings > Billing** — it shows usage
against plan limits with a breakdown by resource category.
