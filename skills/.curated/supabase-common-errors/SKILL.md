---
name: supabase-common-errors
description: 'Diagnose and fix Supabase errors across PostgREST, PostgreSQL, Auth,
  Storage, and Realtime.

  Use when encountering error codes like PGRST301, 42501, 23505, or auth failures.

  Use when debugging failed queries, RLS policy violations, or HTTP 4xx/5xx responses.

  Trigger with "supabase error", "fix supabase", "PGRST", "supabase 403", "RLS not
  working",

  "supabase auth error", "unique constraint", "foreign key violation".

  '
allowed-tools: Read, Grep, Bash(curl:*), Bash(supabase:*), Bash(npx:*)
version: 1.53.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- supabase
- debugging
- errors
- postgrest
- rls
- auth
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Supabase Common Errors

## Overview

Diagnostic guide for Supabase errors across PostgREST (`PGRST*`), PostgreSQL (numeric codes), Auth, Storage, and Realtime. Identify the error layer, trace the root cause, and apply the correct fix — every SDK call returns `{ data, error }` where `data` is null when `error` exists.

The workflow is three steps: capture the error object, classify it by layer and code, then apply and verify the fix. Full step-by-step code lives in [the diagnostic walkthrough](references/implementation.md); complete lookup tables are in [the error reference](references/error-reference.md).

## Prerequisites

- `@supabase/supabase-js` installed (`npm install @supabase/supabase-js`)
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`) configured
- Access to Supabase Dashboard (for log inspection and SQL Editor)
- Supabase CLI installed for local development (`npx supabase --version`)

## Instructions

### Step 1 — Capture the Error Object

Every Supabase SDK call returns a `{ data, error }` tuple. Never assume `data` exists — always destructure and check `error` first, because `data` is null whenever `error` is set.

```typescript
const { data, error } = await supabase.from('todos').select('*')
if (error) {
  console.error(`[${error.code}] ${error.message}`)
  return  // data is null here — do not touch it
}
console.log(`Found ${data.length} rows`)
```

If `error` is undefined rather than null, upgrade to `@supabase/supabase-js@2.x`. See [the walkthrough](references/implementation.md) for the full guard pattern.

### Step 2 — Identify the Error Layer and Code

Match the code prefix to its subsystem, then look it up in the Error Handling tables below:

- **`PGRST*`** → PostgREST (API gateway: JWT, query parsing, schema)
- **5-digit numeric** (e.g. `42501`, `23505`) → PostgreSQL engine (RLS, constraints, migrations)
- **`AuthApiError`** → Auth service (credentials, confirmation, token expiry)
- **`StorageApiError`** → Storage service (bucket, RLS on `storage.objects`, size limits)

A missing code usually means the HTTP status is the signal: `401` → bad/missing `SUPABASE_ANON_KEY`; `500` → an unhandled exception in a database function. A paste-ready `diagnoseSupabaseError()` classifier is in [the walkthrough](references/implementation.md).

### Step 3 — Apply the Fix and Verify

Apply the fix from the matching Error Handling table, then re-run the original operation to confirm. Common recoveries:

- Refresh an expired JWT (`PGRST301`) with `supabase.auth.refreshSession()`.
- Confirm an RLS block (`42501`) by re-querying with the service-role client before correcting the policy.
- After a migration, reload the PostgREST schema cache (Dashboard → Settings → API → "Reload schema cache", or `NOTIFY pgrst, 'reload schema'`).

Full before/after fix code for both cases is in [the walkthrough](references/implementation.md).

## Output

Deliverables after applying this skill:

- Error identified by code and layer (PostgREST, PostgreSQL, Auth, Storage, Realtime)
- Root cause isolated using the diagnostic helper or manual code inspection
- Fix applied from the Error Handling table and verified against the original failing operation
- Guard code in place (`if (error)` checks) preventing silent null-data bugs

## Error Handling

The two most-cited layers are inline below. Auth, Storage, and Realtime tables are in [the full error reference](references/error-reference.md).

### PostgREST API Errors (PGRST*)

| Code | HTTP | Meaning | Root Cause | Fix |
| ------ | ------ | --------- | ------------ | ----- |
| `PGRST301` | 401 | JWT expired or invalid | `SUPABASE_ANON_KEY` is wrong, or the user session expired | Verify `SUPABASE_ANON_KEY` matches the project; call `supabase.auth.refreshSession()` |
| `PGRST302` | 401 | Missing Authorization header | Client created without a key, or middleware stripped the header | Pass `SUPABASE_ANON_KEY` to `createClient()`; check proxy/CDN config |
| `PGRST116` | 406 | No rows returned for `.single()` | Query matched 0 rows but `.single()` expects exactly 1 | Use `.maybeSingle()` for optional lookups, or check filters |
| `PGRST200` | 400 | Invalid query parameters | Malformed filter, bad operator, or invalid column reference | Check filter syntax: `.eq('col', val)` not `.eq('col = val')` |
| `PGRST204` | 400 | Column not found | Column name doesn't exist in the table or view | Verify column exists with `supabase gen types typescript`; check for typos |
| `PGRST000` | 503 | Connection pool exhausted | Too many concurrent connections from serverless functions | Enable pgBouncer (Supavisor) in project settings; reduce connection count |

### PostgreSQL Database Errors (5-digit codes)

| Code | Meaning | Root Cause | Fix |
| ------ | --------- | ------------ | ----- |
| `42501` | RLS policy violation | Row-level security is blocking the operation for this user | Add or fix the RLS policy; test with service role to confirm |
| `23505` | Unique constraint violation | INSERT/UPDATE conflicts with an existing row | Use `.upsert({ onConflict: 'column' })` or check existence first |
| `23503` | Foreign key violation | Referenced row doesn't exist in the parent table | Insert the parent row first, or check the foreign key value |
| `42P01` | Table or relation doesn't exist | Migration not applied, or wrong schema | Run `supabase db push`; verify schema with `\dt` in SQL Editor |
| `42703` | Column doesn't exist | Schema out of sync with code | Regenerate types: `supabase gen types typescript --local > types/supabase.ts` |
| `57014` | Query cancelled (statement timeout) | Query took longer than `statement_timeout` | Add indexes; simplify the query; increase timeout in `postgresql.conf` |

## Examples

The most common failure — calling `.single()` on optional data — is inline below. Three more worked examples (upsert to dodge `23505`, Realtime subscription error handling, and serverless pool exhaustion) are in [the examples reference](references/examples.md).

### Handling `.single()` on optional data (PGRST116)

```typescript
// BAD — throws PGRST116 when the user has no profile row
const { data: profile } = await supabase
  .from('profiles').select('*').eq('user_id', userId).single()

