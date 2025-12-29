---
name: supabase-common-errors
description: |
  Diagnose and fix Supabase common errors with solutions.
  Use when encountering Supabase errors or troubleshooting issues.
  Trigger with phrases like "supabase error", "fix supabase",
  "supabase not working", "debug supabase".
allowed-tools: Read, Grep, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Common Errors

## Overview
Quick reference for the top 10 most common Supabase errors and their solutions.

## Prerequisites
- Basic understanding of Supabase API
- Access to application logs
- SUPABASE_API_KEY environment variable configured

## Instructions

### Step 1: Identify the Error
Check your logs for the error message:
```bash
grep -i "supabase" /var/log/app.log | tail -20
```

### Step 2: Match to Known Errors
Compare the error message against the reference below.

### Step 3: Apply the Solution
Follow the solution steps for your specific error.

## Error Handling

### 1. Invalid JWT
**Message:** `Invalid JWT: expired or malformed`

**Cause:** JWT token has expired or is incorrectly formatted

**Solution:**
```bash
# Verify API key is set
echo $SUPABASE_API_KEY | head -c 10
# Regenerate key if needed in Supabase dashboard
```

---

### 2. RLS Policy Violation
**Message:** `new row violates row-level security policy for table`

**Cause:** Row Level Security (RLS) policy is blocking the operation

**Solution:** Check RLS policies in dashboard or via pg_policies table. Ensure user has required role.

---

### 3. Connection Pool Exhausted
**Message:** `too many clients already`

**Cause:** Connection pool limit reached due to too many concurrent connections

**Solution:**
```typescript
// Increase timeout
const client = new Client({ timeout: 60000 });
```

---

### 4. Invalid Request
**Message:** `Invalid request: missing required field`

**Cause:** Request payload missing required fields.

**Solution:** Validate request before sending. Check API docs for required fields.

---

### 5. Resource Not Found
**Message:** `Resource not found: 404`

**Cause:** Referenced resource does not exist or was deleted.

**Solution:** Verify resource ID. Check if resource was recently deleted.

## Output
- Identified error type and root cause
- Applied fix from solution steps
- Verified error is resolved
- Updated code to prevent recurrence

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

### Error Handling Pattern
```typescript
try {
  const result = await client.operation();
} catch (error) {
  if (error.code === 'RATE_LIMIT') {
    await sleep(error.retryAfter * 1000);
    return retry();
  }
  if (error.code === 'AUTH_ERROR') {
    throw new Error('Invalid API key - check configuration');
  }
  throw error;
}
```

## Resources
- [Supabase Error Codes](https://supabase.com/docs/errors)
- [Status Page](https://status.supabase.com)
- [Support Contact](https://supabase.com/support)

## Next Steps
- Collect evidence with `supabase-debug-bundle`
- Check Supabase status page
- Contact support with request ID if error persists