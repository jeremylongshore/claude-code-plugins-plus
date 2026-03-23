---
name: supabase-common-errors
description: |
  Diagnose and fix Supabase errors across PostgREST, PostgreSQL, Auth, Storage, and Realtime.
  Use when encountering error codes like PGRST301, 42501, 23505, or auth failures.
  Use when debugging failed queries, RLS policy violations, or HTTP 4xx/5xx responses.
  Trigger with "supabase error", "fix supabase", "PGRST", "supabase 403", "RLS not working",
  "supabase auth error", "unique constraint", "foreign key violation".
allowed-tools: Read, Grep, Bash(curl:*), Bash(supabase:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, debugging, errors, postgrest, rls, auth]
---

# Supabase Common Errors

## Overview

Diagnostic guide for Supabase errors across PostgREST (`PGRST*`), PostgreSQL (numeric codes), Auth, Storage, and Realtime. Identify the error layer, trace the root cause, and apply the correct fix — every SDK call returns `{ data, error }` where `data` is null when `error` exists.

## Prerequisites

- `@supabase/supabase-js` installed (`npm install @supabase/supabase-js`)
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`) configured
- Access to Supabase Dashboard (for log inspection and SQL Editor)
- Supabase CLI installed for local development (`npx supabase --version`)

## Instructions

### Step 1 — Capture the Error Object

Every Supabase SDK call returns a `{ data, error }` tuple. Never assume `data` exists — always check `error` first.

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// WRONG — data is null when error exists
const { data } = await supabase.from('todos').select('*')
console.log(data.length) // TypeError: Cannot read property 'length' of null

// CORRECT — always check error first
const { data, error } = await supabase.from('todos').select('*')
if (error) {
  console.error(`[${error.code}] ${error.message}`)
  console.error('Details:', error.details)
  console.error('Hint:', error.hint)
  // error.code tells you the layer:
  //   PGRST* = PostgREST (API gateway)
  //   5-digit numeric = PostgreSQL (database)
  //   AuthApiError = Auth service
  //   StorageApiError = Storage service
  return
}
// Safe to use data here
console.log(`Found ${data.length} rows`)
```

**Troubleshooting:** If `error` is undefined (not null), you may be using an older SDK version. Upgrade to `@supabase/supabase-js@2.x` or later.

### Step 2 — Identify the Error Layer and Code

Match the error code prefix to the correct subsystem, then look up the specific code in the tables below.

**PostgREST errors** start with `PGRST` and correspond to API-layer issues (JWT, query parsing, schema).
**PostgreSQL errors** are 5-character codes (e.g., `42501`, `23505`) from the database engine.
**Auth errors** come as `AuthApiError` with a human-readable message.
**Storage errors** come as `StorageApiError` with an HTTP status.

```typescript
// Diagnostic helper — paste into your codebase to classify errors automatically
function diagnoseSupabaseError(error: { code?: string; message: string; status?: number }) {
  if (!error) return 'No error'

  if (error.code?.startsWith('PGRST')) {
    return `PostgREST error ${error.code}: ${error.message}\n` +
      'Check: JWT validity, column/table names, query syntax'
  }
  if (error.code && /^\d{5}$/.test(error.code)) {
    return `PostgreSQL error ${error.code}: ${error.message}\n` +
      'Check: RLS policies, constraints, schema migrations'
  }
  if (error.message?.includes('AuthApiError')) {
    return `Auth error: ${error.message}\n` +
      'Check: credentials, email confirmation, token expiry'
  }
  if (error.message?.includes('StorageApiError')) {
    return `Storage error: ${error.message}\n` +
      'Check: bucket exists, RLS on storage.objects, file size limits'
  }
  return `Unknown error: ${JSON.stringify(error)}`
}
```

**Troubleshooting:** If the error code is empty or missing, check the HTTP status code on the response. A `401` without a code usually means `SUPABASE_ANON_KEY` is wrong or missing. A `500` without a code usually means a database function threw an unhandled exception.

### Step 3 — Apply the Fix and Verify

Once you have identified the error code, apply the corresponding fix from the Error Handling table. Then verify the fix by re-running the original operation.

```typescript
// Example: Fix PGRST301 (JWT expired)
// Before: stale session causes 401
const { data, error } = await supabase.from('todos').select('*')
// error.code === 'PGRST301'

// Fix: refresh the session, then retry
const { error: refreshError } = await supabase.auth.refreshSession()
if (refreshError) {
  // Token is fully invalid — force re-login
  await supabase.auth.signOut()
  console.error('Session expired. Please sign in again.')
  return
}

// Retry the original query
const { data: retryData, error: retryError } = await supabase.from('todos').select('*')
if (retryError) {
  console.error('Still failing after refresh:', retryError.code, retryError.message)
} else {
  console.log('Fixed! Retrieved', retryData.length, 'rows')
}
```

