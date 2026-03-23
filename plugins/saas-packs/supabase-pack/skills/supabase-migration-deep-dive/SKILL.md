---
name: supabase-migration-deep-dive
description: |
  Database migration patterns with Supabase CLI: npx supabase migration new, zero-downtime
  migrations, data backfill strategies, schema versioning, rollback strategies, and type generation.
  Use when creating database migrations, performing zero-downtime schema changes, backfilling
  data in production, managing schema versions, or planning rollback strategies.
  Trigger: "supabase migration", "supabase schema change", "supabase zero downtime",
  "supabase rollback", "supabase db push", "supabase migration new".
allowed-tools: Read, Write, Edit, Bash(npx supabase:*), Bash(supabase:*), Bash(psql:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, migration, database, schema, zero-downtime, rollback]
---

# Supabase Migration Deep Dive

## Overview

Supabase migrations are SQL files managed by the CLI that track schema changes across environments. This skill covers the complete migration lifecycle: creating migrations with `npx supabase migration new`, writing zero-downtime schema changes that avoid table locks, backfilling data in batches, managing schema versioning across environments, planning rollback strategies, and regenerating TypeScript types after schema changes. Every pattern uses real Supabase CLI commands and `createClient` from `@supabase/supabase-js`.

**When to use:** Creating new database migrations, modifying production schemas without downtime, backfilling existing data after adding columns, managing migration history across dev/staging/production, rolling back failed migrations, or regenerating TypeScript types.

## Prerequisites

- Supabase CLI installed: `npm install -g supabase` or `npx supabase --version`
- `@supabase/supabase-js` v2+ installed in your project
- Local Supabase running: `npx supabase start`
- Understanding of PostgreSQL DDL and transaction behavior

## Instructions

### Step 1: Create and Manage Migrations

Use the Supabase CLI to create, test, and apply migrations. Each migration is a timestamped SQL file that runs in order.

**Create a new migration:**

```bash
# Create a migration file with a descriptive name
npx supabase migration new add_profiles_table
# Creates: supabase/migrations/20260322120000_add_profiles_table.sql

# List all migrations and their status
npx supabase migration list

# Check which migrations have been applied locally
npx supabase db reset --dry-run
```

**Write the migration SQL:**

```sql
-- supabase/migrations/20260322120000_add_profiles_table.sql

-- Create the profiles table
CREATE TABLE public.profiles (
  id uuid REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email text UNIQUE NOT NULL,
  full_name text,
  avatar_url text,
  bio text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "users_read_own_profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "users_update_own_profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Create an index for email lookups
CREATE INDEX idx_profiles_email ON public.profiles(email);

-- Auto-create profile on user signup (trigger)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, avatar_url)
  VALUES (
    new.id,
    new.email,
    new.raw_user_meta_data ->> 'full_name',
    new.raw_user_meta_data ->> 'avatar_url'
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Updated_at trigger
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS trigger AS $$
BEGIN
  new.updated_at = now();
  RETURN new;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
```

**Test the migration locally:**

```bash
# Apply all migrations and seed data (destructive — resets local DB)
npx supabase db reset

# Run pgTAP tests if configured
npx supabase test db

# Verify the schema
npx supabase db lint

# Generate updated TypeScript types
npx supabase gen types typescript --local > lib/database.types.ts
```

**Apply migrations to remote environments:**

```bash
# Push to staging
npx supabase link --project-ref <staging-ref>
npx supabase db push
# Verify: npx supabase migration list --linked

# Push to production (same migration files)
npx supabase link --project-ref <prod-ref>
npx supabase db push
```

### Step 2: Zero-Downtime Migration Patterns

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

### Step 3: Data Backfill, Versioning, and Rollback

Backfill data in batches to avoid overwhelming the database, track schema versions, and plan rollback strategies for failed migrations.

**Batch data backfill from the SDK:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

// Backfill a new column in batches (avoids long-running transactions)
async function backfillColumn(
  table: string,
  column: string,
  computeValue: (row: any) => any,
  batchSize = 500
) {
  let processed = 0;
  let lastId: string | null = null;

  while (true) {
    // Fetch a batch of rows that need backfilling
    let query = supabase
      .from(table)
      .select('*')
      .is(column, null)
      .order('id', { ascending: true })
      .limit(batchSize);

    if (lastId) {
      query = query.gt('id', lastId);
    }

    const { data: rows, error } = await query;
    if (error) throw error;
    if (!rows || rows.length === 0) break;

    // Update each row with the computed value
    for (const row of rows) {
      const newValue = computeValue(row);
      const { error: updateError } = await supabase
        .from(table)
        .update({ [column]: newValue })
        .eq('id', row.id);

      if (updateError) {
        console.error(`Failed to update ${row.id}:`, updateError.message);
      }
    }

    lastId = rows[rows.length - 1].id;
    processed += rows.length;
    console.log(`Backfilled ${processed} rows...`);

    // Brief pause to avoid overwhelming the database
    await new Promise((r) => setTimeout(r, 100));
  }

  console.log(`Backfill complete: ${processed} rows updated`);
}

// Example: backfill a slug column from name
await backfillColumn('projects', 'slug', (row) =>
  row.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
);
```

**Schema versioning — track what's deployed where:**

```bash
# Check migration status on each environment
npx supabase link --project-ref <staging-ref>
npx supabase migration list

# Compare local migrations with remote
npx supabase db diff --linked

# Generate a diff between local and remote schemas
npx supabase db diff --linked --schema public > schema-diff.sql
```

```sql
-- Query the migration history directly
SELECT version, name, statements_applied_at
FROM supabase_migrations.schema_migrations
ORDER BY version DESC
LIMIT 20;
```

**Rollback strategies:**

```sql
-- Strategy 1: Write a compensating migration
-- supabase/migrations/20260327000000_rollback_status_column.sql

