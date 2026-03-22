---
name: flyio-common-errors
description: |
  Diagnose and fix Fly.io common errors and exceptions.
  Use when encountering Fly.io errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "flyio error", "fix flyio",
  "flyio not working", "debug flyio".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flyio]
---

# Fly.io Common Errors

## Overview
Quick reference for the top 10 most common Fly.io errors and their solutions.

## Prerequisites
- Fly.io SDK installed
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
echo $FLYIO_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `flyio-rate-limits` skill.

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
# Check Fly.io status
curl -s https://status.flyio.com

# Verify API connectivity
curl -I https://api.flyio.com

# Check local configuration
env | grep FLYIO
```

### Escalation Path
1. Collect evidence with `flyio-debug-bundle`
2. Check Fly.io status page
3. Contact support with request ID

## Resources
- [Fly.io Status Page](https://status.flyio.com)
- [Fly.io Support](https://docs.flyio.com/support)
- [Fly.io Error Codes](https://docs.flyio.com/errors)

## Next Steps
For comprehensive debugging, see `flyio-debug-bundle`.