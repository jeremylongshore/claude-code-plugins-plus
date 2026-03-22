---
name: linear-common-errors
description: |
  Diagnose and fix Linear common errors and exceptions.
  Use when encountering Linear errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "linear error", "fix linear",
  "linear not working", "debug linear".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linear]
---

# Linear Common Errors

## Overview
Quick reference for the top 10 most common Linear errors and their solutions.

## Prerequisites
- Linear SDK installed
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
echo $LINEAR_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `linear-rate-limits` skill.

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
# Check Linear status
curl -s https://status.linear.com

# Verify API connectivity
curl -I https://api.linear.com

# Check local configuration
env | grep LINEAR
```

### Escalation Path
1. Collect evidence with `linear-debug-bundle`
2. Check Linear status page
3. Contact support with request ID

## Resources
- [Linear Status Page](https://status.linear.com)
- [Linear Support](https://docs.linear.com/support)
- [Linear Error Codes](https://docs.linear.com/errors)

## Next Steps
For comprehensive debugging, see `linear-debug-bundle`.