---
name: supabase-known-pitfalls
description: |
  Identify and fix Supabase anti-patterns: service key exposure, missing RLS,
  N+1 queries, select(*), missing error handling, and other common mistakes.
  Use when reviewing Supabase code, onboarding developers,
  or auditing existing integrations.
  Trigger with phrases like "supabase mistakes", "supabase anti-patterns",
  "supabase pitfalls", "supabase code review", "what not to do supabase".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, code-review, anti-patterns]

---
# Supabase Known Pitfalls

## Overview
The most common Supabase anti-patterns ranked by severity (security > data integrity > performance > maintainability), with the correct pattern for each. Use as a code review checklist or onboarding reference.

## Prerequisites
- Access to Supabase codebase for review
- Understanding of RLS and Supabase SDK

## Instructions

### CRITICAL: Security Pitfalls

#### Pitfall 1: Service Role Key in Client Code

```typescript
// BAD: service role key exposed to the browser
const supabase = createClient(url, process.env.NEXT_PUBLIC_SERVICE_ROLE_KEY!)
// This key bypasses ALL RLS. Anyone can read/write/delete everything.

// GOOD: anon key on client side
const supabase = createClient(url, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
// Anon key respects RLS policies.
```

**Detection**: `grep -rn 'SERVICE_ROLE' --include="*.tsx" --include="*.jsx" src/`

#### Pitfall 2: Tables Without RLS

```sql
-- BAD: table created without enabling RLS
create table public.user_data (
  id uuid primary key,
  email text,
  ssn text  -- PII exposed to anyone with the anon key!
);

-- GOOD: always enable RLS immediately
create table public.user_data (
  id uuid primary key,
  email text,
  ssn text
);
alter table public.user_data enable row level security;
-- Then add appropriate policies
```

**Detection**:
```sql
select tablename from pg_tables
where schemaname = 'public' and rowsecurity = false;
```

#### Pitfall 3: Overly Permissive RLS

```sql
-- BAD: allows any authenticated user to read ALL records
create policy "Authenticated can read all" on public.messages
  for select using (auth.uid() is not null);
-- Every logged-in user sees every message!

-- GOOD: scope to user's own data or organization
create policy "Users read own messages" on public.messages
  for select using (
    sender_id = auth.uid() or recipient_id = auth.uid()
  );
```

### HIGH: Data Integrity Pitfalls

#### Pitfall 4: Ignoring Error Responses

```typescript
// BAD: not checking for errors
const { data } = await supabase.from('orders').insert(order).select().single()
// If error occurred, data is null and you proceed with undefined values

// GOOD: always check error
const { data, error } = await supabase.from('orders').insert(order).select().single()
if (error) {
  console.error('Insert failed:', error.code, error.message)
  throw new Error(`Failed to create order: ${error.message}`)
}
```

#### Pitfall 5: Missing .select() After Mutations

```typescript
// BAD: insert/update/delete return NO data by default
const { data } = await supabase.from('todos').insert({ title: 'New' })
console.log(data)  // null! Not what you expected.

// GOOD: chain .select() to get the result back
const { data } = await supabase.from('todos').insert({ title: 'New' }).select().single()
console.log(data)  // { id: 1, title: 'New', ... }
```

#### Pitfall 6: .single() on Zero-or-Many Results

```typescript
// BAD: .single() throws error if 0 or 2+ rows match
const { data, error } = await supabase
  .from('profiles')
  .select('*')
  .eq('username', search)
  .single()
// error: PGRST116 if no match, PGRST200 if multiple matches

// GOOD: use .maybeSingle() when result is optional
const { data } = await supabase
  .from('profiles')
  .select('*')
  .eq('username', search)
  .maybeSingle()
// data is null if no match, no error thrown
```

### MEDIUM: Performance Pitfalls

#### Pitfall 7: select('*') Everywhere

