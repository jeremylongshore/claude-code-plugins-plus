---
name: openevidence-common-errors
description: |
  Diagnose and fix OpenEvidence common errors.
  Trigger: "openevidence error", "fix openevidence", "debug openevidence".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Common Errors

## Overview
Quick reference for OpenEvidence API errors with solutions.

### 401 — Authentication Failed
**Fix:** Verify API key at OpenEvidence developer portal.

### 403 — Organization Access Denied
**Fix:** Verify org ID and API key permissions.

### 422 — Invalid Query
**Fix:** Clinical question must be medical in nature.

### 429 — Rate Limited
**Fix:** Implement backoff. Check `Retry-After` header.

### 503 — Service Unavailable
**Fix:** DeepConsult queue may be full. Retry after delay.

## Quick Diagnostic
```bash
# Check API connectivity
curl -s -w "\nHTTP %{http_code}" https://api.openevidence.com/v1/health 2>/dev/null || echo "Endpoint check needed"
echo $OPENEVIDENCE_API_KEY | head -c 10
```

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-debug-bundle`.
