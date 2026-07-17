# Zero-Downtime Migration Patterns

Production schema changes must avoid locking tables. These patterns ensure migrations complete without blocking reads or writes.

**Add a column (safe — no lock):**

```sql
-- supabase/migrations/20260323000000_add_status_column.sql

-- Adding a nullable column with a default does NOT lock the table in Postgres 11+
ALTER TABLE public.orders ADD COLUMN status text DEFAULT 'pending';

-- Create an index CONCURRENTLY (does not block writes)
-- NOTE: CONCURRENTLY cannot run inside a transaction block
-- Supabase migrations run each file in a transaction, so use a separate migration
```

```sql
-- supabase/migrations/20260323000001_add_status_index.sql

-- This migration must run outside a transaction for CONCURRENTLY
-- Add this comment at the top of the file:
-- supabase:disable-transaction

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_status
  ON public.orders(status);
```

**Rename a column (two-phase approach):**

```sql
-- Phase 1: Add new column, backfill, update application code
-- supabase/migrations/20260324000000_add_display_name.sql

-- Add the new column
ALTER TABLE public.profiles ADD COLUMN display_name text;

-- Copy data from old column
UPDATE public.profiles SET display_name = full_name WHERE display_name IS NULL;

-- Create a trigger to keep both columns in sync during transition
CREATE OR REPLACE FUNCTION sync_name_columns()
RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'INSERT' OR NEW.full_name IS DISTINCT FROM OLD.full_name THEN
    NEW.display_name = NEW.full_name;
  END IF;
  IF TG_OP = 'INSERT' OR NEW.display_name IS DISTINCT FROM OLD.display_name THEN
    NEW.full_name = NEW.display_name;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sync_names
  BEFORE INSERT OR UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION sync_name_columns();
```

```sql
-- Phase 2: After all application code uses display_name (deploy + verify)
-- supabase/migrations/20260325000000_drop_full_name.sql

-- Remove the sync trigger
DROP TRIGGER IF EXISTS sync_names ON public.profiles;
DROP FUNCTION IF EXISTS sync_name_columns();

-- Drop the old column
ALTER TABLE public.profiles DROP COLUMN full_name;
```

**Change column type (safe approach):**

```sql
-- supabase/migrations/20260326000000_change_price_to_numeric.sql

-- DON'T DO THIS (locks table for the entire rewrite):
-- ALTER TABLE orders ALTER COLUMN price TYPE numeric(10,2);

-- SAFE: Add new column, backfill, swap
ALTER TABLE public.orders ADD COLUMN price_numeric numeric(10,2);

-- Backfill in a separate migration or via application code
UPDATE public.orders SET price_numeric = price::numeric(10,2)
WHERE price_numeric IS NULL;

-- After verifying all data is backfilled:
-- ALTER TABLE public.orders DROP COLUMN price;
-- ALTER TABLE public.orders RENAME COLUMN price_numeric TO price;
```

**Verify zero-downtime from the SDK:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

// Run during migration to verify no downtime
async function migrationHealthCheck(tableName: string) {
  const checks = [];

  for (let i = 0; i < 10; i++) {
    const start = performance.now();
    const { error } = await supabase
      .from(tableName)
      .select('id')
      .limit(1);

    checks.push({
      attempt: i + 1,
      latencyMs: Math.round(performance.now() - start),
      success: !error,
      error: error?.message,
    });

    await new Promise((r) => setTimeout(r, 1000));
  }

  const failures = checks.filter((c) => !c.success);
  console.log(`Health check: ${checks.length - failures.length}/${checks.length} passed`);
  if (failures.length > 0) {
    console.warn('Failures:', failures);
  }
}
```
