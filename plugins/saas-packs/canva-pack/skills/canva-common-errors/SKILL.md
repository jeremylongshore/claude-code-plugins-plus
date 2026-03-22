---
name: canva-common-errors
description: |
  Diagnose and fix Canva Connect API errors and HTTP status codes.
  Use when encountering Canva errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "canva error", "fix canva",
  "canva not working", "debug canva", "canva 401", "canva 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Common Errors

## Overview

Quick reference for the most common Canva Connect API errors at `api.canva.com/rest/v1/*` with real HTTP status codes, error payloads, and fixes.

## Error Reference

### 401 Unauthorized — Token Expired or Invalid

```json
{ "error": "invalid_token", "message": "The access token is invalid or expired" }
```

**Cause:** Access tokens expire after ~4 hours. Token may be malformed or revoked.

**Fix:**
```typescript
// Refresh the token
const res = await fetch('https://api.canva.com/rest/v1/oauth/token', {
  method: 'POST',
  headers: {
    'Authorization': `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString('base64')}`,
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    grant_type: 'refresh_token',
    refresh_token: storedRefreshToken,
  }),
});
const { access_token, refresh_token } = await res.json();
// IMPORTANT: Each refresh token is single-use — store the new one
```

---

### 403 Forbidden — Missing Scope or Insufficient Permissions

```json
{ "error": "insufficient_scope", "message": "Required scope: design:content:write" }
```

**Cause:** Your integration doesn't have the required OAuth scope enabled, or the user isn't authorized for the resource.

**Fix:**
1. Check required scope in the [Scopes Reference](https://www.canva.dev/docs/connect/appendix/scopes/)
2. Enable the scope in your integration settings at [canva.dev](https://www.canva.dev)
3. Re-authorize the user — existing tokens don't gain new scopes retroactively

---

### 429 Too Many Requests — Rate Limited

```json
{ "error": "rate_limit_exceeded", "message": "Rate limit exceeded" }
```

**Cause:** Exceeded per-endpoint rate limits. Key limits:

| Endpoint | Limit |
|----------|-------|
| `GET /v1/users/me` | 10 req/min |
| `POST /v1/designs` | 20 req/min |
| `GET /v1/designs` | 100 req/min |
| `POST /v1/exports` | 75 req/5min, 500/24hr (per user) |
| `POST /v1/asset-uploads` | 30 req/min |
| `POST /v1/autofills` | 60 req/min |
| `POST /v1/folders` | 20 req/min |

**Fix:**
```typescript
async function canvaAPIWithRetry(path: string, token: string, opts: RequestInit = {}) {
  const res = await fetch(`https://api.canva.com/rest/v1${path}`, {
    ...opts,
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', ...opts.headers },
  });

  if (res.status === 429) {
    const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
    console.warn(`Rate limited — waiting ${retryAfter}s`);
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    return canvaAPIWithRetry(path, token, opts); // Retry once
  }

  if (!res.ok) throw new Error(`Canva ${res.status}: ${await res.text()}`);
  return res.json();
}
```

---

### 404 Not Found — Resource Missing

**Cause:** Design, asset, template, or folder ID doesn't exist, was deleted, or the user doesn't have access.

**Fix:**
```bash
# Verify the resource exists — check design ID
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.canva.com/rest/v1/designs/$DESIGN_ID | jq '.design.id'
```

---

### 400 Bad Request — Validation Error

**Common cases:**
```json
{ "error": "validation_error", "message": "Design title invalid" }
```

| Field | Constraint |
|-------|-----------|
| `title` | 1-255 characters |
| `design_type.width` | 40-8000 pixels |
| `design_type.height` | 40-8000 pixels |
| `format.quality` (JPG) | 1-100 |
| `format.width/height` (export) | 40-25000 pixels |
| Chart data | Max 100 rows, 20 columns |

---

### Export Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `license_required` | Design uses premium elements | User needs Canva Pro subscription |
| `approval_required` | Design pending approval | User must approve in Canva |
| `internal_failure` | Canva server error | Retry after delay |

---

### OAuth Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `invalid_client` | Wrong client_id or secret | Check credentials |
| `invalid_grant` | Auth code expired/reused | Restart OAuth flow |
| `invalid_scope` | Scope not enabled | Enable in integration settings |
| `unsupported_grant_type` | Wrong grant_type | Use `authorization_code` or `refresh_token` |

## Quick Diagnostic Commands

```bash
# Check your token
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.canva.com/rest/v1/users/me | jq

# Check API connectivity
curl -sI https://api.canva.com/rest/v1/users/me \
  -H "Authorization: Bearer $TOKEN" 2>&1 | head -5

# Verify environment variables
echo "Client ID: ${CANVA_CLIENT_ID:+[SET]}"
echo "Access Token: ${CANVA_ACCESS_TOKEN:+[SET]}"
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ENOTFOUND` | DNS failure | Check network connectivity |
| `ETIMEDOUT` | Network timeout | Increase timeout, check firewall |
| `invalid_token` | Expired access token | Refresh via OAuth endpoint |
| `insufficient_scope` | Missing permission | Enable scope, re-authorize |

## Resources

- [API Requests & Responses](https://www.canva.dev/docs/connect/api-requests-responses/)
- [Scopes Reference](https://www.canva.dev/docs/connect/appendix/scopes/)

## Next Steps

For comprehensive debugging, see `canva-debug-bundle`.
