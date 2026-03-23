---
name: supabase-sdk-patterns
description: |
  Apply production-ready Supabase SDK patterns for TypeScript and Python projects.
  Use when implementing queries, auth, realtime, storage, or RPC calls
  with @supabase/supabase-js or supabase-py.
  Trigger with phrases like "supabase SDK patterns", "supabase query",
  "supabase typescript", "supabase python", "supabase client setup",
  "supabase realtime", "supabase auth", "supabase storage".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, cursor
tags: [saas, supabase, typescript, python, sdk, patterns]
---

# Supabase SDK Patterns

## Overview

Production patterns for `@supabase/supabase-js` v2 and `supabase-py`. Every Supabase query returns `{ data, error }` — never assume success. This skill covers client initialization, CRUD with filters, auth, realtime subscriptions, storage, RPC, and the Python equivalent for each pattern.

## Prerequisites

- Supabase project with URL and anon key (or service role key for server-side)
- `@supabase/supabase-js` v2 installed (TypeScript) or `supabase` pip package (Python)
- TypeScript projects: generated database types via `supabase gen types typescript`

## Instructions

### Step 1: Initialize a Typed Singleton Client

Create one client instance and reuse it. Never call `createClient` per-request.

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

### Step 2: Query, Filter, and Mutate Data

**All queries return `{ data, error }`.** Always destructure and check error before using data.

**Select with filters and chaining:**

```typescript
const { data, error } = await getSupabase()
  .from('users')
  .select('id, name, email')
  .eq('active', true)       // WHERE active = true
  .gt('age', 18)            // AND age > 18
  .ilike('name', '%john%')  // AND name ILIKE '%john%'
  .in('role', ['admin', 'editor'])  // AND role IN (...)
  .order('name', { ascending: true })
  .limit(10)

if (error) throw error
// data is typed as Pick<User, 'id' | 'name' | 'email'>[]
```

**Insert with select (return the inserted row):**

```typescript
const { data: newUser, error } = await getSupabase()
  .from('users')
  .insert({ name: 'Alice', email: 'alice@example.com', active: true })
  .select()       // Without .select(), data is null
  .single()       // Unwrap from array to single object

if (error) throw error
// newUser is the full row with server-generated id, created_at, etc.
```

**Upsert (insert or update on conflict):**

```typescript
const { data, error } = await getSupabase()
  .from('users')
  .upsert(
    { email: 'alice@example.com', name: 'Alice Updated' },
    { onConflict: 'email' }   // Match on unique column
  )
  .select()
  .single()
```

**Update and delete:**

```typescript
// Update
const { data, error } = await getSupabase()
  .from('users')
  .update({ active: false })
  .eq('id', userId)
  .select()
  .single()

// Delete
const { error } = await getSupabase()
  .from('users')
  .delete()
  .eq('id', userId)
```

**RPC — call a Postgres function:**

```typescript
const { data, error } = await getSupabase()
  .rpc('my_function', { arg1: 'value', arg2: 42 })

if (error) throw error
// data is the function's return value
```

**Complete filter reference:**

| Filter | SQL Equivalent | Example |
|--------|---------------|---------|
| `.eq(col, val)` | `= val` | `.eq('status', 'active')` |
| `.neq(col, val)` | `!= val` | `.neq('role', 'guest')` |
| `.gt(col, val)` | `> val` | `.gt('age', 18)` |
| `.gte(col, val)` | `>= val` | `.gte('score', 90)` |
| `.lt(col, val)` | `< val` | `.lt('price', 100)` |
| `.lte(col, val)` | `<= val` | `.lte('quantity', 0)` |
| `.like(col, pat)` | `LIKE pat` | `.like('name', '%son')` |
| `.ilike(col, pat)` | `ILIKE pat` | `.ilike('email', '%@gmail%')` |
| `.is(col, val)` | `IS val` | `.is('deleted_at', null)` |
| `.in(col, arr)` | `IN (...)` | `.in('id', [1, 2, 3])` |
| `.contains(col, val)` | `@> val` | `.contains('tags', ['urgent'])` |
| `.range(from, to)` | `OFFSET/LIMIT` | `.range(0, 9)` (first 10 rows) |

**Python equivalent:**

```python
# Select with filters
result = get_supabase() \
    .table('users') \
    .select('id, name, email') \
    .eq('active', True) \
    .gt('age', 18) \
    .order('name') \
    .limit(10) \
    .execute()

if result.data is None:
    raise Exception(f"Query failed")

# Insert
result = get_supabase().table('users').insert({
    "name": "Alice", "email": "alice@example.com"
}).execute()

# Upsert
result = get_supabase().table('users').upsert({
    "email": "alice@example.com", "name": "Alice Updated"
}).execute()

# RPC
result = get_supabase().rpc('my_function', {"arg1": "value"}).execute()
```

### Step 3: Auth, Realtime, and Storage

**Auth — sign up, sign in, get session:**

```typescript
// Sign up
const { data, error } = await getSupabase().auth.signUp({
  email: 'user@example.com',
  password: 'securepassword',
})

// Sign in with password
const { data, error } = await getSupabase().auth.signInWithPassword({
  email: 'user@example.com',
  password: 'securepassword',
})
// data.session contains access_token, refresh_token
// data.user contains user metadata

// Get current session
const { data: { session } } = await getSupabase().auth.getSession()
if (!session) {
  // User is not authenticated
}

// Sign out
await getSupabase().auth.signOut()

// Listen for auth changes
getSupabase().auth.onAuthStateChange((event, session) => {
  // event: 'SIGNED_IN' | 'SIGNED_OUT' | 'TOKEN_REFRESHED' | ...
  console.log('Auth event:', event, session?.user?.email)
})
```