```typescript
// BAD: fetches ALL columns including large text/jsonb fields
const { data } = await supabase.from('posts').select('*')

// GOOD: specify only needed columns
const { data } = await supabase.from('posts').select('id, title, created_at')
// Reduces bandwidth, prevents leaking sensitive columns, faster serialization
```

#### Pitfall 8: N+1 Queries

```typescript
// BAD: one query per project to get tasks
const projects = await getProjects()
for (const project of projects) {
  const { data: tasks } = await supabase
    .from('tasks')
    .select('*')
    .eq('project_id', project.id)
  project.tasks = tasks
}
// 1 + N queries where N is the number of projects

// GOOD: use a join (single query)
const { data } = await supabase
  .from('projects')
  .select(`
    id, name,
    tasks (id, title, status)
  `)
// 1 query with embedded join

// ALSO GOOD: batch with .in()
const { data: tasks } = await supabase
  .from('tasks')
  .select('id, title, project_id')
  .in('project_id', projects.map(p => p.id))
```

#### Pitfall 9: Missing Indexes on Foreign Keys

```sql
-- BAD: foreign key without index (slow joins and RLS)
create table public.tasks (
  id uuid primary key,
  project_id uuid references public.projects(id)  -- no index!
);

-- GOOD: always index foreign key columns
create table public.tasks (
  id uuid primary key,
  project_id uuid references public.projects(id)
);
create index idx_tasks_project_id on public.tasks(project_id);
```

#### Pitfall 10: Synchronous Auth Check on Every Request

```typescript
// BAD: hits Supabase Auth API on every single request
async function getUser(req: Request) {
  const { data: { user } } = await supabase.auth.getUser()  // network call
  return user
}

// GOOD: verify JWT locally, only call getUser when needed
async function getUser(req: Request) {
  const { data: { session } } = await supabase.auth.getSession()  // local
  // getUser() only when you need verified, fresh user data
  return session?.user
}
```

### LOW: Maintainability Pitfalls

#### Pitfall 11: Not Using Generated Types

```typescript
// BAD: manual types that drift from schema
interface Todo { id: number; title: string; done: boolean }

// GOOD: use generated types
import type { Database } from './database.types'
type Todo = Database['public']['Tables']['todos']['Row']
// Run: supabase gen types typescript --linked > lib/database.types.ts
```

#### Pitfall 12: Creating Multiple Client Instances

```typescript
// BAD: new client in every file
// utils/auth.ts
const supabase = createClient(url, key)
// utils/data.ts
const supabase = createClient(url, key)  // separate instance!

// GOOD: singleton exported from one file
// lib/supabase.ts
export const supabase = createClient(url, key)
// Import everywhere: import { supabase } from '../lib/supabase'
```

### Code Review Checklist

- [ ] No `SERVICE_ROLE_KEY` in client-side code or `NEXT_PUBLIC_*` vars
- [ ] RLS enabled on all tables (`pg_tables.rowsecurity = true`)
- [ ] All Supabase calls check `error` before using `data`
- [ ] `.select()` chained after `.insert()`, `.update()`, `.upsert()`
- [ ] Column names specified in `.select()` (no `select('*')`)
- [ ] Foreign key columns have indexes
- [ ] No N+1 query patterns (use joins or `.in()`)
- [ ] Single client instance (singleton pattern)
- [ ] Generated types used (not manual interface definitions)
- [ ] `.maybeSingle()` used for optional lookups

## Output
- Anti-patterns identified with severity classification
- Each pitfall paired with the correct Supabase pattern
- Code review checklist for PR reviews
- Detection commands for automated scanning

## Resources
- [Supabase Security](https://supabase.com/docs/guides/security)
- [Supabase Performance](https://supabase.com/docs/guides/database/inspect)
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [TypeScript Support](https://supabase.com/docs/reference/javascript/typescript-support)

## Next Steps
This completes the Supabase skill pack. See `supabase-install-auth` to start a new project.
