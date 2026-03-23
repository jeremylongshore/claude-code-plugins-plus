---
name: supabase-known-pitfalls
description: |
  Avoid and fix the most common Supabase mistakes: exposing service_role key
  in client bundles, forgetting to enable RLS, not using connection pooling
  in serverless, .single() throwing on empty results, missing .select() after
  insert/update, not destructuring { data, error }, creating multiple client
  instances, and not using generated types.
  Use when reviewing Supabase code, onboarding developers, auditing an
  existing project, or debugging unexpected behavior.
  Trigger with phrases like "supabase mistakes", "supabase anti-patterns",
  "supabase pitfalls", "supabase code review", "supabase gotchas",
  "supabase debugging", "what not to do supabase", "supabase common errors".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, anti-patterns, code-review, debugging, security, pitfalls]
---

# Supabase Known Pitfalls

## Overview

The twelve most common Supabase mistakes, ranked by severity: **security** (service_role exposure, missing RLS, permissive policies), **data integrity** (ignoring `{ data, error }`, missing `.select()` after mutations, `.single()` on optional results), **performance** (`select('*')`, N+1 queries, missing FK indexes, synchronous auth checks), and **maintainability** (no generated types, multiple client instances, hardcoded connection strings). Each pitfall shows the broken code, explains why it fails, and provides the correct pattern using `createClient` from `@supabase/supabase-js`.

## Prerequisites

- Access to a Supabase project codebase for review
- `@supabase/supabase-js` v2+ installed
- Basic understanding of Row Level Security (RLS)

## Step 1 — Security Pitfalls (Critical)

These mistakes can expose all your data to any user with browser dev tools.

### Pitfall 1: Exposing service_role Key in Client Code

```typescript
// BAD: service_role key in a NEXT_PUBLIC_ variable — shipped to every browser
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY!  // CATASTROPHIC
)
// This key bypasses ALL RLS. Anyone can:
// - Read every row in every table
// - Delete the entire database
// - Create admin users
// - Access every file in storage

// CORRECT: anon key on client, service_role only on server
// Client (browser):
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!  // respects RLS
)

// Server only (API routes, server actions):
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,  // NO NEXT_PUBLIC_ prefix
  { auth: { autoRefreshToken: false, persistSession: false } }
)
```

**Detection:**
```bash
# Find service_role references in client-side files
grep -rn 'SERVICE_ROLE' --include="*.tsx" --include="*.jsx" --include="*.ts" src/ app/ components/ pages/
# Find NEXT_PUBLIC_ + SERVICE_ROLE combination
grep -rn 'NEXT_PUBLIC.*SERVICE_ROLE' .env* *.ts *.tsx
```

### Pitfall 2: Tables Without RLS Enabled

```sql
-- BAD: table created without enabling RLS
CREATE TABLE public.medical_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id uuid REFERENCES auth.users(id),
  diagnosis text,
  ssn text  -- PII fully exposed to anyone with the anon key!
);
-- With RLS disabled, the anon key can read EVERY row via the PostgREST API

-- CORRECT: always enable RLS immediately after CREATE TABLE
CREATE TABLE public.medical_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id uuid REFERENCES auth.users(id),
  diagnosis text,
  ssn text
);
ALTER TABLE public.medical_records ENABLE ROW LEVEL SECURITY;

-- Then add policies for legitimate access
CREATE POLICY "patients_read_own" ON public.medical_records
  FOR SELECT USING (patient_id = auth.uid());
```

**Detection:**
```sql
-- Find all tables without RLS (run in SQL Editor)
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'public'
AND rowsecurity = false
AND tablename NOT LIKE '\_%';
```

### Pitfall 3: Overly Permissive RLS Policies

