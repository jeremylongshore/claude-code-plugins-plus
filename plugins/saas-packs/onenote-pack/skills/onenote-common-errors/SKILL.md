---
name: onenote-common-errors
description: |
  Diagnose and fix OneNote common errors.
  Trigger: "onenote error", "fix onenote", "debug onenote".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Common Errors

## Overview
Quick reference for OneNote API errors with solutions.

### 401 — Unauthorized
**Fix:** Token expired. Refresh OAuth token. Note: app-only auth deprecated since March 2025 — use delegated auth.

### 403 — Forbidden
**Fix:** Missing Graph permissions. Ensure `Notes.ReadWrite` scope.

### 404 — Not Found
**Fix:** Notebook/section/page ID invalid or user lacks access.

### 429 — Throttled
**Fix:** Microsoft Graph: 10,000 requests/10 min. Check `Retry-After`.

### 507 — Insufficient Storage
**Fix:** OneNote storage quota exceeded. Archive old notebooks.

## Quick Diagnostic
```bash
# Check API connectivity
curl -s -w "\nHTTP %{http_code}" https://graph.microsoft.com/v1.0/me/onenote/health 2>/dev/null || echo "Endpoint check needed"
echo $MICROSOFT_GRAPH_TOKEN | head -c 10
```

## Resources
- [OneNote Docs](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-debug-bundle`.
