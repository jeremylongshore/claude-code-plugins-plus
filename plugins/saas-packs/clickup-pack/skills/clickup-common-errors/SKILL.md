---
name: clickup-common-errors
description: |
  Diagnose and fix ClickUp common errors and exceptions.
  Use when encountering ClickUp errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "clickup error", "fix clickup",
  "clickup not working", "debug clickup".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickup]
---

# ClickUp Common Errors

## Overview

Quick reference for the top 10 most common ClickUp errors and their solutions.


## Prerequisites
- ClickUp SDK installed
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

### Integration Not Connected
**Error Message:**
```
401 Unauthorized: Integration token is not connected to this workspace
```

**Cause:** API integration hasn't been added to the workspace, or token lacks page access.

**Solution:**
```bash
# Add integration in workspace settings → Connections
# Share specific pages/databases with the integration
# Use "internal integration" for full workspace access

```

---

### Page Not Found
**Error Message:**
```
404 Not Found: Could not find page with ID abc-123
```

**Cause:** Page was deleted, archived, or integration lacks access to it.

**Solution:**
# Check if page was moved to trash (search with in_trash filter)
# Verify integration has access (page must be shared with integration)
# Use search API instead of direct ID access


---

### Rate Limit Exceeded
**Error Message:**
```
429 Too Many Requests: Rate limit exceeded. Retry after 1 second.
```

**Cause:** Exceeded 3 requests/second (typical for productivity APIs).

**Solution:**
```typescript
# Productivity APIs have strict per-second limits (3-10 req/s)
# Use batch endpoints where available
# Implement request queue with 334ms minimum spacing

```



## Examples

### Quick Diagnostic Commands
```bash
# Check ClickUp status
curl -s https://status.clickup.com

# Verify API connectivity
curl -I https://api.clickup.com

# Check local configuration
env | grep CLICKUP
```

### Escalation Path
1. Collect evidence with `clickup-debug-bundle`
2. Check ClickUp status page
3. Contact support with request ID

## Resources
- [ClickUp Status Page](https://status.clickup.com)
- [ClickUp Support](https://docs.clickup.com/support)
- [ClickUp Error Codes](https://docs.clickup.com/errors)

## Next Steps
For comprehensive debugging, see `clickup-debug-bundle`.