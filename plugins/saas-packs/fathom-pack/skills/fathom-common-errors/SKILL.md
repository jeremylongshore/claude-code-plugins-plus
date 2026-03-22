---
name: fathom-common-errors
description: |
  Diagnose and fix Fathom common errors and exceptions.
  Use when encountering Fathom errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "fathom error", "fix fathom",
  "fathom not working", "debug fathom".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fathom]
---

# Fathom Common Errors

## Overview
Quick reference for the top 10 most common Fathom errors and their solutions.

## Prerequisites
- Fathom SDK installed
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

### Authentication Failed
**Error Message:**
```
Authentication error: Invalid API key
```

**Cause:** API key is missing, expired, or invalid.

**Solution:**
```bash
# Verify API key is set
echo $FATHOM_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `fathom-rate-limits` skill.

---

### Network Timeout
**Error Message:**
```
Request timeout after 30000ms
```

**Cause:** Network connectivity or server latency issues.

**Solution:**
```typescript
// Increase timeout
const client = new Client({ timeout: 60000 });
```

## Examples

### Quick Diagnostic Commands
```bash
# Check Fathom status
curl -s https://status.fathom.com

# Verify API connectivity
curl -I https://api.fathom.com

# Check local configuration
env | grep FATHOM
```

### Escalation Path
1. Collect evidence with `fathom-debug-bundle`
2. Check Fathom status page
3. Contact support with request ID

## Resources
- [Fathom Status Page](https://status.fathom.com)
- [Fathom Support](https://docs.fathom.com/support)
- [Fathom Error Codes](https://docs.fathom.com/errors)

## Next Steps
For comprehensive debugging, see `fathom-debug-bundle`.