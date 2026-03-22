---
name: remofirst-common-errors
description: |
  Diagnose and fix RemoFirst common errors and exceptions.
  Use when encountering RemoFirst errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "remofirst error", "fix remofirst",
  "remofirst not working", "debug remofirst".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, remofirst]
---

# RemoFirst Common Errors

## Overview
Quick reference for the top 10 most common RemoFirst errors and their solutions.

## Prerequisites
- RemoFirst SDK installed
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
echo $REMOFIRST_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `remofirst-rate-limits` skill.

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
# Check RemoFirst status
curl -s https://status.remofirst.com

# Verify API connectivity
curl -I https://api.remofirst.com

# Check local configuration
env | grep REMOFIRST
```

### Escalation Path
1. Collect evidence with `remofirst-debug-bundle`
2. Check RemoFirst status page
3. Contact support with request ID

## Resources
- [RemoFirst Status Page](https://status.remofirst.com)
- [RemoFirst Support](https://docs.remofirst.com/support)
- [RemoFirst Error Codes](https://docs.remofirst.com/errors)

## Next Steps
For comprehensive debugging, see `remofirst-debug-bundle`.