---
name: windsurf-common-errors
description: |
  Diagnose and fix Windsurf common errors and exceptions.
  Use when encountering Windsurf errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "windsurf error", "fix windsurf",
  "windsurf not working", "debug windsurf".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Common Errors

## Overview
Quick reference for the top 10 most common Windsurf errors and their solutions.

## Prerequisites
- Windsurf SDK installed
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
echo $WINDSURF_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `windsurf-rate-limits` skill.

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
# Check Windsurf status
curl -s https://status.windsurf.com

# Verify API connectivity
curl -I https://api.windsurf.com

# Check local configuration
env | grep WINDSURF
```

### Escalation Path
1. Collect evidence with `windsurf-debug-bundle`
2. Check Windsurf status page
3. Contact support with request ID

## Resources
- [Windsurf Status Page](https://status.windsurf.com)
- [Windsurf Support](https://docs.windsurf.com/support)
- [Windsurf Error Codes](https://docs.windsurf.com/errors)

## Next Steps
For comprehensive debugging, see `windsurf-debug-bundle`.