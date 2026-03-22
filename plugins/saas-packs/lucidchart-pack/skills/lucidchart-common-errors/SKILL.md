---
name: lucidchart-common-errors
description: |
  Diagnose and fix Lucidchart common errors.
  Trigger: "lucidchart error", "fix lucidchart", "debug lucidchart".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Common Errors

## Overview
Quick reference for Lucidchart API errors with solutions.

### 401 — Authentication Failed
**Fix:** Verify OAuth2 credentials at developer.lucid.co.

### 403 — Insufficient Permissions
**Fix:** Check OAuth scopes include required permissions.

### 404 — Document Not Found
**Fix:** Verify document ID. User must have access.

### 429 — Rate Limited
**Fix:** Implement backoff. Lucid API: 100 requests/minute.

## Quick Diagnostic
```bash
# Check API connectivity
curl -s -w "\nHTTP %{http_code}" https://api.lucid.co/v1/health 2>/dev/null || echo "Endpoint check needed"
echo $LUCID_API_KEY | head -c 10
```

## Resources
- [Lucidchart Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-debug-bundle`.
