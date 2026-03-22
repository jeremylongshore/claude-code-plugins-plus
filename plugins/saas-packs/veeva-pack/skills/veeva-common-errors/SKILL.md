---
name: veeva-common-errors
description: |
  Diagnose and fix Veeva common errors and exceptions.
  Use when encountering Veeva errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "veeva error", "fix veeva",
  "veeva not working", "debug veeva".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, veeva]
---

# Veeva Common Errors

## Overview
Quick reference for the top 10 most common Veeva errors and their solutions.

## Prerequisites
- Veeva SDK installed
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
echo $VEEVA_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `veeva-rate-limits` skill.

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
# Check Veeva status
curl -s https://status.veeva.com

# Verify API connectivity
curl -I https://api.veeva.com

# Check local configuration
env | grep VEEVA
```

### Escalation Path
1. Collect evidence with `veeva-debug-bundle`
2. Check Veeva status page
3. Contact support with request ID

## Resources
- [Veeva Status Page](https://status.veeva.com)
- [Veeva Support](https://docs.veeva.com/support)
- [Veeva Error Codes](https://docs.veeva.com/errors)

## Next Steps
For comprehensive debugging, see `veeva-debug-bundle`.