---
name: algolia-common-errors
description: |
  Diagnose and fix Algolia common errors and exceptions.
  Use when encountering Algolia errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "algolia error", "fix algolia",
  "algolia not working", "debug algolia".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, algolia]
---

# Algolia Common Errors

## Overview
Quick reference for the top 10 most common Algolia errors and their solutions.

## Prerequisites
- Algolia SDK installed
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
echo $ALGOLIA_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `algolia-rate-limits` skill.

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
# Check Algolia status
curl -s https://status.algolia.com

# Verify API connectivity
curl -I https://api.algolia.com

# Check local configuration
env | grep ALGOLIA
```

### Escalation Path
1. Collect evidence with `algolia-debug-bundle`
2. Check Algolia status page
3. Contact support with request ID

## Resources
- [Algolia Status Page](https://status.algolia.com)
- [Algolia Support](https://docs.algolia.com/support)
- [Algolia Error Codes](https://docs.algolia.com/errors)

## Next Steps
For comprehensive debugging, see `algolia-debug-bundle`.