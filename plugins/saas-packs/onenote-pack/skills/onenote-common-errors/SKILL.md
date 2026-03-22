---
name: onenote-common-errors
description: |
  Diagnose and fix OneNote common errors and exceptions.
  Use when encountering OneNote errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "onenote error", "fix onenote",
  "onenote not working", "debug onenote".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, onenote]
---

# OneNote Common Errors

## Overview
Quick reference for the top 10 most common OneNote errors and their solutions.

## Prerequisites
- OneNote SDK installed
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
echo $ONENOTE_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `onenote-rate-limits` skill.

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
# Check OneNote status
curl -s https://status.onenote.com

# Verify API connectivity
curl -I https://api.onenote.com

# Check local configuration
env | grep ONENOTE
```

### Escalation Path
1. Collect evidence with `onenote-debug-bundle`
2. Check OneNote status page
3. Contact support with request ID

## Resources
- [OneNote Status Page](https://status.onenote.com)
- [OneNote Support](https://docs.onenote.com/support)
- [OneNote Error Codes](https://docs.onenote.com/errors)

## Next Steps
For comprehensive debugging, see `onenote-debug-bundle`.