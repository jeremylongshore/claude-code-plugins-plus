---
name: canva-common-errors
description: |
  Diagnose and fix Canva common errors and exceptions.
  Use when encountering Canva errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "canva error", "fix canva",
  "canva not working", "debug canva".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, canva]
---

# Canva Common Errors

## Overview
Quick reference for the top 10 most common Canva errors and their solutions.

## Prerequisites
- Canva SDK installed
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
echo $CANVA_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `canva-rate-limits` skill.

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
# Check Canva status
curl -s https://status.canva.com

# Verify API connectivity
curl -I https://api.canva.com

# Check local configuration
env | grep CANVA
```

### Escalation Path
1. Collect evidence with `canva-debug-bundle`
2. Check Canva status page
3. Contact support with request ID

## Resources
- [Canva Status Page](https://status.canva.com)
- [Canva Support](https://docs.canva.com/support)
- [Canva Error Codes](https://docs.canva.com/errors)

## Next Steps
For comprehensive debugging, see `canva-debug-bundle`.