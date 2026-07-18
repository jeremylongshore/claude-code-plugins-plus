# Supabase Common Errors — Full Diagnostic Walkthrough

The complete three-step workflow for capturing, classifying, and fixing Supabase
errors. SKILL.md carries the high-level version; this file has every code block.

## Step 1 — Capture the Error Object

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

## Step 2 — Identify the Error Layer and Code

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

## Step 3 — Apply the Fix and Verify

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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
