---
name: framer-common-errors
description: |
  Diagnose and fix Framer common errors and exceptions.
  Use when encountering Framer errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "framer error", "fix framer",
  "framer not working", "debug framer".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, framer]
---

# Framer Common Errors

## Overview

Quick reference for the top 10 most common Framer errors and their solutions.


## Prerequisites
- Framer SDK installed
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
# Check Framer status
curl -s https://status.framer.com

# Verify API connectivity
curl -I https://api.framer.com

# Check local configuration
env | grep FRAMER
```

### Escalation Path
1. Collect evidence with `framer-debug-bundle`
2. Check Framer status page
3. Contact support with request ID

## Resources
- [Framer Status Page](https://status.framer.com)
- [Framer Support](https://docs.framer.com/support)
- [Framer Error Codes](https://docs.framer.com/errors)

## Next Steps
For comprehensive debugging, see `framer-debug-bundle`.