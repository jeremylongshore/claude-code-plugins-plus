---
name: klaviyo-common-errors
description: |
  Diagnose and fix common Klaviyo API errors and exceptions.
  Use when encountering Klaviyo 4xx/5xx errors, debugging failed requests,
  or troubleshooting SDK integration issues.
  Trigger with phrases like "klaviyo error", "fix klaviyo",
  "klaviyo not working", "debug klaviyo", "klaviyo 400", "klaviyo 429".
allowed-tools: Read, Grep, Bash(curl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Common Errors

## Overview

Quick reference for the most common Klaviyo API errors with real error payloads, root causes, and solutions.

## Prerequisites

- `klaviyo-api` SDK installed
- API credentials configured
- Access to application logs

## Instructions

### Step 1: Identify the Error

Klaviyo returns JSON:API error responses. Extract the status code and error detail:

```typescript
try {
  await profilesApi.createProfile(payload);
} catch (error: any) {
  console.error('Status:', error.status);
  console.error('Errors:', JSON.stringify(error.body?.errors, null, 2));
  // error.body.errors[] has: { id, code, title, detail, source }
}
```

### Step 2: Match and Fix

---

### 400 -- Bad Request (Validation Error)

**Actual Klaviyo response:**
```json
{
  "errors": [{
    "id": "abc-123",
    "code": "invalid",
    "title": "Invalid input.",
    "detail": "The email field is required.",
    "source": { "pointer": "/data/attributes/email" }
  }]
}
```

**Common causes:**
- Missing required field (email, metric name, list name)
- Invalid phone number format (must be E.164: `+15551234567`)
- Invalid filter syntax in query params
- Wrong `type` value in JSON:API payload
- Sending `snake_case` instead of `camelCase` (SDK uses camelCase)

**Fix:**
```typescript
// Wrong: snake_case
{ first_name: 'Jane', phone_number: '+155...' }

// Right: camelCase (SDK convention)
{ firstName: 'Jane', phoneNumber: '+15551234567' }
```

---

### 401 -- Unauthorized

**Actual response:**
```json
{
  "errors": [{
    "code": "not_authenticated",
    "title": "Authentication credentials were not provided.",
    "detail": "Missing or invalid Authorization header."
  }]
}
```

**Root causes:**
1. Missing `KLAVIYO_PRIVATE_KEY` environment variable
2. Using a public key (6 chars) instead of private key (`pk_*`)
3. API key was revoked or rotated

**Fix:**
```bash
# Verify key is set and starts with pk_
echo $KLAVIYO_PRIVATE_KEY | head -c 3
# Should print: pk_

# Test with cURL
curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"
```

---

### 403 -- Forbidden (Missing Scope)

**Actual response:**
```json
{
  "errors": [{
    "code": "permission_denied",
    "title": "You do not have permission to perform this action.",
    "detail": "The API key does not have the required scope: profiles:write"
  }]
}
```

**Fix:** Generate a new API key with the required scope at **Settings > API Keys > Create Private API Key**.

| Endpoint | Required Scope |
|----------|---------------|
| `POST /api/profiles/` | `profiles:write` |
| `GET /api/segments/` | `segments:read` |
| `POST /api/events/` | `events:write` |
| `POST /api/campaigns/` | `campaigns:write` |
| `POST /api/data-privacy-deletion-jobs/` | `data-privacy:write` |

---

### 404 -- Not Found

**Typical causes:**
- Wrong resource ID (profile, list, segment, campaign)
- Using v1/v2 URL paths instead of new API (`/api/v2/` is dead, use `/api/`)
- Resource was deleted

**Fix:**
```typescript
// Verify the resource exists first
const lists = await listsApi.getLists();
const targetList = lists.body.data.find(l => l.attributes.name === 'Newsletter');
if (!targetList) throw new Error('List not found');
```

---

### 409 -- Conflict (Duplicate)

**Actual response:**
```json
{
  "errors": [{
    "code": "duplicate",
    "title": "Conflict.",
    "detail": "A profile already exists with the email customer@example.com"
  }]
}
```

**Fix:** Use `createOrUpdateProfile` (upsert) instead of `createProfile`:
```typescript
// This handles both create and update
await profilesApi.createOrUpdateProfile({
  data: {
    type: 'profile' as any,
    attributes: { email: 'customer@example.com', firstName: 'Updated' },
  },
});
```

---

### 429 -- Rate Limited

**Headers on 429 response:**
```
Retry-After: 10
```

**Klaviyo rate limits (per-account, fixed window):**
| Window | Limit |
|--------|-------|
| Burst (1 second) | 75 requests |
| Steady (1 minute) | 700 requests |

**Note:** When rate limited, `RateLimit-Remaining` and `RateLimit-Reset` headers are NOT returned. Only `Retry-After` (integer seconds) is present.

**Fix:** Honor `Retry-After` header:
```typescript
catch (error: any) {
  if (error.status === 429) {
    const retryAfter = parseInt(error.headers?.['retry-after'] || '10');
    console.log(`Rate limited. Waiting ${retryAfter}s...`);
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    // Retry the request
  }
}
```

---

### 500/503 -- Klaviyo Server Error

**Fix:**
1. Check [Klaviyo Status Page](https://status.klaviyo.com)
2. Retry with exponential backoff (see `klaviyo-rate-limits`)
3. If persistent, check Klaviyo's [changelog](https://developers.klaviyo.com/en/docs/changelog_) for known issues

---

### Common SDK-Level Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find module 'klaviyo-api'` | Wrong package | `npm install klaviyo-api` (not `@klaviyo/sdk`) |
| `TypeError: ... is not a constructor` | Wrong import | Use `new ProfilesApi(session)` not `new KlaviyoClient()` |
| `response.data is undefined` | Wrong access pattern | Use `response.body.data` (not `response.data`) |
| `filter is not valid` | Bad filter syntax | Use `equals(field,"value")` not `field = value` |

## Quick Diagnostic Commands

```bash
# Check Klaviyo API health
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"

# Check Klaviyo status page
curl -s https://status.klaviyo.com/api/v2/status.json | python3 -m json.tool

# Verify local env
env | grep KLAVIYO
npm list klaviyo-api
```

## Escalation Path

1. Collect evidence with `klaviyo-debug-bundle`
2. Check [status.klaviyo.com](https://status.klaviyo.com)
3. Open ticket at [Klaviyo Support](https://support.klaviyo.com) with request IDs from error responses

## Resources

- [Rate Limits & Error Handling](https://developers.klaviyo.com/en/docs/rate_limits_and_error_handling)
- [API Error Alerts](https://developers.klaviyo.com/en/docs/review_api_error_alerts)
- [Klaviyo Status Page](https://status.klaviyo.com)

## Next Steps

For comprehensive debugging, see `klaviyo-debug-bundle`.
