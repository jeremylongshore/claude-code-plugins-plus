## Error Handling Reference

### Invalid JWT

**Error Message:**

```
Invalid JWT: expired or malformed
```

**Cause:** JWT token has expired or is incorrectly formatted

**Solution:**

```bash
Check token expiry with supabase.auth.getSession() and call refreshSession() if needed
```

---

### RLS Policy Violation

**Error Message:**

```
new row violates row-level security policy for table
```

**Cause:** Row Level Security (RLS) policy is blocking the operation

**Solution:**
Check RLS policies in dashboard or via pg_policies table. Ensure user has required role.

---

### Connection Pool Exhausted

**Error Message:**

```
too many clients already
```

**Cause:** Connection pool limit reached due to too many concurrent connections

**Solution:**

```typescript
Use connection pooling mode in Supabase dashboard. Switch to Session mode or pgBouncer.
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
