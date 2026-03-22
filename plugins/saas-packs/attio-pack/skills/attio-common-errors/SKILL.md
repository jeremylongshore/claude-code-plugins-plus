---
name: attio-common-errors
description: |
  Diagnose and fix Attio common errors and exceptions.
  Use when encountering Attio errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "attio error", "fix attio",
  "attio not working", "debug attio".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, attio]
---

# Attio Common Errors

## Overview
Quick reference for the top 10 most common Attio errors and their solutions.

## Prerequisites
- Attio SDK installed
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
echo $ATTIO_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `attio-rate-limits` skill.

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
# Check Attio status
curl -s https://status.attio.com

# Verify API connectivity
curl -I https://api.attio.com

# Check local configuration
env | grep ATTIO
```

### Escalation Path
1. Collect evidence with `attio-debug-bundle`
2. Check Attio status page
3. Contact support with request ID

## Resources
- [Attio Status Page](https://status.attio.com)
- [Attio Support](https://docs.attio.com/support)
- [Attio Error Codes](https://docs.attio.com/errors)

## Next Steps
For comprehensive debugging, see `attio-debug-bundle`.