---
name: supabase-hello-world
description: |
  Create a minimal working Supabase example with real database queries.
  Use when starting a new Supabase integration, testing your setup,
  or learning basic CRUD operations with the Supabase JS client.
  Trigger with phrases like "supabase hello world", "supabase example",
  "supabase quick start", "simple supabase", "first supabase query".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, api, getting-started]

---
# Supabase Hello World

## Overview
Build a minimal working example that creates a table, inserts a row, queries it back, and demonstrates the core Supabase CRUD operations using real `@supabase/supabase-js` client methods.

## Prerequisites
- Completed `supabase-install-auth` setup
- Supabase project with valid URL and anon key

## Instructions

### Step 1: Create a Table via Migration

```bash
# Create a migration file
supabase migration new create_todos

# This creates: supabase/migrations/<timestamp>_create_todos.sql
```

Write the migration SQL:

```sql
-- supabase/migrations/<timestamp>_create_todos.sql
create table public.todos (
  id bigint generated always as identity primary key,
  title text not null,
  is_complete boolean default false,
  user_id uuid references auth.users(id),
  inserted_at timestamptz default now()
);

-- Enable Row Level Security
alter table public.todos enable row level security;

-- Allow authenticated users to read their own todos
create policy "Users can view own todos"
  on public.todos for select
  using (auth.uid() = user_id);

-- Allow authenticated users to insert their own todos
create policy "Users can create todos"
  on public.todos for insert
  with check (auth.uid() = user_id);

-- Allow authenticated users to update their own todos
create policy "Users can update own todos"
  on public.todos for update
  using (auth.uid() = user_id);

-- Allow authenticated users to delete their own todos
create policy "Users can delete own todos"
  on public.todos for delete
  using (auth.uid() = user_id);
```

```bash
# Apply the migration locally
supabase db reset

# Or push to remote
supabase db push
```

### Step 2: CRUD Operations

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// INSERT a row
const { data: newTodo, error: insertError } = await supabase
  .from('todos')
  .insert({ title: 'Hello from Supabase!', is_complete: false })
  .select()
  .single()

console.log('Created:', newTodo)
// { id: 1, title: 'Hello from Supabase!', is_complete: false, ... }

// SELECT rows
const { data: todos, error: selectError } = await supabase
  .from('todos')
  .select('id, title, is_complete, inserted_at')
  .order('inserted_at', { ascending: false })
  .limit(10)

console.log('Todos:', todos)

// UPDATE a row
const { data: updated, error: updateError } = await supabase
  .from('todos')
  .update({ is_complete: true })
  .eq('id', 1)
  .select()
  .single()

console.log('Updated:', updated)

// DELETE a row
const { error: deleteError } = await supabase
  .from('todos')
  .delete()
  .eq('id', 1)

console.log('Deleted:', deleteError ? 'Failed' : 'Success')
```

### Step 3: Filtering and Querying

```typescript
// Filter with multiple conditions
const { data } = await supabase
  .from('todos')
  .select('*')
  .eq('is_complete', false)
  .ilike('title', '%urgent%')
  .order('inserted_at', { ascending: false })

// Count rows without fetching data
const { count } = await supabase
  .from('todos')
  .select('*', { count: 'exact', head: true })

// Upsert (insert or update on conflict)
const { data: upserted } = await supabase
  .from('todos')
  .upsert({ id: 1, title: 'Updated title', is_complete: true })
  .select()
  .single()

// Select with foreign key joins
const { data: todosWithUser } = await supabase
  .from('todos')
  .select(`
    id,
    title,
    user:user_id (
      email
    )
  `)
```

### Step 4: Error Handling Pattern

```typescript
async function safeFetch<T>(
  query: PromiseLike<{ data: T | null; error: any }>
): Promise<T> {
  const { data, error } = await query
  if (error) {
    console.error(`Supabase error [${error.code}]: ${error.message}`)
    throw new Error(error.message)
  }
  return data as T
}

// Usage
const todos = await safeFetch(
  supabase.from('todos').select('*').eq('is_complete', false)
)
```

## Output
- `todos` table created with RLS policies
- Working INSERT, SELECT, UPDATE, DELETE operations
- Filter and join queries demonstrated
- Type-safe error handling pattern

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `PGRST116: relation "todos" does not exist` | Table not created | Run the migration with `supabase db push` |
| `PGRST301: JWT expired` | Auth token expired | Refresh the session or re-authenticate |
| `42501: new row violates RLS policy` | RLS blocking insert | Ensure `auth.uid()` matches `user_id` or adjust policy |
| `23505: duplicate key value` | Unique constraint violated | Use `.upsert()` instead of `.insert()` |
| `data` is `null` after insert | Missing `.select()` | Chain `.select()` after `.insert()` / `.update()` |

## Resources
- [Supabase JS Select](https://supabase.com/docs/reference/javascript/select)
- [Supabase JS Insert](https://supabase.com/docs/reference/javascript/insert)
- [Supabase JS Update](https://supabase.com/docs/reference/javascript/update)
- [Supabase JS Delete](https://supabase.com/docs/reference/javascript/delete)
- [Database Migrations](https://supabase.com/docs/guides/deployment/database-migrations)

## Next Steps
Proceed to `supabase-local-dev-loop` for development workflow setup.