**Realtime — subscribe to database changes:**

```typescript
const channel = getSupabase()
  .channel('room-messages')
  .on(
    'postgres_changes',
    {
      event: '*',           // 'INSERT' | 'UPDATE' | 'DELETE' | '*'
      schema: 'public',
      table: 'messages',
      filter: 'room_id=eq.42',  // Optional row-level filter
    },
    (payload) => {
      console.log('Change:', payload.eventType, payload.new)
      // payload.new = the new row (INSERT/UPDATE)
      // payload.old = the old row (UPDATE/DELETE)
    }
  )
  .subscribe((status) => {
    // status: 'SUBSCRIBED' | 'CLOSED' | 'CHANNEL_ERROR'
    console.log('Subscription status:', status)
  })

// Clean up when done
await getSupabase().removeChannel(channel)
```

**Storage — upload, download, get public URL:**

```typescript
// Upload a file
const { data, error } = await getSupabase().storage
  .from('avatars')          // bucket name
  .upload('users/avatar.png', file, {
    cacheControl: '3600',
    upsert: true,           // overwrite if exists
    contentType: 'image/png',
  })

// Download a file
const { data, error } = await getSupabase().storage
  .from('avatars')
  .download('users/avatar.png')
// data is a Blob

// Get public URL (no auth required if bucket is public)
const { data: { publicUrl } } = getSupabase().storage
  .from('avatars')
  .getPublicUrl('users/avatar.png')

// Get signed URL (time-limited access for private buckets)
const { data, error } = await getSupabase().storage
  .from('documents')
  .createSignedUrl('reports/q4.pdf', 3600)  // expires in 1 hour
// data.signedUrl
```

## Output

After applying these patterns you will have:

- Type-safe singleton client with `Database` generics
- CRUD operations using the full filter chain (eq, gt, in, ilike, etc.)
- Insert-with-select and upsert patterns that return the affected row
- Auth flows for sign-up, sign-in, session management, and state listeners
- Realtime subscriptions with row-level filtering and cleanup
- Storage upload/download with signed URLs for private buckets
- Python equivalents for all query patterns

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

// Only safe to use data after error check
```

| Error Code | Meaning | What to Do |
|------------|---------|------------|
| `PGRST116` | No rows found (`.single()`) | Return null or 404, don't throw |
| `23505` | Unique constraint violation | Use `.upsert()` or show conflict error |
| `42501` | RLS policy violation | Check auth state and RLS policies |
| `PGRST000` | Connection error | Retry with exponential backoff |
| `42P01` | Table does not exist | Verify table name and run migrations |
| `23503` | Foreign key violation | Ensure referenced row exists first |
| `42703` | Column does not exist | Check column name, regenerate types |

## Examples

**Service layer pattern (recommended for production):**

```typescript
// services/user-service.ts
import type { Database } from '../lib/database.types'

type User = Database['public']['Tables']['users']['Row']
type UserInsert = Database['public']['Tables']['users']['Insert']

export const UserService = {
  async getById(id: string): Promise<User | null> {
    const { data, error } = await getSupabase()
      .from('users')
      .select('*')
      .eq('id', id)
      .single()

    if (error?.code === 'PGRST116') return null  // Not found
    if (error) throw error
    return data
  },

  async search(query: string, limit = 20): Promise<User[]> {
    const { data, error } = await getSupabase()
      .from('users')
      .select('id, name, email, avatar_url')
      .or(`name.ilike.%${query}%,email.ilike.%${query}%`)
      .order('name')
      .limit(limit)

    if (error) throw error
    return data
  },

  async createOrUpdate(user: UserInsert): Promise<User> {
    const { data, error } = await getSupabase()
      .from('users')
      .upsert(user, { onConflict: 'email' })
      .select()
      .single()

    if (error) throw error
    return data
  },
}
```

**Pagination helper:**

```typescript
async function paginate<T>(
  table: string,
  select: string,
  { page = 1, pageSize = 20, orderBy = 'id' } = {}
) {
  const from = (page - 1) * pageSize
  const to = from + pageSize - 1

  const { data, error, count } = await getSupabase()
    .from(table)
    .select(select, { count: 'exact' })
    .order(orderBy)
    .range(from, to)

  if (error) throw error
  return {
    data: data as T[],
    page,
    pageSize,
    total: count ?? 0,
    totalPages: Math.ceil((count ?? 0) / pageSize),
  }
}

// Usage
const result = await paginate<User>('users', 'id, name, email', { page: 2 })
```

## Resources

- [Supabase JS Client Reference](https://supabase.com/docs/reference/javascript/initializing)
- [TypeScript Support & Type Generation](https://supabase.com/docs/reference/javascript/typescript-support)
- [Supabase Auth Reference](https://supabase.com/docs/reference/javascript/auth-signup)
- [Realtime Guide](https://supabase.com/docs/guides/realtime)
- [Storage Guide](https://supabase.com/docs/guides/storage)
- [Python Client Reference](https://supabase.com/docs/reference/python/initializing)

## Next Steps

For database schema design, see `supabase-schema-from-requirements`. For auth deep-dive with RLS policies, see `supabase-install-auth`. For realtime architecture patterns, see `supabase-auth-storage-realtime-core`.
