# Typed client queries against the generated schema

After applying the migration and generating types (`npx supabase gen types typescript
--local > types/supabase.ts`), use the generated `Database` type to get end-to-end type
safety on every query.

## Client setup and typed queries

```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from './types/supabase'

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Typed insert
const { data: org, error } = await supabase
  .from('organizations')
  .insert({ name: 'Acme Corp', slug: 'acme', plan: 'pro' })
  .select()
  .single()

// Typed select with foreign key join
const { data: tasks } = await supabase
  .from('tasks')
  .select('*, project:project_id(name, organization_id)')
  .eq('status', 'todo')
  .order('due_date', { ascending: true })

// Nested join across multiple tables
const { data: orgWithProjects } = await supabase
  .from('organizations')
  .select(`
    id, name, slug,
    projects:projects(
      id, name, status,
      tasks:tasks(id, title, status, assigned_to)
    )
  `)
  .eq('slug', 'acme')
  .single()
```

## Verifying RLS is enforced

```typescript
// This should return only rows the authenticated user can see
const { data, error } = await supabase.from('organizations').select('*')

if (error) {
  console.error('RLS check failed:', error.message)
}
console.log(`User can see ${data?.length ?? 0} organizations`)
```

## Querying the e-commerce schema

The same client pattern applies to any schema built with this skill. Against the
e-commerce migration (see [worked-schema-examples.md](worked-schema-examples.md)):

```typescript
// Products with store info
const { data: products } = await supabase
  .from('products')
  .select('*, store:store_id(name, slug)')
  .eq('is_active', true)
  .gte('inventory', 1)
  .order('price', { ascending: true })
  .limit(20)
```