-- Reverse the previous migration
DROP INDEX IF EXISTS idx_orders_status;
ALTER TABLE public.orders DROP COLUMN IF EXISTS status;
```

```bash
# Strategy 2: Repair migration history (if migration partially failed)
# Mark a migration as rolled back in the tracking table
npx supabase migration repair --status reverted 20260326000000

# Then re-apply after fixing
npx supabase db push
```

```typescript
// Strategy 3: Feature-flag a schema change
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, anonKey);

// Use old or new column based on feature flag
async function getOrderStatus(orderId: string) {
  const useNewSchema = process.env.USE_NEW_STATUS_COLUMN === 'true';

  const { data, error } = await supabase
    .from('orders')
    .select(useNewSchema ? 'status_v2' : 'status')
    .eq('id', orderId)
    .single();

  if (error) throw error;
  return useNewSchema ? data.status_v2 : data.status;
}
```

**Regenerate types after migration:**

```bash
# From local development database (recommended)
npx supabase gen types typescript --local > lib/database.types.ts

# From linked remote project
npx supabase gen types typescript --linked > lib/database.types.ts

# Verify types compile
npx tsc --noEmit
```

## Output

After completing this skill, you will have:

- **Migration creation workflow** — `npx supabase migration new` with descriptive SQL files and local testing
- **Zero-downtime patterns** — safe column additions, two-phase renames, concurrent index creation
- **Batch backfill** — SDK-based row-by-row updates with progress logging and rate limiting
- **Schema versioning** — `supabase migration list` and `db diff` for comparing environments
- **Rollback strategies** — compensating migrations, `migration repair`, and feature-flagged schema changes
- **Type regeneration** — `supabase gen types typescript` after every schema change
- **Migration promotion** — `db push` workflow from local to staging to production

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `migration has already been applied` | Re-running existing migration | Use `supabase migration list` to check status; never modify applied migrations |
| `cannot run inside a transaction block` | `CREATE INDEX CONCURRENTLY` in transaction | Add `-- supabase:disable-transaction` comment at top of migration file |
| `column does not exist` after migration | Migration not applied or types stale | Run `supabase db push` then `supabase gen types typescript` |
| `deadlock detected` during backfill | Concurrent updates on same rows | Reduce batch size; add retry logic with exponential backoff |
| `statement timeout` on large table | Migration takes longer than timeout | Increase `statement_timeout` in migration: `SET statement_timeout = '300s';` |
| `migration repair` failed | Wrong version number | Use exact version from `supabase migration list` (the timestamp prefix) |
| `db diff` shows unexpected changes | Schema drift from manual SQL Editor changes | Run `supabase db pull` to capture manual changes as a migration |
| Type mismatch after migration | Generated types don't match new schema | Delete `database.types.ts` and regenerate from `--local` or `--linked` |

## Examples

**Example 1 — Complete migration workflow:**

```bash
# 1. Create migration
npx supabase migration new add_tags_to_projects

# 2. Write SQL
cat > supabase/migrations/20260322150000_add_tags_to_projects.sql << 'SQL'
ALTER TABLE public.projects ADD COLUMN tags text[] DEFAULT '{}';
CREATE INDEX idx_projects_tags ON public.projects USING GIN(tags);
SQL

# 3. Test locally
npx supabase db reset
npx supabase gen types typescript --local > lib/database.types.ts

# 4. Push to staging
npx supabase link --project-ref <staging-ref>
npx supabase db push

# 5. Push to production
npx supabase link --project-ref <prod-ref>
npx supabase db push
```

**Example 2 — Backfill with progress tracking:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

// Backfill default tags for existing projects
const { count } = await supabase
  .from('projects')
  .select('*', { count: 'exact', head: true })
  .is('tags', null);

console.log(`${count} projects need backfill`);

await backfillColumn('projects', 'tags', (row) => {
  // Derive tags from project name and description
  const tags: string[] = [];
  if (row.name?.includes('API')) tags.push('api');
  if (row.name?.includes('Web')) tags.push('web');
  return tags.length > 0 ? tags : ['untagged'];
});
```

**Example 3 — Safe enum migration:**

```sql
-- supabase/migrations/20260328000000_add_order_status_enum.sql

-- DON'T: ALTER TYPE with new values inside a transaction
-- DO: Use text with CHECK constraint instead

ALTER TABLE public.orders
  ADD CONSTRAINT chk_order_status
  CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'));

-- To add a new status later, just drop and recreate the constraint:
-- ALTER TABLE public.orders DROP CONSTRAINT chk_order_status;
-- ALTER TABLE public.orders ADD CONSTRAINT chk_order_status
--   CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded'));
```

## Resources

- [Database Migrations — Supabase Docs](https://supabase.com/docs/guides/deployment/database-migrations)
- [Supabase CLI Migration Commands](https://supabase.com/docs/reference/cli/supabase-migration)
- [supabase db push — Supabase Docs](https://supabase.com/docs/reference/cli/supabase-db-push)
- [supabase gen types — Supabase Docs](https://supabase.com/docs/reference/cli/supabase-gen-types)
- [Zero-Downtime PostgreSQL Migrations](https://www.postgresql.org/docs/current/sql-altertable.html)
- [supabase db diff — Supabase Docs](https://supabase.com/docs/reference/cli/supabase-db-diff)

## Next Steps

- For advanced troubleshooting after migrations, see `supabase-advanced-troubleshooting`
- For multi-environment migration promotion, see `supabase-multi-env-setup`
- For performance tuning after schema changes, see `supabase-performance-tuning`
