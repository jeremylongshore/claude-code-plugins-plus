---
name: serpapi-common-errors
description: |
  Diagnose and fix SerpApi common errors and exceptions.
  Use when encountering SerpApi errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "serpapi error", "fix serpapi",
  "serpapi not working", "debug serpapi".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, serpapi]
---

# SerpApi Common Errors

## Overview

Quick reference for the top 10 most common SerpApi errors and their solutions.


## Prerequisites
- SerpApi SDK installed
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
Error: Command 'npm run build' exited with code 1
```

**Cause:** Compilation error, missing dependency, or misconfigured build command.

**Solution:**
```bash
# Reproduce locally
npm run build
# Check for missing env vars that build depends on
# Verify Node.js version matches platform runtime

```

---

### Function Timeout
**Error Message:**
```
FUNCTION_INVOCATION_TIMEOUT: Task timed out after 30s
```

**Cause:** Serverless function exceeded execution time limit.

**Solution:**
# Profile function execution time locally
# Move heavy computation to background jobs
# Use Edge Runtime for faster cold starts
# Upgrade plan for longer timeouts (60s Pro, 300s Enterprise)


---

### Domain Verification Failed
**Error Message:**
```
Error: Domain verification failed — DNS records not found
```

**Cause:** Required DNS records (CNAME or A record) not configured at registrar.

**Solution:**
```typescript
# Add the required DNS record at your registrar
# CNAME for subdomains: app.example.com → cname.provider.com
# A record for apex: example.com → 76.76.21.21
# Allow up to 48h for DNS propagation

```



## Examples

### Quick Diagnostic Commands
```bash
# Check SerpApi status
curl -s https://status.serpapi.com

# Verify API connectivity
curl -I https://api.serpapi.com

# Check local configuration
env | grep SERPAPI
```

### Escalation Path
1. Collect evidence with `serpapi-debug-bundle`
2. Check SerpApi status page
3. Contact support with request ID

## Resources
- [SerpApi Status Page](https://status.serpapi.com)
- [SerpApi Support](https://docs.serpapi.com/support)
- [SerpApi Error Codes](https://docs.serpapi.com/errors)

## Next Steps
For comprehensive debugging, see `serpapi-debug-bundle`.