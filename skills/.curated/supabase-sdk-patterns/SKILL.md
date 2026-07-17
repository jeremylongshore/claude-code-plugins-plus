---
name: supabase-sdk-patterns
description: |
  Use when implementing Supabase queries, auth, realtime, storage, or RPC calls
  with @supabase/supabase-js or supabase-py and you need production-ready,
  type-safe patterns that always check the { data, error } contract.
  Trigger with phrases like "supabase SDK patterns", "supabase query",
  "supabase typescript", "supabase python", "supabase client setup",
  "supabase realtime", "supabase auth", "supabase storage".
allowed-tools: Read, Write, Edit, Grep
version: 1.53.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- supabase
- typescript
- python
- sdk
- patterns
compatibility: Designed for Claude Code, also compatible with Cursor
---
# Supabase SDK Patterns

## Overview

Production patterns for `@supabase/supabase-js` v2 and `supabase-py`, where every call returns `{ data, error }` and success is never assumed. Covers client initialization, CRUD with filters, auth, realtime, storage, and RPC, with Python equivalents for the query patterns.

## Prerequisites

- Supabase project with URL and anon key (or service role key for server-side)
- `@supabase/supabase-js` v2 installed (TypeScript) or `supabase` pip package (Python)
- TypeScript projects: generated database types via `supabase gen types typescript`

## Instructions

### Step 1: Initialize a typed singleton client

Create one client instance and reuse it. Never call `createClient` per-request — a
singleton preserves the auth session and connection pool.

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

let supabase: ReturnType<typeof createClient<Database>>

export function getSupabase() {
  if (!supabase) {
    supabase = createClient<Database>(
      process.env.SUPABASE_URL!,
      process.env.SUPABASE_ANON_KEY!,
      {
        auth: { autoRefreshToken: true, persistSession: true },
        db: { schema: 'public' },
        global: { headers: { 'x-app-name': 'my-app' } },
      }
    )
  }
  return supabase
}
```

**Python equivalent:**

```python
from supabase import create_client, Client

_client: Client | None = None

def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_ANON_KEY"],
        )
    return _client
```

### Step 2: Query, filter, and mutate data

Destructure `{ data, error }` and check `error` before touching `data`. Chain
filters onto `.from(table).select(...)`; use `.select().single()` after an
insert/upsert to return the affected row. Skeleton:

```typescript
const { data, error } = await getSupabase()
  .from('users')
  .select('id, name, email')
  .eq('active', true)
  .order('name')
  .limit(10)

if (error) throw error
```

For the full CRUD set (insert-with-select, upsert on conflict, update, delete,
RPC), the complete 12-filter reference table, and the Python equivalents, see
[queries and filters](references/queries-and-filters.md).

### Step 3: Auth, realtime, and storage

Auth, realtime channels, and storage all follow the same `{ data, error }`
contract. Auth exposes `signUp` / `signInWithPassword` / `getSession` /
`onAuthStateChange`; realtime subscribes to `postgres_changes` on a channel and
requires `removeChannel` cleanup; storage does `upload` / `download` /
`getPublicUrl` / `createSignedUrl` per bucket. Full walkthroughs with code for
each: see [auth, realtime, and storage](references/auth-realtime-storage.md).

## Output

Applying these patterns yields:

- Type-safe singleton client with `Database` generics
- CRUD operations using the full filter chain (eq, gt, in, ilike, etc.)
- Insert-with-select and upsert patterns that return the affected row
- Auth flows for sign-up, sign-in, session management, and state listeners
- Realtime subscriptions with row-level filtering and cleanup
- Storage upload/download with signed URLs for private buckets
- Python equivalents for the query patterns

## Error Handling

Every Supabase call returns `{ data, error }`. Never skip the error check.

```typescript
const { data, error } = await getSupabase().from('users').select('*')

if (error) {
  // error is a PostgrestError with these fields:
  //   error.message  — human-readable description
  //   error.code     — Postgres error code (e.g., '23505')
  //   error.details  — additional context
  //   error.hint     — suggested fix from Postgres
  console.error(`Query failed [${error.code}]: ${error.message}`)
  throw error
}

// Only safe to use data after the error check
```

| Error Code | Meaning | What to Do |
| ------------ | --------- | ------------ |
| `PGRST116` | No rows found (`.single()`) | Return null or 404, don't throw |
| `23505` | Unique-constraint violation (Postgres duplicate key) | Use `.upsert()` or show conflict error |
| `42501` | RLS policy violation (Postgres insufficient privilege) | Check auth state and RLS policies |
| `PGRST000` | Connection error | Retry with exponential backoff |
| `42P01` | Table does not exist | Verify table name and run migrations |
| `23503` | Foreign key violation | Ensure referenced row exists first |
| `42703` | Column does not exist | Check column name, regenerate types |

## Examples

The recommended production shape is a typed **service layer** that wraps the
client so callers never touch raw queries, plus a **pagination helper** that
returns a page of rows and the total count in one round trip. Both full,
copy-ready implementations are in [service patterns](references/service-patterns.md).

## Resources

- [Supabase JS Client Reference](https://supabase.com/docs/reference/javascript/initializing)
- [TypeScript Support & Type Generation](https://supabase.com/docs/reference/javascript/typescript-support)
- [Supabase Auth Reference](https://supabase.com/docs/reference/javascript/auth-signup)
- [Realtime Guide](https://supabase.com/docs/guides/realtime)
- [Storage Guide](https://supabase.com/docs/guides/storage)
- [Python Client Reference](https://supabase.com/docs/reference/python/initializing)

## Next Steps

For database schema design, see `supabase-schema-from-requirements`. For auth deep-dive with RLS policies, see `supabase-install-auth`. For realtime architecture patterns, see `supabase-auth-storage-realtime-core`.