```typescript
// Example: Fix 42501 (RLS policy violation)
// Step A: Confirm RLS is the problem using service role client
const adminClient = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,  // bypasses RLS
  { auth: { autoRefreshToken: false, persistSession: false } }
)
const { data: adminData } = await adminClient.from('todos').select('*')
console.log('Admin sees', adminData?.length, 'rows')  // If this works, RLS is blocking

// Step B: Check which user the JWT resolves to
const { data: { user } } = await supabase.auth.getUser()
console.log('Current auth.uid() =', user?.id)

// Step C: Fix the RLS policy in SQL Editor or migration
/*
  CREATE POLICY "Users can read own todos"
    ON todos FOR SELECT
    USING (auth.uid() = user_id);

  -- Verify with:
  SET request.jwt.claim.sub = '<user-id>';
  SELECT * FROM todos;
*/

// Step D: Retry original query
const { data: fixedData, error: fixedError } = await supabase.from('todos').select('*')
console.log(fixedError ? `Still blocked: ${fixedError.code}` : `Success: ${fixedData.length} rows`)
```

**Troubleshooting:** After applying a migration, you may need to reload the PostgREST schema cache. In the Supabase Dashboard, go to Settings > API and click "Reload schema cache", or call `NOTIFY pgrst, 'reload schema'` in SQL.

## Output

Deliverables after applying this skill:

- Error identified by code and layer (PostgREST, PostgreSQL, Auth, Storage, Realtime)
- Root cause isolated using the diagnostic helper or manual code inspection
- Fix applied from the Error Handling table and verified against the original failing operation
- Guard code in place (`if (error)` checks) preventing silent null-data bugs

## Error Handling

### PostgREST API Errors (PGRST*)

| Code | HTTP | Meaning | Root Cause | Fix |
|------|------|---------|------------|-----|
| `PGRST301` | 401 | JWT expired or invalid | `SUPABASE_ANON_KEY` is wrong, or the user session expired | Verify `SUPABASE_ANON_KEY` matches the project; call `supabase.auth.refreshSession()` |
| `PGRST302` | 401 | Missing Authorization header | Client created without a key, or middleware stripped the header | Pass `SUPABASE_ANON_KEY` to `createClient()`; check proxy/CDN config |
| `PGRST116` | 406 | No rows returned for `.single()` | Query matched 0 rows but `.single()` expects exactly 1 | Use `.maybeSingle()` for optional lookups, or check filters |
| `PGRST200` | 400 | Invalid query parameters | Malformed filter, bad operator, or invalid column reference | Check filter syntax: `.eq('col', val)` not `.eq('col = val')` |
| `PGRST204` | 400 | Column not found | Column name doesn't exist in the table or view | Verify column exists with `supabase gen types typescript`; check for typos |
| `PGRST000` | 503 | Connection pool exhausted | Too many concurrent connections from serverless functions | Enable pgBouncer (Supavisor) in project settings; reduce connection count |

### PostgreSQL Database Errors (5-digit codes)

| Code | Meaning | Root Cause | Fix |
|------|---------|------------|-----|
| `42501` | RLS policy violation | Row-level security is blocking the operation for this user | Add or fix the RLS policy; test with service role to confirm |
| `23505` | Unique constraint violation | INSERT/UPDATE conflicts with an existing row | Use `.upsert({ onConflict: 'column' })` or check existence first |
| `23503` | Foreign key violation | Referenced row doesn't exist in the parent table | Insert the parent row first, or check the foreign key value |
| `42P01` | Table or relation doesn't exist | Migration not applied, or wrong schema | Run `supabase db push`; verify schema with `\dt` in SQL Editor |
| `42703` | Column doesn't exist | Schema out of sync with code | Regenerate types: `supabase gen types typescript --local > types/supabase.ts` |
| `57014` | Query cancelled (statement timeout) | Query took longer than `statement_timeout` | Add indexes; simplify the query; increase timeout in `postgresql.conf` |

### Auth Service Errors

| Error Message | Cause | Fix |
|---------------|-------|-----|
| `invalid_credentials` / `Invalid login credentials` | Wrong email or password | Verify credentials; check if email is confirmed |
| `email_not_confirmed` / `Email not confirmed` | User hasn't clicked confirmation link | Check inbox/spam; for local dev check Inbucket at `localhost:54324` |
| `user_already_exists` / `User already registered` | Duplicate sign-up | Call `signInWithPassword()` instead of `signUp()` |
| `Token has expired or is invalid` | Stale magic link or OTP | Request a new magic link or OTP; links expire after 5 minutes by default |
| `AuthRetryableFetchError` | Network failure reaching Auth service | Retry with backoff; verify `SUPABASE_URL` is correct and reachable |