```sql
-- BAD: lets any authenticated user read ALL messages
CREATE POLICY "anyone_can_read" ON public.messages
  FOR SELECT USING (auth.uid() IS NOT NULL);
-- Every logged-in user sees every other user's private messages

-- BAD: lets any authenticated user update ANY row
CREATE POLICY "anyone_can_update" ON public.profiles
  FOR UPDATE USING (auth.uid() IS NOT NULL);
-- Users can edit each other's profiles

-- CORRECT: scope to the user's own data
CREATE POLICY "read_own_messages" ON public.messages
  FOR SELECT USING (
    sender_id = auth.uid() OR recipient_id = auth.uid()
  );

CREATE POLICY "update_own_profile" ON public.profiles
  FOR UPDATE USING (id = auth.uid());
```

### Pitfall 4: Not Using Connection Pooling in Serverless

```typescript
// BAD: direct connection string in a serverless function
// Each Lambda/Edge invocation opens a new connection — exhausts pool in minutes
const connectionString = 'postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres'

// CORRECT: use the pooled connection string (Supavisor, port 6543)
const connectionString = 'postgresql://postgres.xxx:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres'
// Transaction mode: shares connections across requests
// Required for serverless (Vercel, Netlify, Cloudflare Workers, AWS Lambda)
```

## Step 2 — Data Integrity Pitfalls (High)

These mistakes cause silent data loss, null pointer errors, and inconsistent state.

### Pitfall 5: Not Handling { data, error }

```typescript
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(url, key)

// BAD: destructuring only data — errors silently ignored
const { data } = await supabase.from('orders').insert(order).select().single()
console.log(data.id)  // TypeError: Cannot read property 'id' of null
// The insert failed (maybe RLS blocked it), data is null, error has the reason

// CORRECT: always check error before using data
const { data, error } = await supabase.from('orders').insert(order).select().single()
if (error) {
  console.error('Insert failed:', error.code, error.message, error.details)
  throw new Error(`Order creation failed: ${error.message}`)
}
// Now data is guaranteed to be non-null
console.log(data.id)
```

### Pitfall 6: Missing .select() After Insert/Update/Upsert

```typescript
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(url, key)

// BAD: insert without .select() returns NO data
const { data } = await supabase.from('todos').insert({ title: 'Buy milk' })
console.log(data)  // null! Not the inserted row.
// Supabase mutations return null by default (like SQL INSERT without RETURNING)

// CORRECT: chain .select() to get the inserted/updated row back
const { data, error } = await supabase
  .from('todos')
  .insert({ title: 'Buy milk' })
  .select('id, title, is_complete, created_at')  // like SQL RETURNING
  .single()

if (error) throw new Error(`Insert failed: ${error.message}`)
console.log(data)  // { id: '...', title: 'Buy milk', is_complete: false, ... }
```

### Pitfall 7: .single() on Empty or Multiple Results

```typescript
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(url, key)

// BAD: .single() throws PGRST116 when no rows match
const { data, error } = await supabase
  .from('profiles')
  .select('id, username, avatar_url')
  .eq('username', searchTerm)
  .single()
// error: { code: 'PGRST116', message: 'JSON object requested, multiple (or no) rows returned' }
// This is an ERROR, not just null — it breaks your flow

// BAD: .single() also throws when MULTIPLE rows match (PGRST200)

// CORRECT: use .maybeSingle() for 0-or-1 results
const { data, error } = await supabase
  .from('profiles')
  .select('id, username, avatar_url')
  .eq('username', searchTerm)
  .maybeSingle()
// data is null if no match (no error thrown)
// data is the row if exactly one match
// error only if 2+ rows match

// RULE OF THUMB:
// .single()      — use ONLY when you KNOW exactly 1 row exists (e.g., by primary key)
// .maybeSingle() — use when 0 or 1 rows might match (lookups by unique field)
// neither        — use when you expect an array of results
```

## Step 3 — Performance and Maintainability Pitfalls (Medium/Low)

### Pitfall 8: select('*') Everywhere

