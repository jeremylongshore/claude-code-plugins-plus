---
name: intercom-common-errors
description: |
  Diagnose and fix Intercom API errors by HTTP status code and error type.
  Use when encountering Intercom errors, debugging failed API requests,
  or troubleshooting integration issues.
  Trigger with phrases like "intercom error", "fix intercom",
  "intercom not working", "debug intercom", "intercom 401", "intercom 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Common Errors

## Overview

Quick reference for Intercom API errors by HTTP status code, with real error response shapes and proven solutions.

## Intercom Error Response Shape

All Intercom errors return this structure:

```json
{
  "type": "error.list",
  "request_id": "req_abc123",
  "errors": [
    {
      "code": "unauthorized",
      "message": "Access Token Invalid"
    }
  ]
}
```

## Error Reference

### 401 Unauthorized

```json
{
  "type": "error.list",
  "errors": [{ "code": "unauthorized", "message": "Access Token Invalid" }]
}
```

**Causes:**
- Access token is expired, revoked, or malformed
- Using a test token against production (or vice versa)
- Token was regenerated in Developer Hub but not updated in app

**Fix:**

```bash
# Verify token works
curl -s https://api.intercom.io/me \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  -H "Accept: application/json" | jq '.type'
# Should return "admin"

# If invalid, regenerate at:
# app.intercom.com > Settings > Developer Hub > Your App > Authentication
```

---

### 403 Forbidden

```json
{
  "type": "error.list",
  "errors": [{ "code": "forbidden", "message": "You do not have permission to access this resource" }]
}
```

**Causes:**
- OAuth app missing required scope
- Trying to access a resource in another workspace
- Admin permissions insufficient

**Fix:** Add the required OAuth scope in Developer Hub > OAuth Scopes.

---

### 404 Not Found

```json
{
  "type": "error.list",
  "errors": [{ "code": "not_found", "message": "User Not Found" }]
}
```

**Causes:**
- Contact, conversation, or article ID is invalid
- Resource was deleted
- Using `user_id` where `contact_id` is expected (or vice versa)

**Fix:**

```typescript
// Always check existence before operating
try {
  const contact = await client.contacts.find({ contactId: id });
} catch (err) {
  if (err instanceof IntercomError && err.statusCode === 404) {
    console.log(`Contact ${id} not found, skipping`);
  }
}
```

---

### 409 Conflict

```json
{
  "type": "error.list",
  "errors": [{ "code": "conflict", "message": "A contact matching those details already exists with id=abc123" }]
}
```

**Causes:**
- Creating a contact with a duplicate `external_id` or `email`
- Race condition in concurrent contact creation

**Fix:**

```typescript
// Search first, create if not found
async function findOrCreateContact(email: string, externalId: string) {
  const existing = await client.contacts.search({
    query: { field: "email", operator: "=", value: email },
  });

  if (existing.data.length > 0) {
    return existing.data[0];
  }

  return client.contacts.create({
    role: "user",
    email,
    externalId,
  });
}
```

---

### 422 Unprocessable Entity

```json
{
  "type": "error.list",
  "errors": [{ "code": "parameter_invalid", "message": "email is not a valid email address" }]
}
```

**Causes:**
- Invalid field value (bad email format, wrong type)
- Missing required field
- Custom attribute name exceeds 190 characters

**Fix:** Validate inputs before sending. Check the `errors` array for specifics.

---

### 429 Rate Limit Exceeded

```json
{
  "type": "error.list",
  "errors": [{ "code": "rate_limit_exceeded", "message": "Rate limit exceeded" }]
}
```

**Response headers:**

```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1711100060
```

**Limits:** 10,000 req/min per app, 25,000 req/min per workspace.

**Fix:**

```typescript
import { IntercomError } from "intercom-client";

async function withBackoff<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (err instanceof IntercomError && err.statusCode === 429) {
        if (attempt === maxRetries) throw err;
        const resetAt = err.headers?.["x-ratelimit-reset"];
        const waitMs = resetAt
          ? (parseInt(resetAt) * 1000) - Date.now() + 1000
          : 1000 * Math.pow(2, attempt);
        console.log(`Rate limited, waiting ${waitMs}ms`);
        await new Promise(r => setTimeout(r, Math.max(waitMs, 1000)));
      } else {
        throw err;
      }
    }
  }
  throw new Error("Unreachable");
}
```

---

### 500/502/503 Server Errors

**Causes:** Intercom-side issue, not your fault.

**Fix:**

```bash
# 1. Check Intercom status
curl -s https://status.intercom.com/api/v2/summary.json | jq '.status'

# 2. Retry with backoff (same pattern as 429)
# 3. If persistent, contact Intercom support with request_id
```

## Quick Diagnostic Script

```bash
#!/bin/bash
TOKEN="${INTERCOM_ACCESS_TOKEN}"

echo "=== Intercom API Diagnostics ==="

# Test auth
echo -n "Auth: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  https://api.intercom.io/me)
echo "$STATUS $([ "$STATUS" = "200" ] && echo "OK" || echo "FAIL")"

# Check rate limits
echo -n "Rate limit remaining: "
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i x-ratelimit-remaining

# Intercom status
echo -n "Intercom status: "
curl -s https://status.intercom.com/api/v2/status.json | jq -r '.status.description'
```

## Error Handling

| Error Code | HTTP | Retryable | Action |
|------------|------|-----------|--------|
| `unauthorized` | 401 | No | Regenerate token |
| `forbidden` | 403 | No | Add OAuth scope |
| `not_found` | 404 | No | Verify resource ID |
| `conflict` | 409 | No | Search before create |
| `parameter_invalid` | 422 | No | Fix input data |
| `rate_limit_exceeded` | 429 | Yes | Backoff and retry |
| `server_error` | 500+ | Yes | Retry, check status page |

## Resources

- [Error Codes](https://developers.intercom.com/docs/references/rest-api/errors/error-codes)
- [HTTP Responses](https://developers.intercom.com/docs/references/rest-api/errors/http-responses)
- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)
- [Intercom Status](https://status.intercom.com)

## Next Steps

For comprehensive debugging, see `intercom-debug-bundle`.
