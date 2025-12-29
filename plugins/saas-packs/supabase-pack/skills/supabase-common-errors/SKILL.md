---
name: supabase-common-errors
description: |
  Supabase common errors and solutions. Trigger phrases:
  "supabase error", "fix supabase", "supabase not working",
  "supabase troubleshoot", "debug supabase".
allowed-tools: Read, Grep, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Common Errors

## Overview
Quick reference for the top 10 most common Supabase errors and their solutions.

## Error Reference

### 1. Invalid JWT
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

### 2. RLS Policy Violation
**Error Message:**
```
new row violates row-level security policy for table
```

**Cause:** Row Level Security (RLS) policy is blocking the operation

**Solution:**
Check RLS policies in dashboard or via pg_policies table. Ensure user has required role.

---

### 3. Connection Pool Exhausted
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

### 4. Invalid Request
**Error Message:**
```
Invalid request: missing required field
```

**Cause:** Request payload missing required fields.

**Solution:**
Validate request before sending. Check API docs for required fields.

---

### 5. Resource Not Found
**Error Message:**
```
Resource not found: 404
```

**Cause:** Referenced resource does not exist or was deleted.

**Solution:**
Verify resource ID. Check if resource was recently deleted.

---

### 6-10. Additional Errors
See Supabase documentation for additional error codes.

## Quick Diagnostic Commands
```bash
# Check Supabase status
curl -s https://status.supabase.com

# Verify API connectivity
curl -I https://api.supabase.com

# Check local configuration
env | grep SUPABASE
```

## Escalation Path
If errors persist after trying solutions:
1. Collect evidence with `supabase-debug-bundle`
2. Check Supabase status page
3. Contact support with request ID

## Next Steps
For comprehensive debugging, see `supabase-debug-bundle`.