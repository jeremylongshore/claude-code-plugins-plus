# Supabase Hello World — Complete Examples

Runnable end-to-end scripts in TypeScript and Python. Each performs the full
insert-then-select round-trip against the `todos` table created in Step 1 of
the workflow (see [implementation.md](implementation.md)).

## TypeScript (Complete Script)

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

## Python

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
