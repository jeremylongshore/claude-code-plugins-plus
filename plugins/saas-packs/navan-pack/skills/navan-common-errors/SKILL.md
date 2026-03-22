---
name: navan-common-errors
description: |
  Diagnose and fix Navan common errors.
  Trigger: "navan error", "fix navan", "debug navan".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Common Errors

## Overview
Quick reference for Navan API errors with solutions.

### 401 — Authentication Failed
**Fix:** Verify API key at Navan Admin > Integrations.

### 403 — Company Access Denied
**Fix:** Check company_id matches your organization.

### 404 — Trip/Expense Not Found
**Fix:** Verify resource ID exists.

### 429 — Rate Limited
**Fix:** Navan API: 120 requests/minute. Implement backoff.

### 409 — Conflict
**Fix:** Duplicate booking or expense. Check idempotency key.

## Quick Diagnostic
```bash
# Check API connectivity
curl -s -w "\nHTTP %{http_code}" https://api.navan.com/v1/health 2>/dev/null || echo "Endpoint check needed"
echo $NAVAN_API_KEY | head -c 10
```

## Resources
- [Navan Docs](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-debug-bundle`.
