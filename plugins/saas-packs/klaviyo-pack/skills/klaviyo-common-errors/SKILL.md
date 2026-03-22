---
name: klaviyo-common-errors
description: |
  Diagnose and fix Klaviyo common errors and exceptions.
  Use when encountering Klaviyo errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "klaviyo error", "fix klaviyo",
  "klaviyo not working", "debug klaviyo".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klaviyo]
---

# Klaviyo Common Errors

## Overview
Quick reference for the top 10 most common Klaviyo errors and their solutions.

## Prerequisites
- Klaviyo SDK installed
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
echo $KLAVIYO_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `klaviyo-rate-limits` skill.

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
# Check Klaviyo status
curl -s https://status.klaviyo.com

# Verify API connectivity
curl -I https://api.klaviyo.com

# Check local configuration
env | grep KLAVIYO
```

### Escalation Path
1. Collect evidence with `klaviyo-debug-bundle`
2. Check Klaviyo status page
3. Contact support with request ID

## Resources
- [Klaviyo Status Page](https://status.klaviyo.com)
- [Klaviyo Support](https://docs.klaviyo.com/support)
- [Klaviyo Error Codes](https://docs.klaviyo.com/errors)

## Next Steps
For comprehensive debugging, see `klaviyo-debug-bundle`.