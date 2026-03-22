---
name: customerio-common-errors
description: |
  Diagnose and fix Customer.io common errors and exceptions.
  Use when encountering Customer.io errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "customerio error", "fix customerio",
  "customerio not working", "debug customerio".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io Common Errors

## Overview
Quick reference for the top 10 most common Customer.io errors and their solutions.

## Prerequisites
- Customer.io SDK installed
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
echo $CUSTOMERIO_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `customerio-rate-limits` skill.

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
# Check Customer.io status
curl -s https://status.customerio.com

# Verify API connectivity
curl -I https://api.customerio.com

# Check local configuration
env | grep CUSTOMERIO
```

### Escalation Path
1. Collect evidence with `customerio-debug-bundle`
2. Check Customer.io status page
3. Contact support with request ID

## Resources
- [Customer.io Status Page](https://status.customerio.com)
- [Customer.io Support](https://docs.customerio.com/support)
- [Customer.io Error Codes](https://docs.customerio.com/errors)

## Next Steps
For comprehensive debugging, see `customerio-debug-bundle`.