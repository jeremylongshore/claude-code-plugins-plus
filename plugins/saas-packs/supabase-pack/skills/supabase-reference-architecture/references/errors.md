# Error Handling Reference

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing SUPABASE_URL or SUPABASE_ANON_KEY` | Environment variables not set | Check `.env` file and ensure variables are loaded |
| `new row violates row-level security policy` | RLS blocks the operation | Verify `org_id` JWT claim matches the row's `org_id` |
| `Not a member of tenant` | User tried switching to unauthorized tenant | Check `tenant_members` table for the user-tenant pair |
| `relation "public.audit_log" does not exist` | Audit migration not applied | Run `supabase db push` or `supabase db reset` |
| `permission denied for function claim_next_job` | Missing execute grant | Run `grant execute on function claim_next_job to authenticated` |
| `Cross-project profile lookup failed` | Wrong service_role key for the target project | Verify `MAIN_SUPABASE_SERVICE_ROLE_KEY` matches the main project |
| `TypeError: Cannot read properties of null` | Client singleton not initialized | Ensure env vars are available before first `getSupabaseClient()` call |
| `cron.schedule: permission denied` | `pg_cron` extension not enabled | Enable via dashboard: Database > Extensions > pg_cron |

## RLS Debugging Checklist

1. Verify `alter table ... enable row level security` was run on the table
2. Check that at least one permissive policy exists for the operation (SELECT, INSERT, UPDATE, DELETE)
3. Confirm the JWT contains the expected `org_id` claim: `select auth.jwt() ->> 'org_id'`
4. Test the policy logic directly: `select * from projects where org_id = 'expected-uuid'`
5. Use `supabase inspect db policies` to list all active policies

## Cross-Project Access Troubleshooting

- **401 Unauthorized**: The `service_role` key is wrong or belongs to a different project
- **Network timeout**: Cross-region calls add latency; consider caching or co-locating projects
- **Rate limited**: Supabase enforces per-project rate limits; distribute load across projects
- **Type mismatch**: Regenerate types for both projects after schema changes
