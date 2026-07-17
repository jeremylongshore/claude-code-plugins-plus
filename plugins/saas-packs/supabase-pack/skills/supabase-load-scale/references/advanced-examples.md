# Advanced Scaling Examples

## Switch an Existing Table to Partitioned

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

## Test Read Replica Lag

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
