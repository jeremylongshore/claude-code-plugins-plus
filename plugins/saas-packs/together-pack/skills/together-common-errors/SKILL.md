---
name: together-common-errors
description: |
  Diagnose and fix Together AI common errors and exceptions.
  Use when encountering Together AI errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "together error", "fix together",
  "together not working", "debug together".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, together]
---

# Together AI Common Errors

## Overview
Quick reference for the top 10 most common Together AI errors and their solutions.

## Prerequisites
- Together AI SDK installed
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
echo $TOGETHER_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `together-rate-limits` skill.

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
# Check Together AI status
curl -s https://status.together.com

# Verify API connectivity
curl -I https://api.together.com

# Check local configuration
env | grep TOGETHER
```

### Escalation Path
1. Collect evidence with `together-debug-bundle`
2. Check Together AI status page
3. Contact support with request ID

## Resources
- [Together AI Status Page](https://status.together.com)
- [Together AI Support](https://docs.together.com/support)
- [Together AI Error Codes](https://docs.together.com/errors)

## Next Steps
For comprehensive debugging, see `together-debug-bundle`.