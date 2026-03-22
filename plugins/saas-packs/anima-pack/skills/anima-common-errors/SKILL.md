---
name: anima-common-errors
description: |
  Diagnose and fix Anima common errors and exceptions.
  Use when encountering Anima errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "anima error", "fix anima",
  "anima not working", "debug anima".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anima]
---

# Anima Common Errors

## Overview

Quick reference for the top 10 most common Anima errors and their solutions.


## Prerequisites
- Anima SDK installed
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

### OAuth Token Expired
**Error Message:**
```
403 Forbidden: Access token expired
```

**Cause:** OAuth access token has expired (typically 1-24h lifetime).

**Solution:**
```bash
# Refresh the token using your refresh_token
curl -X POST https://api.vendor.com/oauth/token \
  -d "grant_type=refresh_token&refresh_token=$REFRESH_TOKEN"
# Store new access_token and update env var

```

---

### File Not Found
**Error Message:**
```
404 Not Found: File not found or you don't have access
```

**Cause:** File ID is wrong, file was deleted, or API token doesn't have access.

**Solution:**
# Verify file ID from the URL (e.g., figma.com/file/FILE_ID/...)
# Check file permissions — must be shared with the API token's user
# Use team/project listing to find correct file ID


---

### Rate Limited (File Exports)
**Error Message:**
```
429 Too Many Requests: Export rate limit exceeded
```

**Cause:** Too many export requests in a short window (design APIs have tight export limits).

**Solution:**
```typescript
# Batch export requests — request multiple node IDs in one call
# Cache exported assets locally with content-hash filenames
# Implement backoff: wait 60s after hitting 429

```



## Examples

### Quick Diagnostic Commands
```bash
# Check Anima status
curl -s https://status.anima.com

# Verify API connectivity
curl -I https://api.anima.com

# Check local configuration
env | grep ANIMA
```

### Escalation Path
1. Collect evidence with `anima-debug-bundle`
2. Check Anima status page
3. Contact support with request ID

## Resources
- [Anima Status Page](https://status.anima.com)
- [Anima Support](https://docs.anima.com/support)
- [Anima Error Codes](https://docs.anima.com/errors)

## Next Steps
For comprehensive debugging, see `anima-debug-bundle`.