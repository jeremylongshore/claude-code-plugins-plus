---
name: groq-common-errors
description: |
  Diagnose and fix Groq common errors and exceptions.
  Use when encountering Groq errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "groq error", "fix groq",
  "groq not working", "debug groq".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Groq Common Errors

## Overview
Quick reference for the top 10 most common Groq errors and their solutions.

## Prerequisites
- Groq SDK installed
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
echo $GROQ_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `groq-rate-limits` skill.

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
# Check Groq status
curl -s https://status.groq.com

# Verify API connectivity
curl -I https://api.groq.com

# Check local configuration
env | grep GROQ
```

### Escalation Path
1. Collect evidence with `groq-debug-bundle`
2. Check Groq status page
3. Contact support with request ID

## Resources
- [Groq Status Page](https://status.groq.com)
- [Groq Support](https://docs.groq.com/support)
- [Groq Error Codes](https://docs.groq.com/errors)

## Next Steps
For comprehensive debugging, see `groq-debug-bundle`.