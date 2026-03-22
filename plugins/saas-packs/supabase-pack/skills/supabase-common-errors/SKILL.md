---
name: supabase-common-errors
description: |
  Diagnose and fix Supabase errors across PostgREST, Auth, Storage, and Realtime.
  Use when encountering error codes, debugging failed queries,
  or troubleshooting HTTP 4xx/5xx responses from Supabase.
  Trigger with phrases like "supabase error", "fix supabase",
  "supabase not working", "debug supabase", "PGRST", "supabase 403".
allowed-tools: Read, Grep, Bash(curl:*), Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, debugging, errors]

---
# Supabase Common Errors

## Overview
Quick-reference diagnostic guide for the most frequent Supabase errors. Covers PostgREST errors (PGRST*), PostgreSQL errors (numeric codes), Auth errors, Storage errors, and Realtime connection issues.

## Prerequisites
- Supabase SDK installed
- Access to browser console or server logs

## Instructions

### PostgREST API Errors (HTTP Layer)

| Code | HTTP | Meaning | Solution |
|------|------|---------|----------|
| `PGRST000` | 503 | Connection pool exhausted | Check connection count; enable pgBouncer in `supavisor` mode |
| `PGRST116` | 406 | No rows found (`.single()` used) | Check filters; use `.maybeSingle()` for optional results |
| `PGRST204` | 406 | Column not found in select | Verify column name matches schema; regenerate types |
| `PGRST301` | 401 | JWT expired or invalid | Refresh session: `supabase.auth.refreshSession()` |
| `PGRST302` | 401 | Missing Authorization header | Ensure client is initialized with valid anon/service key |

### PostgreSQL Errors (Database Layer)

| Code | Meaning | Solution |
|------|---------|----------|
| `23505` | Unique constraint violation | Use `.upsert()` with `onConflict` or check before insert |
| `23503` | Foreign key violation | Ensure referenced row exists before insert |
| `42501` | RLS policy violation | Check `auth.uid()` in policy matches the request user |
| `42P01` | Table does not exist | Run pending migrations: `supabase db push` |
| `42703` | Column does not exist | Check schema; regenerate types with `supabase gen types` |
| `57014` | Query cancelled (timeout) | Add index or simplify query; check `statement_timeout` |

### Debugging RLS Issues

```typescript
// Step 1: Test if RLS is the problem by using the service role client
const adminClient = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false }
})

const { data: adminData } = await adminClient.from('todos').select('*')
// If this works but anon client fails, RLS is blocking

// Step 2: Check which user the JWT resolves to
const { data: { user } } = await supabase.auth.getUser()
console.log('auth.uid() =', user?.id)

// Step 3: Test the policy directly in SQL
// In Supabase SQL Editor:
// set request.jwt.claim.sub = '<user-id>';
// select * from todos;  -- should return rows if policy is correct
```

### Auth Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `AuthApiError: User already registered` | Duplicate email | Sign in instead of sign up |
| `AuthApiError: Invalid login credentials` | Wrong password | Verify credentials; check if email confirmed |
| `AuthApiError: Email not confirmed` | Confirmation pending | Check inbox (or Inbucket locally) |
| `AuthApiError: Token has expired or is invalid` | Stale magic link / OTP | Request a new one |
| `AuthRetryableFetchError` | Network issue | Retry; check SUPABASE_URL |

### Storage Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `StorageApiError: Bucket not found` | Invalid bucket name | Create bucket in dashboard or migration |
| `StorageApiError: The resource already exists` | Duplicate upload path | Use `upsert: true` in upload options |
| `StorageApiError: new row violates RLS` | Storage RLS blocking | Add policy on `storage.objects` table |
| `413 Payload Too Large` | File exceeds limit | Increase bucket `file_size_limit` or use TUS resumable upload |

### Realtime Troubleshooting

```typescript
// Check subscription status
const channel = supabase.channel('my-channel')
  .on('postgres_changes', { event: '*', schema: 'public', table: 'todos' }, (payload) => {
    console.log('Change:', payload)
  })
  .subscribe((status, err) => {
    console.log('Subscription status:', status)
    // 'SUBSCRIBED' = working
    // 'CHANNEL_ERROR' = check if Realtime is enabled on the table
    // 'TIMED_OUT' = network issue
    if (err) console.error('Subscription error:', err)
  })
```

Common Realtime fixes:
- **No events received**: Enable Realtime on the table in Dashboard > Database > Replication
- **`CHANNEL_ERROR`**: Check that the `supabase_realtime` publication includes your table
- **Events stop after deploy**: Realtime connections drop on schema changes; clients auto-reconnect

### General Debugging Checklist

1. Check `error.code` and `error.message` from the Supabase response
2. Verify `SUPABASE_URL` and key are correct for the environment
3. Test with service role key to isolate RLS issues
4. Check Supabase Dashboard > Logs > API for request details
5. Check https://status.supabase.com for platform-wide incidents

## Output
- Error identified by code and layer (PostgREST, Postgres, Auth, Storage, Realtime)
- Root cause determined with specific diagnostic steps
- Fix applied and verified against the original failing operation

## Resources
- [Supabase Status Page](https://status.supabase.com)
- [PostgREST Error Codes](https://postgrest.org/en/stable/references/errors.html)
- [PostgreSQL Error Codes](https://www.postgresql.org/docs/current/errcodes-appendix.html)
- [RLS Troubleshooting](https://supabase.com/docs/guides/troubleshooting/rls-simplified-BJTcS8)

## Next Steps
For persistent issues, see `supabase-debug-bundle`.
