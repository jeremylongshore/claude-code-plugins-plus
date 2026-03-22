---
name: grammarly-common-errors
description: |
  Diagnose and fix Grammarly common errors and exceptions.
  Use when encountering Grammarly errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "grammarly error", "fix grammarly",
  "grammarly not working", "debug grammarly".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, grammarly]
---

# Grammarly Common Errors

## Overview
Quick reference for the top 10 most common Grammarly errors and their solutions.

## Prerequisites
- Grammarly SDK installed
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
echo $GRAMMARLY_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `grammarly-rate-limits` skill.

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
# Check Grammarly status
curl -s https://status.grammarly.com

# Verify API connectivity
curl -I https://api.grammarly.com

# Check local configuration
env | grep GRAMMARLY
```

### Escalation Path
1. Collect evidence with `grammarly-debug-bundle`
2. Check Grammarly status page
3. Contact support with request ID

## Resources
- [Grammarly Status Page](https://status.grammarly.com)
- [Grammarly Support](https://docs.grammarly.com/support)
- [Grammarly Error Codes](https://docs.grammarly.com/errors)

## Next Steps
For comprehensive debugging, see `grammarly-debug-bundle`.