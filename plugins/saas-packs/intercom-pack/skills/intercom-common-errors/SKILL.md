---
name: intercom-common-errors
description: |
  Diagnose and fix Intercom common errors and exceptions.
  Use when encountering Intercom errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "intercom error", "fix intercom",
  "intercom not working", "debug intercom".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, intercom]
---

# Intercom Common Errors

## Overview
Quick reference for the top 10 most common Intercom errors and their solutions.

## Prerequisites
- Intercom SDK installed
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
echo $INTERCOM_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `intercom-rate-limits` skill.

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
# Check Intercom status
curl -s https://status.intercom.com

# Verify API connectivity
curl -I https://api.intercom.com

# Check local configuration
env | grep INTERCOM
```

### Escalation Path
1. Collect evidence with `intercom-debug-bundle`
2. Check Intercom status page
3. Contact support with request ID

## Resources
- [Intercom Status Page](https://status.intercom.com)
- [Intercom Support](https://docs.intercom.com/support)
- [Intercom Error Codes](https://docs.intercom.com/errors)

## Next Steps
For comprehensive debugging, see `intercom-debug-bundle`.