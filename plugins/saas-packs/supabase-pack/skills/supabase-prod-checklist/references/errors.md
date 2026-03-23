# Error Handling Reference

## Production Error Catalog

| Error | HTTP Status | Cause | Solution |
|-------|------------|-------|----------|
| `403 Forbidden` | 403 | RLS enabled but no policies created | Add SELECT/INSERT/UPDATE/DELETE policies for each role |
| `429 Too Many Requests` | 429 | Plan rate limit exceeded | Upgrade plan or implement client-side exponential backoff |
| Connection timeout | — | Direct connection in serverless | Switch to pooled connection string (Supavisor port 6543) |
| `PGRST301` permission denied | 401 | Service role key used where anon expected | Verify client uses anon key for client-side, service_role for server only |
| Auth emails not delivered | — | Default SMTP rate-limited (4/hour free) | Configure custom SMTP: SendGrid, Resend, or Postmark |
| Edge Function cold start | — | First invocation after idle period | Pre-warm with scheduled pings or accept ~200ms delay |
| Storage upload fails | 400/403 | Missing bucket policy or size limit exceeded | Add INSERT policy on `storage.objects` and check `file_size_limit` |
| Slow queries | — | Missing indexes on filter/join columns | Run Performance Advisor, add indexes per foreign keys and WHERE clauses |
| Migration conflicts | — | Manual Dashboard edits diverged from files | Run `npx supabase db diff` to capture drift, commit as migration |
| Realtime disconnects | — | Concurrent connection limit exceeded per tier | Reduce subscriptions or upgrade plan tier |

## Alert Thresholds

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| API Down | 5xx errors > 10/min | P1 — Critical | Check Supabase status page, verify Edge Functions, check DB connections |
| High Latency | p99 > 5000ms | P2 — Warning | Run Performance Advisor, check missing indexes, verify connection pooling |
| Rate Limited | 429 errors > 5/min | P2 — Warning | Implement backoff, consider plan upgrade, audit request patterns |
| Auth Failures | 401/403 errors spike | P1 — Critical | Check RLS policies, verify JWT expiry, audit auth provider settings |
| Pool Exhaustion | Active connections > 80% pool | P1 — Critical | Switch to Supavisor pooled connection, reduce direct connections |
| Storage Quota | Usage > 80% of plan limit | P3 — Info | Clean unused files, upgrade plan, implement lifecycle policies |

## Supabase Error Code Reference

```typescript
// Common Supabase error shapes
interface SupabaseError {
  message: string;
  details: string | null;
  hint: string | null;
  code: string;  // PostgreSQL error code
}

// Handle errors in application code
const { data, error } = await supabase.from('posts').select('*');
if (error) {
  switch (error.code) {
    case '42501': // insufficient_privilege — RLS blocking
      console.error('RLS policy missing or too restrictive');
      break;
    case '23505': // unique_violation
      console.error('Duplicate record:', error.details);
      break;
    case '23503': // foreign_key_violation
      console.error('Referenced record does not exist');
      break;
    case '57014': // statement_timeout
      console.error('Query timed out — add index or optimize');
      break;
    default:
      console.error('Supabase error:', error.message);
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
