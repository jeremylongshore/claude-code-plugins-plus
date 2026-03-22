---
name: onenote-common-errors
description: |
  Diagnose and fix OneNote common errors and exceptions.
  Use when encountering OneNote errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "onenote error", "fix onenote",
  "onenote not working", "debug onenote".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, onenote]
---

# OneNote Common Errors

## Overview

Quick reference for the top 10 most common OneNote errors and their solutions.


## Prerequisites
- OneNote SDK installed
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
# Check OneNote status
curl -s https://status.onenote.com

# Verify API connectivity
curl -I https://api.onenote.com

# Check local configuration
env | grep ONENOTE
```

### Escalation Path
1. Collect evidence with `onenote-debug-bundle`
2. Check OneNote status page
3. Contact support with request ID

## Resources
- [OneNote Status Page](https://status.onenote.com)
- [OneNote Support](https://docs.onenote.com/support)
- [OneNote Error Codes](https://docs.onenote.com/errors)

## Next Steps
For comprehensive debugging, see `onenote-debug-bundle`.