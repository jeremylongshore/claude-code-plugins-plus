---
name: openevidence-common-errors
description: |
  Diagnose and fix OpenEvidence common errors and exceptions.
  Use when encountering OpenEvidence errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "openevidence error", "fix openevidence",
  "openevidence not working", "debug openevidence".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openevidence]
---

# OpenEvidence Common Errors

## Overview
Quick reference for the top 10 most common OpenEvidence errors and their solutions.

## Prerequisites
- OpenEvidence SDK installed
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
echo $OPENEVIDENCE_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `openevidence-rate-limits` skill.

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
# Check OpenEvidence status
curl -s https://status.openevidence.com

# Verify API connectivity
curl -I https://api.openevidence.com

# Check local configuration
env | grep OPENEVIDENCE
```

### Escalation Path
1. Collect evidence with `openevidence-debug-bundle`
2. Check OpenEvidence status page
3. Contact support with request ID

## Resources
- [OpenEvidence Status Page](https://status.openevidence.com)
- [OpenEvidence Support](https://docs.openevidence.com/support)
- [OpenEvidence Error Codes](https://docs.openevidence.com/errors)

## Next Steps
For comprehensive debugging, see `openevidence-debug-bundle`.