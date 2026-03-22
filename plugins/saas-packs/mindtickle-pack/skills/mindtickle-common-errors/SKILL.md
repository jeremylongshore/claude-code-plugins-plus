---
name: mindtickle-common-errors
description: |
  Diagnose and fix Mindtickle common errors and exceptions.
  Use when encountering Mindtickle errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "mindtickle error", "fix mindtickle",
  "mindtickle not working", "debug mindtickle".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mindtickle]
---

# Mindtickle Common Errors

## Overview
Quick reference for the top 10 most common Mindtickle errors and their solutions.

## Prerequisites
- Mindtickle SDK installed
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
echo $MINDTICKLE_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `mindtickle-rate-limits` skill.

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
# Check Mindtickle status
curl -s https://status.mindtickle.com

# Verify API connectivity
curl -I https://api.mindtickle.com

# Check local configuration
env | grep MINDTICKLE
```

### Escalation Path
1. Collect evidence with `mindtickle-debug-bundle`
2. Check Mindtickle status page
3. Contact support with request ID

## Resources
- [Mindtickle Status Page](https://status.mindtickle.com)
- [Mindtickle Support](https://docs.mindtickle.com/support)
- [Mindtickle Error Codes](https://docs.mindtickle.com/errors)

## Next Steps
For comprehensive debugging, see `mindtickle-debug-bundle`.