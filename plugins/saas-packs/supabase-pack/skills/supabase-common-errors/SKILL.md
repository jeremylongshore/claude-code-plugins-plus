---
name: supabase-common-errors
description: |
  Diagnose and fix Supabase common errors and exceptions.
  Use when encountering Supabase errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "supabase error", "fix supabase",
  "supabase not working", "debug supabase".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Common Errors

## Overview
Quick reference for the top 10 most common Supabase errors and their solutions.

## Prerequisites
- Supabase SDK installed
- API credentials configured
- Access to error logs

## Instructions

### Step 1: Identify the Error
Check error message and code in your logs or console.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.

## Output
- Identified error cause
- Applied fix
- Verified resolution

## Error Handling

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

## Examples

### Quick Diagnostic Commands
```bash
# Check Supabase status
curl -s https://status.supabase.com

# Verify API connectivity
curl -I https://api.supabase.com

# Check local configuration
env | grep SUPABASE
```

### Escalation Path
1. Collect evidence with `supabase-debug-bundle`
2. Check Supabase status page
3. Contact support with request ID

## Resources
- [Supabase Status Page](https://status.supabase.com)
- [Supabase Support](https://supabase.com/docs/support)
- [Supabase Error Codes](https://supabase.com/docs/errors)

## Next Steps
For comprehensive debugging, see `supabase-debug-bundle`.