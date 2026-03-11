---
name: replit-common-errors
description: |
  Diagnose and fix Replit common errors and exceptions.
  Use when encountering Replit errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "replit error", "fix replit",
  "replit not working", "debug replit".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Common Errors

## Overview
Quick reference for the top 10 most common Replit errors and their solutions.

## Prerequisites
- Replit SDK installed
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
echo $REPLIT_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `replit-rate-limits` skill.

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
# Check Replit status
curl -s https://status.replit.com

# Verify API connectivity
curl -I https://api.replit.com

# Check local configuration
env | grep REPLIT
```

### Escalation Path
1. Collect evidence with `replit-debug-bundle`
2. Check Replit status page
3. Contact support with request ID

## Resources
- [Replit Status Page](https://status.replit.com)
- [Replit Support](https://docs.replit.com/support)
- [Replit Error Codes](https://docs.replit.com/errors)

## Next Steps
For comprehensive debugging, see `replit-debug-bundle`.