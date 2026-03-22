---
name: juicebox-common-errors
description: |
  Diagnose and fix Juicebox API errors.
  Trigger: "juicebox error", "fix juicebox", "debug juicebox".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Common Errors

## Error Reference

### 401 Authentication
```json
{"error": "invalid_api_key"}
```
**Fix:** Verify key at app.juicebox.ai > Settings.

### 403 Plan Limits
```json
{"error": "quota_exceeded"}
```
**Fix:** Check quota in dashboard, upgrade plan.

### 429 Rate Limited
**Fix:** Check `Retry-After` header. Implement exponential backoff.

### 400 Invalid Query
**Fix:** Ensure query is non-empty, check filter syntax.

### 404 Profile Not Found
**Fix:** Profile may be removed. Re-run search.

## Quick Diagnostic
```bash
curl -s -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  https://api.juicebox.ai/v1/health
```

## Resources
- [Juicebox Docs](https://docs.juicebox.work)

## Next Steps
See `juicebox-debug-bundle`.
