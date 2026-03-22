---
name: webflow-common-errors
description: |
  Diagnose and fix Webflow Data API v2 errors — 400, 401, 403, 404, 409, 429, 500.
  Use when encountering Webflow API errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "webflow error", "fix webflow",
  "webflow not working", "debug webflow", "webflow 429", "webflow 401".
allowed-tools: Read, Grep, Bash(curl:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Common Errors

## Overview

Quick reference for the most common Webflow Data API v2 errors, their root causes,
and concrete solutions. Covers every HTTP status code the API returns.

## Prerequisites

- `webflow-api` SDK installed
- API token configured
- Access to application logs

## HTTP Error Reference

### 400 Bad Request — Invalid Input

```
{ "code": "validation_error", "message": "Invalid field data" }
```

**Common causes:**
- Missing required field (`name` and `slug` are always required for CMS items)
- Wrong field type (sending string for a Number field)
- Invalid slug format (must be lowercase, hyphens only, no spaces)
- Bulk request exceeds 100 items

**Fix:**

```typescript
// Check collection schema before creating items
const collection = await webflow.collections.get(collectionId);
const requiredFields = collection.fields?.filter(f => f.isRequired);
console.log("Required fields:", requiredFields?.map(f => `${f.slug} (${f.type})`));

// Validate slug format
function isValidSlug(slug: string): boolean {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug);
}
```

---

### 401 Unauthorized — Invalid Token

```
{ "code": "unauthorized", "message": "Not authorized" }
```

**Common causes:**
- Token revoked or expired
- Token copied with extra whitespace
- Using v1 API key format with v2 endpoints

**Fix:**

```bash
# Verify token works
curl -s https://api.webflow.com/v2/sites \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"

# Check for whitespace issues
echo -n "$WEBFLOW_API_TOKEN" | wc -c
```

```typescript
// Programmatic token check
async function verifyToken(): Promise<boolean> {
  try {
    await webflow.sites.list();
    return true;
  } catch (err: any) {
    if (err.statusCode === 401) {
      console.error("Token invalid. Generate new token at developers.webflow.com");
      return false;
    }
    throw err;
  }
}
```

---

### 403 Forbidden — Missing Scope

```
{ "code": "forbidden", "message": "Insufficient permissions" }
```

**Common causes:**
- Token missing required scope (e.g., calling CMS write with only `cms:read`)
- Site token used for a different site
- OAuth app not authorized for the scope

**Fix:**

```typescript
// Required scopes by operation
const SCOPE_MAP: Record<string, string> = {
  "sites.list": "sites:read",
  "sites.publish": "sites:write",
  "collections.list": "cms:read",
  "collections.items.createItem": "cms:write",
  "pages.list": "pages:read",
  "forms.list": "forms:read",
  "products.list": "ecommerce:read",
  "products.create": "ecommerce:write",
  "orders.list": "ecommerce:read",
  "orders.refund": "ecommerce:write",
};
```

Generate a new token with the correct scopes at `https://developers.webflow.com`.

---

### 404 Not Found — Wrong Resource ID

```
{ "code": "not_found", "message": "Resource not found" }
```

**Common causes:**
- Wrong `site_id`, `collection_id`, or `item_id`
- Resource deleted
- Using staging ID against live endpoint (or vice versa)

**Fix:**

```typescript
// Discovery chain: always start from sites.list()
async function discoverResources() {
  const { sites } = await webflow.sites.list();
  console.log("Sites:", sites?.map(s => `${s.displayName}: ${s.id}`));

  for (const site of sites!) {
    const { collections } = await webflow.collections.list(site.id!);
    console.log(`  Collections in ${site.displayName}:`);
    for (const col of collections!) {
      console.log(`    ${col.displayName}: ${col.id}`);
    }
  }
}
```

---

### 409 Conflict — Duplicate Resource

```
{ "code": "conflict", "message": "Item with slug already exists" }
```

**Common causes:**
- CMS item with same slug already exists in collection
- Trying to create a resource that already exists

**Fix:**

```typescript
// Check for existing slug before creating
async function createOrUpdate(collectionId: string, slug: string, fieldData: Record<string, any>) {
  const { items } = await webflow.collections.items.listItems(collectionId);
  const existing = items?.find(i => i.fieldData?.slug === slug);

  if (existing) {
    return webflow.collections.items.updateItem(collectionId, existing.id!, { fieldData });
  }
  return webflow.collections.items.createItem(collectionId, { fieldData: { slug, ...fieldData } });
}
```

---

### 429 Too Many Requests — Rate Limited

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

**Common causes:**
- Exceeded per-key rate limit
- Site publish called more than once per minute
- Rapid-fire requests without throttling

**Fix:**

```typescript
// The SDK auto-retries 429s with exponential backoff.
// For manual control:
async function waitForRateLimit(retryAfterSeconds: number) {
  console.log(`Rate limited. Waiting ${retryAfterSeconds}s...`);
  await new Promise(r => setTimeout(r, retryAfterSeconds * 1000));
}
```

See `webflow-rate-limits` for comprehensive rate limit handling.

---

### 500/502/503 — Webflow Server Error

**Fix:**

```bash
# 1. Check Webflow status
curl -s https://status.webflow.com/api/v2/status.json | jq '.status'

# 2. Retry with backoff (SDK handles this automatically)
# 3. If persistent, check Webflow status page and open support ticket
```

## Quick Diagnostic Commands

```bash
# Test API connectivity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites

# Check rate limit headers
curl -v -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites 2>&1 | grep -i "x-ratelimit\|retry-after"

# List sites (quick token verification)
curl -s -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites | jq '.sites[].displayName'

# Check Webflow platform status
curl -s https://status.webflow.com/api/v2/status.json | jq '.status.description'
```

## Error Handling Pattern

```typescript
import { WebflowClient } from "webflow-api";

async function resilientCall<T>(
  operation: () => Promise<T>,
  label: string
): Promise<T> {
  try {
    return await operation();
  } catch (err: any) {
    const status = err.statusCode || err.status;

    const actionMap: Record<number, string> = {
      400: "Fix request payload — check field names and types",
      401: "Rotate token at developers.webflow.com",
      403: "Add missing scope to token",
      404: "Verify resource IDs with discovery chain",
      409: "Handle duplicate — update instead of create",
      429: "Wait for Retry-After header (SDK auto-retries)",
      500: "Webflow server error — retry later",
    };

    console.error(`[${label}] HTTP ${status}: ${actionMap[status] || "Unknown error"}`);
    console.error(`  Message: ${err.message}`);
    console.error(`  Body: ${JSON.stringify(err.body)}`);

    throw err;
  }
}
```

## Escalation Path

1. Check error code against this reference
2. Run diagnostic commands above
3. Collect evidence with `webflow-debug-bundle`
4. Check [Webflow Status](https://status.webflow.com)
5. Open support ticket with request ID and error details

## Output

- Identified error cause from HTTP status code
- Applied targeted fix
- Verified resolution

## Resources

- [Webflow API Error Codes](https://developers.webflow.com/data/reference/rest-introduction)
- [Webflow Status Page](https://status.webflow.com)
- [Rate Limits Reference](https://developers.webflow.com/data/reference/rate-limits)

## Next Steps

For comprehensive debugging, see `webflow-debug-bundle`.
