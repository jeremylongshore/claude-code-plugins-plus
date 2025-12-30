---
name: vercel-common-errors
description: |
  Diagnose and fix Vercel common errors and exceptions.
  Use when encountering Vercel errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "vercel error", "fix vercel",
  "vercel not working", "debug vercel".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Common Errors

## Overview
Quick reference for the top 10 most common Vercel errors and their solutions.

## Prerequisites
- Vercel SDK installed
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

### Build Failed
**Error Message:**
```
Command 'npm run build' exited with 1
```

**Cause:** Build script failed due to errors in code or dependencies

**Solution:**
```bash
Check build logs in Vercel dashboard. Run 'npm run build' locally to reproduce.
```

---

### Function Timeout
**Error Message:**
```
FUNCTION_INVOCATION_TIMEOUT
```

**Cause:** Serverless function exceeded execution time limit

**Solution:**
Optimize function code, use Edge Runtime, or upgrade plan for longer timeouts.

---

### Domain Verification Failed
**Error Message:**
```
Domain verification failed
```

**Cause:** DNS records not configured correctly

**Solution:**
```typescript
Add required CNAME or A records. Wait for DNS propagation (up to 48h).
```

## Examples

### Quick Diagnostic Commands
```bash
# Check Vercel status
curl -s https://www.vercel-status.com

# Verify API connectivity
curl -I https://api.vercel.com

# Check local configuration
env | grep VERCEL
```

### Escalation Path
1. Collect evidence with `vercel-debug-bundle`
2. Check Vercel status page
3. Contact support with request ID

## Resources
- [Vercel Status Page](https://www.vercel-status.com)
- [Vercel Support](https://vercel.com/docs/support)
- [Vercel Error Codes](https://vercel.com/docs/errors)

## Next Steps
For comprehensive debugging, see `vercel-debug-bundle`.