---
name: supabase-hello-world
description: |
  Run your first Supabase query — insert a row and read it back.
  Use when starting a new Supabase project, verifying your connection works,
  or learning the basic insert-then-select pattern with @supabase/supabase-js.
  Trigger with phrases like "supabase hello world", "first supabase query",
  "supabase quick start", "test supabase connection", "supabase insert and select".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, database, getting-started]
---

# Supabase Hello World — First Query

## Overview

Execute your first real Supabase query: create a `todos` table in the dashboard, insert a row with the JS client, and read it back. This validates that your project URL, anon key, and Row Level Security are configured correctly before you build anything else.

## Prerequisites

- Completed `supabase-install-auth` setup (project URL + anon key in `.env`)
- `@supabase/supabase-js` v2+ installed (`npm install @supabase/supabase-js`)
- A Supabase project at [supabase.com/dashboard](https://supabase.com/dashboard)

## Instructions

### Step 1: Create the `todos` Table

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

### Step 2: Insert a Row

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

### Step 3: Read It Back

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

## Output

- `todos` table created with RLS enabled
- One row inserted via the JS client
- Same row read back with `.select('*')`
- Dashboard confirms the data round-trip

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `relation "public.todos" does not exist` | Table not created | Run the Step 1 SQL in the dashboard SQL Editor |
| `new row violates row-level security policy` | RLS blocks the insert | Add the permissive insert policy from Step 1 |
| `Invalid API key` | Wrong anon key in `.env` | Copy from Settings > API in the dashboard |
| `FetchError: request to https://... failed` | Wrong project URL | Verify `SUPABASE_URL` matches dashboard URL |
| `data` is `null` after insert | Missing `.select()` chain | Add `.select()` after `.insert()` |
| Empty array returned from select | RLS blocks reads | Add the select policy from Step 1 |

## Examples

### TypeScript (Complete Script)

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

async function helloSupabase() {
  // Insert
  const { data: inserted, error: insertErr } = await supabase
    .from('todos')
    .insert({ task: 'Hello from TypeScript!' })
    .select()
    .single()

  if (insertErr) throw new Error(`Insert: ${insertErr.message}`)
  console.log('Inserted:', inserted)

  // Read back
  const { data: rows, error: selectErr } = await supabase
    .from('todos')
    .select('*')
    .order('inserted_at', { ascending: false })
    .limit(5)

  if (selectErr) throw new Error(`Select: ${selectErr.message}`)
  console.log('Recent todos:', rows)
}

helloSupabase().catch(console.error)
```

### Python

```python
from supabase import create_client
import os

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_ANON_KEY"]
)

# Insert a row
result = supabase.table("todos").insert({"task": "Hello from Python!"}).execute()
print("Inserted:", result.data)
# [{"id": 2, "task": "Hello from Python!", "is_complete": False, ...}]

# Read it back
result = supabase.table("todos").select("*").execute()
print("All todos:", result.data)
```

Install the Python client with: `pip install supabase`

## Resources

- [Supabase Getting Started](https://supabase.com/docs/guides/getting-started)
- [JS Client — Insert](https://supabase.com/docs/reference/javascript/insert)
- [JS Client — Select](https://supabase.com/docs/reference/javascript/select)
- [Python Client](https://supabase.com/docs/reference/python/introduction)
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)

## Next Steps

Proceed to `supabase-local-dev-loop` for local development workflow with the Supabase CLI.
