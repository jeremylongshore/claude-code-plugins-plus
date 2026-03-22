---
name: castai-common-errors
description: |
  Diagnose and fix Cast AI common errors and exceptions.
  Use when encountering Cast AI errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "castai error", "fix castai",
  "castai not working", "debug castai".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, castai]
---

# Cast AI Common Errors

## Overview
Quick reference for the top 10 most common Cast AI errors and their solutions.

## Prerequisites
- Cast AI SDK installed
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
echo $CASTAI_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `castai-rate-limits` skill.

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
# Check Cast AI status
curl -s https://status.castai.com

# Verify API connectivity
curl -I https://api.castai.com

# Check local configuration
env | grep CASTAI
```

### Escalation Path
1. Collect evidence with `castai-debug-bundle`
2. Check Cast AI status page
3. Contact support with request ID

## Resources
- [Cast AI Status Page](https://status.castai.com)
- [Cast AI Support](https://docs.castai.com/support)
- [Cast AI Error Codes](https://docs.castai.com/errors)

## Next Steps
For comprehensive debugging, see `castai-debug-bundle`.