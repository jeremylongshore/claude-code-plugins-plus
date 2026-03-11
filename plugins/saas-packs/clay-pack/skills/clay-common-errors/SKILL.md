---
name: clay-common-errors
description: |
  Diagnose and fix Clay common errors and exceptions.
  Use when encountering Clay errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "clay error", "fix clay",
  "clay not working", "debug clay".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Common Errors

## Overview
Quick reference for the top 10 most common Clay errors and their solutions.

## Prerequisites
- Clay SDK installed
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
echo $CLAY_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `clay-rate-limits` skill.

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
const client = new Client({ timeout: 60000 });  # 60000: 1 minute in ms
```

## Examples

### Quick Diagnostic Commands
```bash
set -euo pipefail
# Check Clay status
curl -s https://status.clay.com

# Verify API connectivity
curl -I https://api.clay.com

# Check local configuration
env | grep CLAY
```

### Escalation Path
1. Collect evidence with `clay-debug-bundle`
2. Check Clay status page
3. Contact support with request ID

## Resources
- [Clay Status Page](https://status.clay.com)
- [Clay Support](https://docs.clay.com/support)
- [Clay Error Codes](https://docs.clay.com/errors)

## Next Steps
For comprehensive debugging, see `clay-debug-bundle`.