```typescript
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(url, key)

// BAD: fetches ALL columns including large text/jsonb/bytea fields
const { data } = await supabase.from('posts').select('*')
// Problems:
// 1. Transfers unnecessary data (slower, more bandwidth)
// 2. May leak sensitive columns (SSN, internal notes, hashed passwords)
// 3. No TypeScript autocompletion — type is too broad
// 4. Cannot benefit from covering indexes

// CORRECT: specify only the columns you need
const { data } = await supabase
  .from('posts')
  .select('id, title, slug, excerpt, published_at, author:profiles(name, avatar_url)')
// Benefits: smaller payload, typed results, index-friendly, no data leakage
```

### Pitfall 9: N+1 Query Pattern

```typescript
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(url, key)

// BAD: 1 query to get projects + N queries to get tasks per project
const { data: projects } = await supabase.from('projects').select('id, name')

for (const project of projects ?? []) {
  const { data: tasks } = await supabase
    .from('tasks')
    .select('id, title, status')
    .eq('project_id', project.id)
  project.tasks = tasks  // N additional queries!
}
// Total: 1 + N queries (if you have 50 projects, that's 51 queries)

// CORRECT: use PostgREST embedded joins (single query)
const { data } = await supabase
  .from('projects')
  .select(`
    id, name,
    tasks (id, title, status)
  `)
// Total: 1 query with automatic JOIN
// PostgREST detects the foreign key and embeds the related data

// ALSO CORRECT: batch with .in() for non-FK relationships
const projectIds = projects?.map(p => p.id) ?? []
const { data: allTasks } = await supabase
  .from('tasks')
  .select('id, title, status, project_id')
  .in('project_id', projectIds)
// Total: 2 queries regardless of N
```

### Pitfall 10: Missing Indexes on Foreign Key Columns

```sql
-- BAD: foreign key without index
CREATE TABLE public.comments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id uuid REFERENCES public.posts(id),  -- no index!
  author_id uuid REFERENCES auth.users(id),  -- no index!
  body text,
  created_at timestamptz DEFAULT now()
);
-- Every query filtering by post_id or author_id does a sequential scan
-- RLS policies checking these columns also become slow

-- CORRECT: always index foreign key columns
CREATE TABLE public.comments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id uuid REFERENCES public.posts(id),
  author_id uuid REFERENCES auth.users(id),
  body text,
  created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_comments_post_id ON public.comments(post_id);
CREATE INDEX idx_comments_author_id ON public.comments(author_id);
```

**Detection:**
```sql
-- Find foreign keys without indexes
SELECT
  tc.table_name,
  kcu.column_name,
  'CREATE INDEX idx_' || tc.table_name || '_' || kcu.column_name
    || ' ON public.' || tc.table_name || '(' || kcu.column_name || ');' AS fix
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
LEFT JOIN pg_indexes pi
  ON pi.tablename = tc.table_name
  AND pi.indexdef LIKE '%' || kcu.column_name || '%'
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
AND pi.indexname IS NULL;
```

### Pitfall 11: Creating Multiple Client Instances

```typescript
// BAD: new client in every file — wastes memory, breaks auth state
// utils/auth.ts
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(url, key)  // instance 1

// utils/data.ts
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(url, key)  // instance 2 — separate auth session!

// components/Profile.tsx
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(url, key)  // instance 3 — yet another session

// Problems:
// - Auth state is not shared between instances
// - Realtime subscriptions multiply
// - Memory overhead from duplicate GoTrue instances
// - Session refresh happens 3x unnecessarily

// CORRECT: singleton pattern — one instance, imported everywhere
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

export const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Every file imports the same instance:
// import { supabase } from '@/lib/supabase'
```

### Pitfall 12: Not Using Generated Types

