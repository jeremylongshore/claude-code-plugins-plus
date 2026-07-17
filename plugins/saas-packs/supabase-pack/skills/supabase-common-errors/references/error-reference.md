# Supabase Error Code Reference

Complete lookup tables for every error layer. SKILL.md keeps the two most-cited
tables (PostgREST + PostgreSQL) inline; the Auth, Storage, and Realtime tables
live here in full.

## PostgREST API Errors (PGRST*)

| Code | HTTP | Meaning | Root Cause | Fix |
| ------ | ------ | --------- | ------------ | ----- |
| `PGRST301` | 401 | JWT expired or invalid | `SUPABASE_ANON_KEY` is wrong, or the user session expired | Verify `SUPABASE_ANON_KEY` matches the project; call `supabase.auth.refreshSession()` |
| `PGRST302` | 401 | Missing Authorization header | Client created without a key, or middleware stripped the header | Pass `SUPABASE_ANON_KEY` to `createClient()`; check proxy/CDN config |
| `PGRST116` | 406 | No rows returned for `.single()` | Query matched 0 rows but `.single()` expects exactly 1 | Use `.maybeSingle()` for optional lookups, or check filters |
| `PGRST200` | 400 | Invalid query parameters | Malformed filter, bad operator, or invalid column reference | Check filter syntax: `.eq('col', val)` not `.eq('col = val')` |
| `PGRST204` | 400 | Column not found | Column name doesn't exist in the table or view | Verify column exists with `supabase gen types typescript`; check for typos |
| `PGRST000` | 503 | Connection pool exhausted | Too many concurrent connections from serverless functions | Enable pgBouncer (Supavisor) in project settings; reduce connection count |

## PostgreSQL Database Errors (5-digit codes)

| Code | Meaning | Root Cause | Fix |
| ------ | --------- | ------------ | ----- |
| `42501` | RLS policy violation | Row-level security is blocking the operation for this user | Add or fix the RLS policy; test with service role to confirm |
| `23505` | Unique constraint violation | INSERT/UPDATE conflicts with an existing row | Use `.upsert({ onConflict: 'column' })` or check existence first |
| `23503` | Foreign key violation | Referenced row doesn't exist in the parent table | Insert the parent row first, or check the foreign key value |
| `42P01` | Table or relation doesn't exist | Migration not applied, or wrong schema | Run `supabase db push`; verify schema with `\dt` in SQL Editor |
| `42703` | Column doesn't exist | Schema out of sync with code | Regenerate types: `supabase gen types typescript --local > types/supabase.ts` |
| `57014` | Query cancelled (statement timeout) | Query took longer than `statement_timeout` | Add indexes; simplify the query; increase timeout in `postgresql.conf` |

## Auth Service Errors

| Error Message | Cause | Fix |
| --------------- | ------- | ----- |
| `invalid_credentials` / `Invalid login credentials` | Wrong email or password | Verify credentials; check if email is confirmed |
| `email_not_confirmed` / `Email not confirmed` | User hasn't clicked confirmation link | Check inbox/spam; for local dev check Inbucket at `localhost:54324` |
| `user_already_exists` / `User already registered` | Duplicate sign-up | Call `signInWithPassword()` instead of `signUp()` |
| `Token has expired or is invalid` | Stale magic link or OTP | Request a new magic link or OTP; links expire after 5 minutes by default |
| `AuthRetryableFetchError` | Network failure reaching Auth service | Retry with backoff; verify `SUPABASE_URL` is correct and reachable |

## Storage Errors

| Error | Cause | Fix |
| ------- | ------- | ----- |
| `Bucket not found` | Bucket name is wrong or bucket doesn't exist | Create the bucket in Dashboard or via migration SQL |
| `The resource already exists` | Uploading to a path that already has a file | Pass `{ upsert: true }` in upload options to overwrite |
| `new row violates row-level security` | Storage RLS blocking the upload/download | Add a policy on `storage.objects` for the operation (INSERT, SELECT, DELETE) |
| `413 Payload Too Large` | File exceeds the bucket's size limit | Increase `file_size_limit` on the bucket, or use TUS resumable upload for large files |

## Realtime Errors

| Symptom | Cause | Fix |
| --------- | ------- | ----- |
| `CHANNEL_ERROR` on subscribe | Realtime not enabled for the table | Dashboard > Database > Replication > enable the table; or add it to `supabase_realtime` publication |
| `TIMED_OUT` on subscribe | Network issue or firewall blocking WebSocket | Check that port 443 WebSocket connections are allowed |
| No events received | Table not in Realtime publication | Run: `ALTER PUBLICATION supabase_realtime ADD TABLE your_table;` |
| Events stop after deploy | Schema change drops Realtime connections | Clients auto-reconnect; ensure `.subscribe()` handles reconnection |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
