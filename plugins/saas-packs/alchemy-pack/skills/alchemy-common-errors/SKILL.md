---
name: alchemy-common-errors
description: |
  Diagnose and fix Alchemy common errors and exceptions.
  Use when encountering Alchemy errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "alchemy error", "fix alchemy",
  "alchemy not working", "debug alchemy".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, alchemy]
---

# Alchemy Common Errors

## Overview
Quick reference for the top 10 most common Alchemy errors and their solutions.

## Prerequisites
- Alchemy SDK installed
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
echo $ALCHEMY_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `alchemy-rate-limits` skill.

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
# Check Alchemy status
curl -s https://status.alchemy.com

# Verify API connectivity
curl -I https://api.alchemy.com

# Check local configuration
env | grep ALCHEMY
```

### Escalation Path
1. Collect evidence with `alchemy-debug-bundle`
2. Check Alchemy status page
3. Contact support with request ID

## Resources
- [Alchemy Status Page](https://status.alchemy.com)
- [Alchemy Support](https://docs.alchemy.com/support)
- [Alchemy Error Codes](https://docs.alchemy.com/errors)

## Next Steps
For comprehensive debugging, see `alchemy-debug-bundle`.