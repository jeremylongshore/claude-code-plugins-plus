---
name: hootsuite-common-errors
description: |
  Diagnose and fix Hootsuite common errors and exceptions.
  Use when encountering Hootsuite errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "hootsuite error", "fix hootsuite",
  "hootsuite not working", "debug hootsuite".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Common Errors

## Error Reference

### 401 Unauthorized
**Cause:** Access token expired (tokens last ~1 hour).
**Fix:** Refresh token via OAuth:
```bash
curl -X POST https://platform.hootsuite.com/oauth2/token \
  -u "$HOOTSUITE_CLIENT_ID:$HOOTSUITE_CLIENT_SECRET" \
  -d "grant_type=refresh_token&refresh_token=$HOOTSUITE_REFRESH_TOKEN"
```

### 403 Forbidden
**Cause:** App lacks required permissions or user doesn't own the resource.
**Fix:** Check app scopes in developer portal. Ensure user has access to the social profile.

### 422 Unprocessable Entity — scheduledSendTime
**Cause:** Scheduled time is in the past or invalid ISO 8601 format.
**Fix:** Always use future dates in ISO 8601: `new Date(Date.now() + 3600000).toISOString()`

### 422 — socialProfileIds
**Cause:** Profile ID invalid or disconnected.
**Fix:** List profiles first: `GET /v1/socialProfiles` and verify IDs.

### 429 Too Many Requests
**Cause:** Rate limit exceeded.
**Fix:** Implement exponential backoff. See `hootsuite-rate-limits`.

### Media Upload — State REJECTED
**Cause:** File too large, wrong format, or exceeds platform limits.
**Fix:** Check per-platform limits: Twitter images 5MB, Facebook 10MB, video varies.

### invalid_grant — Token Exchange
**Cause:** Authorization code expired (30 second lifetime) or already used.
**Fix:** Re-initiate OAuth flow — codes are single-use and expire in 30s.

### redirect_uri_mismatch
**Cause:** Redirect URI doesn't exactly match app registration.
**Fix:** Must match character-for-character, including trailing slash.

## Quick Diagnostics

```bash
# Test token validity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $HOOTSUITE_ACCESS_TOKEN" \
  https://platform.hootsuite.com/v1/me

# List profiles (verifies full API access)
curl -s -H "Authorization: Bearer $HOOTSUITE_ACCESS_TOKEN" \
  https://platform.hootsuite.com/v1/socialProfiles | python3 -m json.tool
```

## Resources

- [Hootsuite API FAQ](https://developer.hootsuite.com/docs/rest-api-faq)
- [REST API Reference](https://apidocs.hootsuite.com/docs/api/index.html)

## Next Steps

For debugging tools, see `hootsuite-debug-bundle`.
