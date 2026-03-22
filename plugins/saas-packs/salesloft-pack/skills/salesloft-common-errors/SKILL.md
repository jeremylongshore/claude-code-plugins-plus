---
name: salesloft-common-errors
description: |
  Diagnose and fix SalesLoft API errors: 401, 403, 422, 429, and 5xx.
  Use when encountering SalesLoft errors, debugging failed requests,
  or troubleshooting OAuth token issues.
  Trigger: "salesloft error", "fix salesloft", "salesloft not working", "salesloft 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Common Errors

## Overview

Quick reference for the most common SalesLoft REST API v2 errors. All errors return JSON with a message field. Rate limiting uses a cost-based system (600 cost/minute).

## Error Reference

### 401 Unauthorized -- Invalid or Expired Token

```json
{ "error": "Not authorized", "error_description": "The access token is invalid" }
```

**Causes:** Token expired, revoked, or wrong environment key.

**Fix:**
```typescript
// Check if token works
const { data } = await api.get('/me.json').catch(err => {
  if (err.response?.status === 401) {
    console.error('Token invalid. Refreshing...');
    return refreshAccessToken(storedRefreshToken);
  }
  throw err;
});
```

### 403 Forbidden -- Insufficient Scopes

```json
{ "error": "Forbidden", "error_description": "Insufficient scope for this resource" }
```

**Fix:** Check app scopes in [developer portal](https://developers.salesloft.com). Common issue: using user-level OAuth for team-level endpoints (cadences, team templates).

### 404 Not Found -- Wrong Endpoint or Deleted Resource

```bash
# Verify endpoint format -- all endpoints end with .json
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.salesloft.com/v2/people/12345.json
# NOT /people/12345 (missing .json suffix)
```

### 422 Unprocessable Entity -- Validation Errors

```json
{
  "errors": [
    { "attribute": "email_address", "message": "is required" },
    { "attribute": "email_address", "message": "has already been taken" }
  ]
}
```

**Common 422 causes:**
| Field | Error | Solution |
|-------|-------|----------|
| `email_address` | required | Must include when creating a person |
| `email_address` | already taken | Use `GET /people.json?email_addresses[]=x` first |
| `cadence_id` | not active | Cadence must have `current_state: 'active'` |
| `person_id` | already enrolled | Check existing cadence memberships |

### 429 Too Many Requests -- Rate Limit Exceeded

```
X-RateLimit-Limit-Per-Minute: 600
X-RateLimit-Remaining-Per-Minute: 0
Retry-After: 42
```

**SalesLoft uses cost-based rate limiting:**
- Default: each request costs 1 point
- Pages 101-150: 3 points per request
- Pages 151-250: 8 points per request
- Pages 251-500: 10 points per request
- Pages 501+: 30 points per request

```typescript
// Auto-retry with Retry-After header
api.interceptors.response.use(undefined, async (error) => {
  if (error.response?.status === 429) {
    const wait = parseInt(error.response.headers['retry-after'] || '60');
    await new Promise(r => setTimeout(r, wait * 1000));
    return api.request(error.config);
  }
  throw error;
});
```

### 5xx Server Errors

**Fix:** Retry with exponential backoff. Check [status.salesloft.com](https://status.salesloft.com) for outages.

## Quick Diagnostic

```bash
# 1. Verify token
curl -s -H "Authorization: Bearer $SALESLOFT_API_KEY" \
  https://api.salesloft.com/v2/me.json | jq '.data.email'

# 2. Check API status
curl -s https://status.salesloft.com/api/v2/status.json | jq '.status'

# 3. Test specific endpoint
curl -v -H "Authorization: Bearer $SALESLOFT_API_KEY" \
  'https://api.salesloft.com/v2/people.json?per_page=1'

# 4. Check rate limit remaining
curl -sI -H "Authorization: Bearer $SALESLOFT_API_KEY" \
  https://api.salesloft.com/v2/people.json | grep -i ratelimit
```

## Error Handling

| Status | Retryable | Action |
|--------|-----------|--------|
| 401 | No | Refresh token or re-authenticate |
| 403 | No | Update app scopes in developer portal |
| 404 | No | Check endpoint URL (must end in `.json`) |
| 422 | No | Fix request payload |
| 429 | Yes | Wait for `Retry-After` header value |
| 500-503 | Yes | Exponential backoff, check status page |

## Resources

- [SalesLoft API Basics](https://developers.salesloft.com/docs/platform/api-basics/)
- [Rate Limits](https://developers.salesloft.com/docs/platform/api-basics/rate-limits/)
- [Status Page](https://status.salesloft.com)

## Next Steps

For comprehensive debugging, see `salesloft-debug-bundle`.
