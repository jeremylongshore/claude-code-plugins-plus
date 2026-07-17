# Testing Patterns Reference

Concrete test patterns the CI workflow runs: pgTAP database tests for schema and
RLS validation, plus application tests against the local Supabase instance.

## Database Test Example (pgTAP)

Write pgTAP tests in `supabase/tests/` to validate RLS policies and schema constraints in CI:

```sql
-- supabase/tests/rls_validation.test.sql
begin;
select plan(3);

-- All public tables must have RLS enabled
select is(
  (select count(*)::int from pg_tables
   where schemaname = 'public' and rowsecurity = false),
  0,
  'All public tables have RLS enabled'
);

-- Verify anon role cannot read protected data
set role anon;
select is_empty(
  'select * from public.profiles',
  'anon role cannot read profiles without auth'
);
reset role;

-- Verify authenticated users can only see their own rows
set role authenticated;
select isnt_empty(
  $$select * from pg_policies where tablename = 'profiles' and cmd = 'SELECT'$$,
  'profiles table has a SELECT policy for authenticated users'
);
reset role;

select * from finish();
rollback;
```

Run locally with `npx supabase test db` before pushing.

## Application Test Pattern

Use `createClient` from `@supabase/supabase-js` in tests, pointing at the local instance:

```typescript
// tests/setup.ts
import { createClient } from '@supabase/supabase-js';
import type { Database } from '../src/types/database.types';

export const supabase = createClient<Database>(
  process.env.SUPABASE_URL ?? 'http://127.0.0.1:54321',
  process.env.SUPABASE_ANON_KEY ?? 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
);

// tests/profiles.test.ts
import { supabase } from './setup';

test('can insert and read a profile', async () => {
  const { data, error } = await supabase
    .from('profiles')
    .insert({ id: 'test-user', display_name: 'Test' })
    .select()
    .single();

  expect(error).toBeNull();
  expect(data?.display_name).toBe('Test');
});
```