### Storage Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Bucket not found` | Bucket name is wrong or bucket doesn't exist | Create the bucket in Dashboard or via migration SQL |
| `The resource already exists` | Uploading to a path that already has a file | Pass `{ upsert: true }` in upload options to overwrite |
| `new row violates row-level security` | Storage RLS blocking the upload/download | Add a policy on `storage.objects` for the operation (INSERT, SELECT, DELETE) |
| `413 Payload Too Large` | File exceeds the bucket's size limit | Increase `file_size_limit` on the bucket, or use TUS resumable upload for large files |

### Realtime Errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| `CHANNEL_ERROR` on subscribe | Realtime not enabled for the table | Dashboard > Database > Replication > enable the table; or add it to `supabase_realtime` publication |
| `TIMED_OUT` on subscribe | Network issue or firewall blocking WebSocket | Check that port 443 WebSocket connections are allowed |
| No events received | Table not in Realtime publication | Run: `ALTER PUBLICATION supabase_realtime ADD TABLE your_table;` |
| Events stop after deploy | Schema change drops Realtime connections | Clients auto-reconnect; ensure `.subscribe()` handles reconnection |

## Examples

### Example 1 — Handling `.single()` on optional data (PGRST116)

```typescript
// BAD — crashes when user has no profile
const { data: profile } = await supabase
  .from('profiles')
  .select('*')
  .eq('user_id', userId)
  .single()  // throws PGRST116 if no row exists

// GOOD — returns null instead of erroring
const { data: profile, error } = await supabase
  .from('profiles')
  .select('*')
  .eq('user_id', userId)
  .maybeSingle()

if (!profile) {
  // Create a default profile
  const { data: newProfile } = await supabase
    .from('profiles')
    .insert({ user_id: userId, display_name: 'New User' })
    .select()
    .single()
}
```

### Example 2 — Upsert to avoid unique constraint (23505)

```typescript
// BAD — fails if row already exists
const { error } = await supabase
  .from('user_settings')
  .insert({ user_id: userId, theme: 'dark' })
// error.code === '23505' — unique constraint on user_id

// GOOD — inserts or updates based on conflict column
const { data, error } = await supabase
  .from('user_settings')
  .upsert(
    { user_id: userId, theme: 'dark' },
    { onConflict: 'user_id' }
  )
  .select()
  .single()
```

### Example 3 — Realtime subscription with error handling

```typescript
const channel = supabase
  .channel('todos-changes')
  .on(
    'postgres_changes',
    { event: '*', schema: 'public', table: 'todos' },
    (payload) => {
      console.log('Change received:', payload.eventType, payload.new)
    }
  )
  .subscribe((status, err) => {
    switch (status) {
      case 'SUBSCRIBED':
        console.log('Realtime connected')
        break
      case 'CHANNEL_ERROR':
        console.error('Realtime error — is the table in the publication?', err)
        // Fix: ALTER PUBLICATION supabase_realtime ADD TABLE todos;
        break
      case 'TIMED_OUT':
        console.error('Realtime timed out — check network')
        break
      case 'CLOSED':
        console.log('Channel closed')
        break
    }
  })

// Always clean up on unmount / exit
process.on('SIGINT', async () => {
  await supabase.removeChannel(channel)
  process.exit(0)
})
```

### Example 4 — Connection pool exhaustion (PGRST000) in serverless

```typescript
// BAD — creates a new client per request in serverless (Lambda, Edge Functions)
export async function handler(req: Request) {
  const supabase = createClient(url, key)  // new connection every invocation
  const { data } = await supabase.from('todos').select('*')
  return Response.json(data)
}

// GOOD — reuse client across warm invocations
const supabase = createClient(url, key, {
  auth: { autoRefreshToken: false, persistSession: false }
})

export async function handler(req: Request) {
  const { data, error } = await supabase.from('todos').select('*')
  if (error) {
    if (error.code === 'PGRST000') {
      // Pool exhausted — return 503 so the caller retries
      return new Response('Service temporarily unavailable', { status: 503 })
    }
    return Response.json({ error: error.message }, { status: 400 })
  }
  return Response.json(data)
}
```

## Resources

- [Supabase JavaScript SDK Reference](https://supabase.com/docs/reference/javascript/introduction)
- [PostgREST Error Codes](https://postgrest.org/en/stable/references/errors.html)
- [PostgreSQL Error Codes](https://www.postgresql.org/docs/current/errcodes-appendix.html)
- [Supabase Auth Error Handling](https://supabase.com/docs/reference/javascript/auth-error-codes)
- [RLS Debugging Guide](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Realtime Troubleshooting](https://supabase.com/docs/guides/realtime/troubleshooting)
- [Supabase Status Page](https://status.supabase.com)

## Next Steps

- Use `supabase-debug-bundle` to generate a full diagnostic snapshot when errors persist after applying these fixes.
- Use `supabase-security-basics` to audit your RLS policies and prevent `42501` errors proactively.
- Use `supabase-known-pitfalls` for edge cases and SDK behavior that can cause subtle bugs.
- Use `supabase-observability` to set up logging and alerting so you catch errors before users report them.
