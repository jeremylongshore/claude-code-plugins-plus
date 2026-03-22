---
name: miro-common-errors
description: |
  Diagnose and fix Miro REST API v2 errors by HTTP status code.
  Use when encountering Miro API errors, debugging failed requests,
  or troubleshooting authentication and permission issues.
  Trigger with phrases like "miro error", "fix miro",
  "miro not working", "debug miro", "miro 401", "miro 403", "miro 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, errors, troubleshooting]
compatible-with: claude-code
---

# Miro Common Errors

## Overview

Quick reference for Miro REST API v2 errors organized by HTTP status code, with real error response bodies and proven fixes.

## Prerequisites

- Access token configured
- `curl` available for diagnostic requests

## Quick Diagnostic

```bash
# 1. Verify API connectivity
curl -s -o /dev/null -w "%{http_code}" https://api.miro.com/v2/boards \
  -H "Authorization: Bearer $MIRO_ACCESS_TOKEN"

# 2. Check token validity
curl -s https://api.miro.com/v1/oauth-token \
  -H "Authorization: Bearer $MIRO_ACCESS_TOKEN" | jq

# 3. Check Miro status page
curl -s https://status.miro.com/api/v2/status.json | jq '.status.description'
```

## Error Reference

### 400 — Bad Request

```json
{
  "status": 400,
  "code": "invalidInput",
  "message": "Could not resolve the value for parameter: data.content",
  "context": { "fields": [{ "field": "data.content", "message": "Required" }] }
}
```

**Common causes:**
- Missing required fields in request body
- Wrong data types (string instead of number for position)
- Invalid enum values (e.g., `shape: 'oval'` — correct is `shape: 'circle'`)

**Fix:** Cross-reference your request body with the [REST API reference](https://developers.miro.com/docs/rest-api-reference-guide). Each item type has specific required fields.

**Sticky note required fields:** `data.content`, `data.shape` (`square` or `rectangle`)
**Shape required fields:** `data.shape` (see `miro-sdk-patterns` for valid shapes)
**Connector required fields:** `startItem.id`, `endItem.id`

---

### 401 — Unauthorized

```json
{
  "status": 401,
  "code": "tokenNotProvided",
  "message": "Access token is not provided"
}
```

```json
{
  "status": 401,
  "code": "tokenExpired",
  "message": "Access token has expired"
}
```

**Common causes:**
- Missing `Authorization: Bearer <token>` header
- Access token expired (tokens last 3599 seconds / ~1 hour)
- Using client_id/client_secret instead of access_token

**Fix:**
```bash
# Check if token is set
echo "Token length: ${#MIRO_ACCESS_TOKEN}"

# Refresh expired token
curl -X POST https://api.miro.com/v1/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token" \
  -d "client_id=$MIRO_CLIENT_ID" \
  -d "client_secret=$MIRO_CLIENT_SECRET" \
  -d "refresh_token=$MIRO_REFRESH_TOKEN"
```

---

### 403 — Forbidden

```json
{
  "status": 403,
  "code": "insufficientPermissions",
  "message": "Required scopes: boards:write",
  "context": { "requiredScopes": ["boards:write"] }
}
```

**Common causes:**
- Token lacks required OAuth scope
- User does not have board-level permission (viewer trying to write)
- Team-level restrictions prevent the operation

**Fix:**
1. Check which scopes your token has vs. what the endpoint requires
2. Update scopes in your Miro app settings at https://developers.miro.com
3. Re-authorize the user to get a token with updated scopes

| Endpoint Category | Required Scope |
|-------------------|---------------|
| GET boards/items | `boards:read` |
| POST/PATCH/DELETE boards/items | `boards:write` |
| GET team/members | `team:read` |
| Organization endpoints | `organizations:read` |

---

### 404 — Not Found

```json
{
  "status": 404,
  "code": "boardNotFound",
  "message": "Board not found or access denied"
}
```

**Common causes:**
- Board ID is wrong or has been deleted
- Item ID references a deleted item
- Token owner does not have access to the board

**Fix:**
```bash
# Verify board exists and you have access
curl -s https://api.miro.com/v2/boards/$BOARD_ID \
  -H "Authorization: Bearer $MIRO_ACCESS_TOKEN" | jq '.id, .name'

# List boards to find correct ID
curl -s "https://api.miro.com/v2/boards?limit=10" \
  -H "Authorization: Bearer $MIRO_ACCESS_TOKEN" | jq '.data[] | {id, name}'
```

---

### 409 — Conflict

```json
{
  "status": 409,
  "code": "duplicateTagTitle",
  "message": "A tag with this title already exists"
}
```

**Common causes:**
- Creating a tag with a title that already exists on the board
- Concurrent modifications to the same item

**Fix:** Fetch existing tags first and reuse their IDs instead of creating duplicates.

---

### 429 — Rate Limited

```json
{
  "status": 429,
  "code": "rateLimitExceeded",
  "message": "Rate limit exceeded"
}
```

**Response headers:**
```
X-RateLimit-Limit: 100000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1700000060
Retry-After: 30
```

**Fix:** Honor the `Retry-After` header. See `miro-rate-limits` for complete backoff patterns. The global limit is 100,000 credits/minute.

---

### 500 / 502 / 503 — Server Error

**Common causes:**
- Miro platform issue (check https://status.miro.com)
- Transient infrastructure error

**Fix:**
1. Check Miro status page
2. Retry with exponential backoff (see `miro-rate-limits`)
3. If persistent (>5 min), it is a Miro-side issue — enable fallback mode

## Programmatic Error Handler

```typescript
async function handleMiroError(response: Response, context: string): Promise<never> {
  const body = await response.json().catch(() => ({}));

  switch (response.status) {
    case 401:
      console.error(`[Miro:${context}] Token expired/invalid. Refreshing...`);
      // Trigger token refresh
      break;
    case 403:
      console.error(`[Miro:${context}] Missing scopes: ${body.context?.requiredScopes?.join(', ')}`);
      break;
    case 429:
      const retryAfter = response.headers.get('Retry-After') ?? '60';
      console.warn(`[Miro:${context}] Rate limited. Retry after ${retryAfter}s`);
      break;
    default:
      console.error(`[Miro:${context}] ${response.status}: ${body.message ?? 'Unknown error'}`);
  }

  throw new Error(`Miro API ${response.status}: ${body.message ?? context}`);
}
```

## Escalation Path

1. Run diagnostics above
2. Collect evidence with `miro-debug-bundle`
3. Check https://status.miro.com
4. File support ticket with request ID (from `X-Request-Id` response header)

## Resources

- [Miro Status Page](https://status.miro.com)
- [REST API Reference Guide](https://developers.miro.com/docs/rest-api-reference-guide)
- [Permission Scopes](https://developers.miro.com/reference/scopes)
- [Rate Limiting](https://developers.miro.com/reference/rate-limiting)

## Next Steps

For comprehensive debugging, see `miro-debug-bundle`.
