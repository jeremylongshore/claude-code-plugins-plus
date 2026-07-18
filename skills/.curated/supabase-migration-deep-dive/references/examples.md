# Examples

**Example 1 — Complete migration workflow:**

```text
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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
