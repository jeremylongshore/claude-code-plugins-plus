---
name: linktree-common-errors
description: |
  Diagnose and fix Linktree common errors.
  Trigger: "linktree error", "fix linktree", "debug linktree".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Common Errors

## Overview
Quick reference for Linktree API errors with solutions.

### 400 — Invalid Request
**Fix:** Check request body format, ensure URLs are valid.

### 401 — Authentication Failed
**Fix:** Verify API key at linktr.ee developer portal.

### 404 — Profile/Link Not Found
**Fix:** Verify profile username or link ID exists.

### 429 — Rate Limited
**Fix:** Implement exponential backoff. Check `Retry-After` header.

## Quick Diagnostic
```bash
# Check API connectivity
curl -s -w "\nHTTP %{http_code}" https://api.linktr.ee/v1/health 2>/dev/null || echo "Endpoint check needed"
echo $LINKTREE_API_KEY | head -c 10
```

## Resources
- [Linktree Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-debug-bundle`.