```typescript
// BAD: manual types that drift from the actual database schema
interface Todo {
  id: number        // wrong! Supabase uses uuid by default
  title: string
  done: boolean     // wrong! Column is actually called is_complete
  createdAt: string // wrong! Column is actually called created_at
}

// The compiler doesn't catch any of these mismatches.
// You get runtime errors instead of compile-time errors.

// CORRECT: generate types from your database schema
// Step 1: Generate
// npx supabase gen types typescript --linked > lib/database.types.ts

// Step 2: Use the generated types
import type { Database } from './database.types'

type Todo = Database['public']['Tables']['todos']['Row']
// { id: string, title: string, is_complete: boolean, created_at: string, user_id: string }

type TodoInsert = Database['public']['Tables']['todos']['Insert']
// { title: string, user_id?: string, is_complete?: boolean }

// Step 3: Pass the Database type to createClient
import { createClient } from '@supabase/supabase-js'

const supabase = createClient<Database>(url, key)

// Now all queries are fully typed:
const { data } = await supabase.from('todos').select('id, title, is_complete')
// data is typed as { id: string; title: string; is_complete: boolean }[] | null

// Automate type generation in CI:
// Add to package.json scripts: "types:supabase": "supabase gen types typescript --linked > lib/database.types.ts"
```

## Output

- Security pitfalls identified: service_role exposure, missing RLS, permissive policies, no connection pooling
- Data integrity pitfalls fixed: `{ data, error }` handling, `.select()` after mutations, `.maybeSingle()` usage
- Performance pitfalls resolved: column-specific selects, JOIN queries, FK indexes
- Maintainability improved: singleton client, generated types
- Detection commands for automated scanning of each pitfall

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `PGRST116: JSON object requested, multiple (or no) rows returned` | Used `.single()` when 0 or 2+ rows match | Use `.maybeSingle()` for optional lookups |
| `data` is `null` after insert | Missing `.select()` chain | Add `.select('column1, column2')` after `.insert()` |
| `TypeError: Cannot read property of null` | Destructured only `data`, ignoring `error` | Always destructure `{ data, error }` and check error first |
| `too many connections for role` | Direct connection from serverless | Use pooled connection string (port 6543) |
| `permission denied for table` | RLS blocking access, no matching policy | Check RLS policies match the authenticated user's JWT claims |
| `relation does not exist` | Table name typo, not caught at compile time | Use generated types for compile-time validation |

## Examples

### Quick Security Audit

```bash
# Check for all three critical security pitfalls in one pass
echo "=== Pitfall 1: Service role in client code ==="
grep -rn 'SERVICE_ROLE' --include="*.tsx" --include="*.ts" src/ app/ components/ 2>/dev/null || echo "Clean"

echo "=== Pitfall 2: Tables without RLS ==="
# Run in SQL Editor:
# SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND rowsecurity = false;

echo "=== Pitfall 3: Overly permissive policies ==="
# Run in SQL Editor:
# SELECT tablename, policyname FROM pg_policies WHERE qual = 'true' AND cmd != 'r';
```

### Code Review Checklist

```markdown
## Supabase PR Review Checklist

### Security
- [ ] No `SERVICE_ROLE_KEY` in client-side code or `NEXT_PUBLIC_*` vars
- [ ] RLS enabled on all new tables
- [ ] RLS policies scope to `auth.uid()` or org membership (no `USING (true)` for writes)

### Data Integrity
- [ ] All Supabase calls destructure `{ data, error }` and check error
- [ ] `.select()` chained after `.insert()`, `.update()`, `.upsert()`
- [ ] `.maybeSingle()` used for optional lookups (not `.single()`)

### Performance
- [ ] Column names specified in `.select()` (no `select('*')`)
- [ ] No N+1 patterns (use embedded joins or `.in()`)
- [ ] Foreign key columns have indexes

### Maintainability
- [ ] Single `createClient` instance (singleton pattern)
- [ ] Generated types used (not manual interfaces)
- [ ] Pooled connection string for serverless deployments
```

## Resources

- [Supabase Auth: Securing Your Data](https://supabase.com/docs/guides/auth#securing-your-data)
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [TypeScript Support](https://supabase.com/docs/reference/javascript/typescript-support)
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Supabase JavaScript Client Reference](https://supabase.com/docs/reference/javascript/select)
- [PostgREST Error Codes](https://postgrest.org/en/stable/references/errors.html)

## Next Steps

This completes the Supabase pitfalls reference. To start a new project with best practices from day one, see `supabase-hello-world`.
