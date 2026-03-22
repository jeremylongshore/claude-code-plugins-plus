---
name: attio-common-errors
description: |
  Diagnose and fix the top Attio REST API errors by HTTP status code.
  Real error response formats, actual error codes, and proven fixes.
  Trigger: "attio error", "fix attio", "attio not working",
  "attio 429", "attio 403", "attio 422", "debug attio".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Common Errors

## Overview

Every Attio API error returns a consistent JSON body. This skill covers the real error codes, response format, and proven solutions for each.

## Attio Error Response Format

All errors from `https://api.attio.com/v2` return this structure:

```json
{
  "status_code": 429,
  "type": "rate_limit_error",
  "code": "rate_limit_exceeded",
  "message": "Rate limit exceeded, please try again later"
}
```

Fields: `status_code` (HTTP status), `type` (error category), `code` (specific code), `message` (human-readable).

## Error Reference

### 400 Bad Request -- `invalid_request`

```json
{ "status_code": 400, "type": "invalid_request_error", "code": "invalid_request", "message": "..." }
```

**Common causes and fixes:**

| Message pattern | Cause | Fix |
|----------------|-------|-----|
| `Invalid value for attribute` | Wrong type for attribute slug | Check attribute type with `GET /v2/objects/{obj}/attributes` |
| `Cannot query historic values` | Used history param on unsupported type | Remove `show_historic` for that attribute |
| `Missing required field` | Required attribute not provided | Check `is_required` on attribute definition |
| `Invalid filter format` | Malformed filter object | Use shorthand `{ "email": "x" }` or verbose `{ "$and": [...] }` |

**Diagnostic:**
```bash
# List attributes to verify types
curl -s https://api.attio.com/v2/objects/people/attributes \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" \
  | jq '.data[] | {slug: .api_slug, type: .type, required: .is_required}'
```

### 401 Unauthorized -- `authentication_error`

```json
{ "status_code": 401, "type": "authentication_error", "code": "invalid_api_key", "message": "..." }
```

| Cause | Fix |
|-------|-----|
| Missing `Authorization` header | Add `Authorization: Bearer sk_...` |
| Token revoked or deleted | Generate new token in Attio dashboard |
| Malformed header | Ensure format is `Bearer <token>` (one space, no quotes) |

**Diagnostic:**
```bash
# Verify token works
curl -s -o /dev/null -w "%{http_code}" \
  https://api.attio.com/v2/objects \
  -H "Authorization: Bearer ${ATTIO_API_KEY}"
# Should return 200
```

### 403 Forbidden -- `insufficient_scopes`

```json
{ "status_code": 403, "type": "authorization_error", "code": "insufficient_scopes",
  "message": "Token requires 'record_permission:read-write' scope" }
```

| Operation | Required scopes |
|-----------|----------------|
| List/get records | `object_configuration:read` + `record_permission:read` |
| Create/update records | `object_configuration:read` + `record_permission:read-write` |
| List entries | `object_configuration:read` + `record_permission:read` + `list_entry:read` |
| Create/update entries | Above + `list_entry:read-write` |
| Create notes | `note:read-write` + `object_configuration:read` + `record_permission:read` |
| List tasks | `task:read` + `object_configuration:read` + `record_permission:read` + `user_management:read` |
| Manage webhooks | `webhook:read-write` |

**Fix:** Edit token in **Settings > Developers > Access tokens**, add missing scope, save. No need to regenerate.

### 404 Not Found -- `not_found`

```json
{ "status_code": 404, "type": "not_found_error", "code": "not_found", "message": "..." }
```

| Cause | Fix |
|-------|-----|
| Wrong object slug | Verify with `GET /v2/objects` -- use `api_slug` field |
| Invalid record_id | Record may have been deleted or merged |
| Wrong list slug | Verify with `GET /v2/lists` |
| Typo in endpoint path | Check path starts with `/v2/` |

### 409 Conflict -- `conflict`

Occurs when creating a record with a value that conflicts with an existing unique attribute (e.g., duplicate email or domain).

**Fix:** Use `PUT` (assert) instead of `POST` to upsert:
```typescript
// Assert: create or update matching record
await client.put("/objects/people/records", {
  data: {
    values: {
      email_addresses: ["existing@example.com"],
      name: [{ first_name: "Updated", last_name: "Name" }],
    },
  },
});
```

### 422 Unprocessable Entity -- `validation_error`

| Message pattern | Cause | Fix |
|----------------|-------|-----|
| `Invalid email address` | Malformed email string | Validate email format before sending |
| `Invalid phone number` | Not E.164 format | Prefix with country code: `+14155551234` |
| `Unknown attribute` | Attribute slug does not exist | List attributes first |
| `Invalid record reference` | target_record_id doesn't exist | Verify record exists first |

### 429 Too Many Requests -- `rate_limit_exceeded`

```json
{
  "status_code": 429,
  "type": "rate_limit_error",
  "code": "rate_limit_exceeded",
  "message": "Rate limit exceeded, please try again later"
}
```

Attio uses a **sliding window algorithm** with a **10-second window**. The `Retry-After` response header contains a date (usually the next second).

**Immediate fix:**
```typescript
if (res.status === 429) {
  const retryAfter = res.headers.get("Retry-After");
  const waitMs = retryAfter
    ? new Date(retryAfter).getTime() - Date.now()
    : 1000;
  await new Promise((r) => setTimeout(r, Math.max(waitMs, 100)));
  // Retry the request
}
```

See `attio-rate-limits` for full backoff and queue patterns.

### 500+ Server Error

Rare, but Attio may reduce rate limits during incidents. Always implement retry for 5xx.

**Check:** [status.attio.com](https://status.attio.com)

## Quick Diagnostic Script

```bash
#!/bin/bash
echo "=== Attio Diagnostic ==="
echo -n "Auth: "
curl -s -o /dev/null -w "%{http_code}" \
  https://api.attio.com/v2/objects \
  -H "Authorization: Bearer ${ATTIO_API_KEY}"
echo ""

echo -n "Status page: "
curl -s https://status.attio.com/api/v2/status.json | jq -r '.status.description'

echo "Objects:"
curl -s https://api.attio.com/v2/objects \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" \
  | jq -r '.data[].api_slug' 2>/dev/null || echo "FAILED"
```

## Error Handling Pattern

```typescript
import { AttioApiError } from "./client";

async function handleAttioError(err: AttioApiError): Promise<void> {
  switch (err.statusCode) {
    case 401: throw new Error("Attio auth failed -- check ATTIO_API_KEY");
    case 403: throw new Error(`Missing scope: ${err.message}`);
    case 404: console.warn("Resource not found, may have been deleted");  break;
    case 409: console.warn("Conflict -- use PUT to upsert instead");     break;
    case 429: /* handled by retry wrapper */ break;
    default:  throw err;
  }
}
```

## Resources

- [Attio REST API Overview](https://docs.attio.com/rest-api/overview)
- [Attio Rate Limiting Guide](https://docs.attio.com/rest-api/guides/rate-limiting)
- [Attio Status Page](https://status.attio.com)

## Next Steps

For evidence collection, see `attio-debug-bundle`. For retry patterns, see `attio-rate-limits`.
