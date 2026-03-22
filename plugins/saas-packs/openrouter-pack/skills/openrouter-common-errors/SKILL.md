---
name: openrouter-common-errors
description: |
  Diagnose and fix OpenRouter common errors and exceptions.
  Use when encountering OpenRouter errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "openrouter error", "fix openrouter",
  "openrouter not working", "debug openrouter".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openrouter]
---

# OpenRouter Common Errors

## Overview
Quick reference for the top 10 most common OpenRouter errors and their solutions.

## Prerequisites
- OpenRouter SDK installed
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
echo $OPENROUTER_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `openrouter-rate-limits` skill.

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
# Check OpenRouter status
curl -s https://status.openrouter.com

# Verify API connectivity
curl -I https://api.openrouter.com

# Check local configuration
env | grep OPENROUTER
```

### Escalation Path
1. Collect evidence with `openrouter-debug-bundle`
2. Check OpenRouter status page
3. Contact support with request ID

## Resources
- [OpenRouter Status Page](https://status.openrouter.com)
- [OpenRouter Support](https://docs.openrouter.com/support)
- [OpenRouter Error Codes](https://docs.openrouter.com/errors)

## Next Steps
For comprehensive debugging, see `openrouter-debug-bundle`.