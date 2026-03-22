---
name: hubspot-common-errors
description: |
  Diagnose and fix common HubSpot API errors with real error responses.
  Use when encountering HubSpot errors, debugging failed API requests,
  or troubleshooting integration issues with specific HTTP status codes.
  Trigger with phrases like "hubspot error", "fix hubspot", "hubspot 401",
  "hubspot 429", "hubspot not working", "debug hubspot API".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Common Errors

## Overview

Quick reference for the most common HubSpot API errors, their real error response bodies, and solutions.

## Prerequisites

- `@hubspot/api-client` installed
- API credentials configured
- Access to application logs

## Instructions

### Step 1: Identify the Error

Check the HTTP status code and response body. HubSpot returns structured errors:

```json
{
  "status": "error",
  "message": "One or more validation errors occurred",
  "correlationId": "abc123-def456",
  "category": "VALIDATION_ERROR",
  "errors": [
    {
      "message": "Property values were not valid: [{\"isValid\":false,\"message\":\"...\"}]",
      "context": { "propertyName": "email" }
    }
  ]
}
```

### Step 2: Match and Fix

---

### 401 Unauthorized

**Real response:**
```json
{
  "status": "error",
  "message": "Authentication credentials not found. This API supports OAuth 2.0 authentication and you can find more details at https://developers.hubspot.com/docs/methods/auth/oauth-overview",
  "correlationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "category": "INVALID_AUTHENTICATION"
}
```

**Causes:**
- Missing `Authorization: Bearer` header
- Expired OAuth access token (30-minute TTL)
- Revoked or regenerated private app token

**Fix:**
```bash
# Verify token is set and valid
curl -s https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" | jq .status
# Should return null (success) or "error"
```

---

### 403 Forbidden

**Real response:**
```json
{
  "status": "error",
  "message": "This access token does not have proper permissions. (requires any of [crm.objects.contacts.write])",
  "correlationId": "...",
  "category": "MISSING_SCOPES"
}
```

**Fix:** Add the missing scope to your private app in Settings > Integrations > Private Apps, then regenerate the token.

---

### 409 Conflict

**Real response:**
```json
{
  "status": "error",
  "message": "Contact already exists. Existing ID: 12345",
  "correlationId": "...",
  "category": "CONFLICT"
}
```

**Fix:** Search before creating, or use batch upsert:
```typescript
// Use search-first pattern
const existing = await client.crm.contacts.searchApi.doSearch({
  filterGroups: [{
    filters: [{ propertyName: 'email', operator: 'EQ', value: email }],
  }],
  properties: ['email'],
  limit: 1, after: 0, sorts: [],
});

if (existing.results.length > 0) {
  await client.crm.contacts.basicApi.update(existing.results[0].id, { properties });
} else {
  await client.crm.contacts.basicApi.create({ properties, associations: [] });
}
```

---

### 429 Too Many Requests

**Real response:**
```json
{
  "status": "error",
  "message": "You have reached your secondly limit.",
  "correlationId": "...",
  "category": "RATE_LIMITS"
}
```

**Headers returned:**
```
X-HubSpot-RateLimit-Daily: 500000
X-HubSpot-RateLimit-Daily-Remaining: 499950
X-HubSpot-RateLimit-Secondly: 10
X-HubSpot-RateLimit-Secondly-Remaining: 0
Retry-After: 1
```

**Fix:** Honor `Retry-After` header and use SDK built-in retries:
```typescript
const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3, // auto-retries 429s with backoff
});
```

---

### 400 Validation Error (Property)

**Real response:**
```json
{
  "status": "error",
  "message": "Property values were not valid: [{\"isValid\":false,\"message\":\"Property \\\"nonexistent_field\\\" does not exist\",\"error\":\"PROPERTY_DOESNT_EXIST\",\"name\":\"nonexistent_field\"}]",
  "correlationId": "...",
  "category": "VALIDATION_ERROR"
}
```

**Fix:**
```typescript
// List available properties for an object type
// GET /crm/v3/properties/{objectType}
const properties = await client.crm.properties.coreApi.getAll('contacts');
const propNames = properties.results.map(p => p.name);
console.log('Available contact properties:', propNames);
```

---

### 400 Invalid Association

**Real response:**
```json
{
  "status": "error",
  "message": "association type id 999 doesn't exist between contact and company",
  "correlationId": "...",
  "category": "VALIDATION_ERROR"
}
```

**Common association type IDs:**

| From | To | TypeId | Label |
|------|----|--------|-------|
| Contact | Company | 1 | Primary |
| Contact | Deal | 3 | -- |
| Company | Deal | 5 | -- |
| Contact | Ticket | 16 | -- |
| Note | Contact | 202 | -- |
| Task | Contact | 204 | -- |
| Note | Deal | 214 | -- |

---

### 404 Not Found (Archived Record)

**Real response:**
```json
{
  "status": "error",
  "message": "Object not found. objectType=contacts, objectId=12345. It may have been deleted.",
  "correlationId": "...",
  "category": "OBJECT_NOT_FOUND"
}
```

**Fix:** The record may be archived. Check with `archived=true`:
```typescript
const contact = await client.crm.contacts.basicApi.getById(
  '12345',
  ['email'],
  undefined,
  undefined,
  true // archived = true
);
```

## Output

- Error identified by HTTP status and category
- Root cause determined
- Fix applied with working code
- Verified resolution

## Error Handling

### Catch-All Error Handler

```typescript
import { HttpError } from '@hubspot/api-client/lib/codegen/crm/contacts';

async function handleHubSpotError(error: any): Promise<void> {
  const status = error?.code || error?.statusCode || 500;
  const body = typeof error?.body === 'string' ? JSON.parse(error.body) : error?.body || {};

  console.error(`HubSpot API Error [${status}]`, {
    message: body.message,
    category: body.category,
    correlationId: body.correlationId,
    errors: body.errors,
  });

  // Save correlationId for support tickets
  if (status >= 500) {
    console.error('HubSpot server error. Check https://status.hubspot.com');
  }
}
```

## Examples

### Quick Diagnostic Commands

```bash
# Check HubSpot API status
curl -s https://status.hubspot.com/api/v2/summary.json | jq '.status.description'

# Verify token and scopes
curl -s https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"

# Check rate limit headers
curl -sI https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i ratelimit
```

## Resources

- [HubSpot Error Handling Guide](https://developers.hubspot.com/docs/api-reference/error-handling)
- [HubSpot Status Page](https://status.hubspot.com)
- [Association Type IDs](https://developers.hubspot.com/docs/guides/api/crm/associations)

## Next Steps

For comprehensive debugging, see `hubspot-debug-bundle`.
