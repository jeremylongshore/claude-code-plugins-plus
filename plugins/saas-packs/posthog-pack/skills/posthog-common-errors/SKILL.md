---
name: posthog-common-errors
description: |
  Diagnose and fix PostHog common errors and exceptions.
  Use when encountering PostHog errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "posthog error", "fix posthog",
  "posthog not working", "debug posthog".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# PostHog Common Errors

## Overview
Quick reference for the top 10 most common PostHog errors and their solutions.

## Prerequisites
- PostHog SDK installed
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
echo $POSTHOG_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `posthog-rate-limits` skill.

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
# Check PostHog status
curl -s https://status.posthog.com

# Verify API connectivity
curl -I https://api.posthog.com

# Check local configuration
env | grep POSTHOG
```

### Escalation Path
1. Collect evidence with `posthog-debug-bundle`
2. Check PostHog status page
3. Contact support with request ID

## Resources
- [PostHog Status Page](https://status.posthog.com)
- [PostHog Support](https://docs.posthog.com/support)
- [PostHog Error Codes](https://docs.posthog.com/errors)

## Next Steps
For comprehensive debugging, see `posthog-debug-bundle`.