// GOOD — returns null instead of erroring
const { data: profile, error } = await supabase
  .from('profiles').select('*').eq('user_id', userId).maybeSingle()

if (!profile) {
  await supabase.from('profiles').insert({ user_id: userId, display_name: 'New User' })
}
```

## Resources

- [Full diagnostic walkthrough](references/implementation.md) — every capture/classify/fix code block
- [Complete error reference](references/error-reference.md) — Auth, Storage, and Realtime tables
- [Worked examples](references/examples.md) — upsert, Realtime, serverless pooling
- [Supabase JavaScript SDK Reference](https://supabase.com/docs/reference/javascript/introduction)
- [PostgREST Error Codes](https://postgrest.org/en/stable/references/errors.html)
- [PostgreSQL Error Codes](https://www.postgresql.org/docs/current/errcodes-appendix.html)
- [RLS Debugging Guide](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Realtime Troubleshooting](https://supabase.com/docs/guides/realtime/troubleshooting)
- [Supabase Status Page](https://status.supabase.com)

## Next Steps

- Use `supabase-debug-bundle` to generate a full diagnostic snapshot when errors persist after applying these fixes.
- Use `supabase-security-basics` to audit your RLS policies and prevent `42501` errors proactively.
- Use `supabase-known-pitfalls` for edge cases and SDK behavior that can cause subtle bugs.
- Use `supabase-observability` to set up logging and alerting so you catch errors before users report them.
