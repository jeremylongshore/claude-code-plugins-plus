# Supabase Hello World — Full Implementation

Annotated, step-by-step code for the insert-then-select round-trip. The
SKILL.md body carries the lean skeleton; this file carries the complete,
commented walkthrough for each step.

## Step 1: Create the `todos` Table

Open your Supabase dashboard SQL Editor and run:

```sql
-- Create a simple todos table
create table public.todos (
  id bigint generated always as identity primary key,
  task text not null,
  is_complete boolean default false,
  inserted_at timestamptz default now()
);

-- Enable Row Level Security (required for anon key access)
alter table public.todos enable row level security;

-- Allow anyone with the anon key to read and insert
-- (permissive for hello-world; lock down before production)
create policy "Allow public read" on public.todos
  for select using (true);

create policy "Allow public insert" on public.todos
  for insert with check (true);
```

Verify the table appears under **Table Editor** in the dashboard before continuing.

## Step 2: Insert a Row

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// Insert a row and return it with .select()
const { data, error } = await supabase
  .from('todos')
  .insert({ task: 'Hello from Supabase!' })
  .select()

if (error) {
  console.error('Insert failed:', error.message)
  // e.g. "new row violates row-level security policy"
  process.exit(1)
}

console.log('Inserted:', data)
// [{ id: 1, task: "Hello from Supabase!", is_complete: false, inserted_at: "2026-03-22T..." }]
```

Key detail: `.insert()` alone returns `{ data: null }`. You must chain `.select()` to get the inserted row back.

## Step 3: Read It Back

```typescript
// Select all rows from todos
const { data: todos, error: selectError } = await supabase
  .from('todos')
  .select('*')

if (selectError) {
  console.error('Select failed:', selectError.message)
  process.exit(1)
}

console.log('Todos:', todos)
// [{ id: 1, task: "Hello from Supabase!", is_complete: false, inserted_at: "2026-03-22T..." }]

// Verify the round-trip
if (todos && todos.length > 0) {
  console.log('Round-trip verified — row exists in database')
} else {
  console.error('No rows returned. Check RLS policies.')
}
```

Open the **Table Editor** in the Supabase dashboard to visually confirm the row is there.
