---
name: mindtickle-common-errors
description: |
  Diagnose and fix MindTickle common errors.
  Trigger: "mindtickle error", "fix mindtickle", "debug mindtickle".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Common Errors

## Overview
Quick reference for MindTickle API errors with solutions.

### 401 — Invalid API Key
**Fix:** Verify key at MindTickle Admin > Integrations.

### 403 — Insufficient Permissions
**Fix:** API key needs admin-level access.

### 404 — Resource Not Found
**Fix:** Verify module/user/team ID exists.

### 429 — Rate Limited
**Fix:** MindTickle API: 60 requests/minute. Implement backoff.

## Quick Diagnostic
```bash
# Check API connectivity
curl -s -w "\nHTTP %{http_code}" https://api.mindtickle.com/v2/health 2>/dev/null || echo "Endpoint check needed"
echo $MINDTICKLE_API_KEY | head -c 10
```

## Resources
- [MindTickle Docs](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-debug-bundle`.
