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

### Authentication Failed
**Error Message:**
```
Authentication error: Invalid API key
```

**Cause:** API key is missing, expired, or invalid.

**Solution:**
```bash
# Verify API key is set
echo $ANIMA_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `anima-rate-limits` skill.

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