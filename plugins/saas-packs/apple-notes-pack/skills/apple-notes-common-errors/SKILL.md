---
name: apple-notes-common-errors
description: |
  Diagnose and fix Apple Notes common errors and exceptions.
  Use when encountering Apple Notes errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "apple-notes error", "fix apple-notes",
  "apple-notes not working", "debug apple-notes".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apple-notes]
---

# Apple Notes Common Errors

## Overview
Quick reference for the top 10 most common Apple Notes errors and their solutions.

## Prerequisites
- Apple Notes SDK installed
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
echo $APPLE-NOTES_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `apple-notes-rate-limits` skill.

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
# Check Apple Notes status
curl -s https://status.apple-notes.com

# Verify API connectivity
curl -I https://api.apple-notes.com

# Check local configuration
env | grep APPLE-NOTES
```

### Escalation Path
1. Collect evidence with `apple-notes-debug-bundle`
2. Check Apple Notes status page
3. Contact support with request ID

## Resources
- [Apple Notes Status Page](https://status.apple-notes.com)
- [Apple Notes Support](https://docs.apple-notes.com/support)
- [Apple Notes Error Codes](https://docs.apple-notes.com/errors)

## Next Steps
For comprehensive debugging, see `apple-notes-debug-bundle`.