---
name: exa-common-errors
description: |
  Diagnose and fix Exa common errors and exceptions.
  Use when encountering Exa errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "exa error", "fix exa",
  "exa not working", "debug exa".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa Common Errors

## Overview
Quick reference for the top 10 most common Exa errors and their solutions.

## Prerequisites
- Exa SDK installed
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
echo $EXA_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `exa-rate-limits` skill.

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
# Check Exa status
curl -s https://status.exa.com

# Verify API connectivity
curl -I https://api.exa.com

# Check local configuration
env | grep EXA
```

### Escalation Path
1. Collect evidence with `exa-debug-bundle`
2. Check Exa status page
3. Contact support with request ID

## Resources
- [Exa Status Page](https://status.exa.com)
- [Exa Support](https://docs.exa.com/support)
- [Exa Error Codes](https://docs.exa.com/errors)

## Next Steps
For comprehensive debugging, see `exa-debug-bundle`.