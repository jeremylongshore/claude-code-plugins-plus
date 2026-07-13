# Data Backfill, Versioning, and Rollback

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
