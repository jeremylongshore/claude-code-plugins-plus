---
name: shopify-common-errors
description: |
  Diagnose and fix common Shopify API errors including 401, 403, 422, 429, and GraphQL errors.
  Use when encountering Shopify errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "shopify error", "fix shopify",
  "shopify not working", "debug shopify", "shopify 422".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Common Errors

## Overview

Quick-reference guide for the most common Shopify API errors with real error messages, causes, and fixes.

## Prerequisites

- Shopify app with API credentials configured
- Access to application logs or console output

## Instructions

### Step 1: Identify the Error Type

Check whether the error is an HTTP status code error or a GraphQL `userErrors` response.

### Step 2: Match Error Below and Apply Fix

---

### 401 Unauthorized

**Actual Shopify Response:**
```json
{
  "errors": "[API] Invalid API key or access token (unrecognized login or wrong password)"
}
```

**Causes:**
- Access token expired (merchant uninstalled and reinstalled)
- Wrong `X-Shopify-Access-Token` header
- Using a Storefront API token for Admin API or vice versa

**Fix:**
```bash
# Verify token format:
# Admin API token: shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (32 hex chars)
# Storefront API token: different format, starts with shpat_ too
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://your-store.myshopify.com/admin/api/2024-10/shop.json"
# Should return 200
```

---

### 403 Forbidden

**Actual Shopify Response:**
```json
{
  "errors": "This action requires merchant approval for read_orders scope."
}
```

**Cause:** Your app's access token lacks the required scope.

**Fix:** Add the needed scope to your app config and re-trigger OAuth:
```toml
# shopify.app.toml
[access_scopes]
scopes = "read_products,write_products,read_orders,write_orders"
```

---

### 404 Not Found

**Actual Shopify Response:**
```json
{
  "errors": "Not Found"
}
```

**Causes:**
- Wrong API version in URL
- Resource was deleted
- Store domain is incorrect

**Fix:**
```bash
# Verify the API version exists
curl -s "https://your-store.myshopify.com/admin/api/2024-10/shop.json" \
  -H "X-Shopify-Access-Token: $TOKEN"

# Check available API versions
curl -s "https://your-store.myshopify.com/admin/api/versions.json" \
  -H "X-Shopify-Access-Token: $TOKEN"
```

---

### 422 Unprocessable Entity

**Actual Shopify Responses:**
```json
{
  "errors": {
    "title": ["can't be blank"],
    "handle": ["has already been taken"]
  }
}
```

```json
{
  "errors": {
    "base": ["Product cannot be saved: Title is too long (maximum is 255 characters)"]
  }
}
```

**Common 422 triggers:**
- Missing required fields (title, etc.)
- Duplicate handle/slug
- Invalid metafield type
- Price format issues (must be string like "29.99")
- Invalid country/province codes

**Fix:** Check the `errors` object or `userErrors` array for specific field-level messages.

---

### 429 Too Many Requests (Rate Limited)

**REST API Response:**
```
HTTP/1.1 429 Too Many Requests
Retry-After: 2.0
```

**GraphQL Response (in body, returns 200):**
```json
{
  "errors": [
    {
      "message": "Throttled",
      "extensions": {
        "code": "THROTTLED",
        "documentation": "https://shopify.dev/api/usage/rate-limits"
      }
    }
  ],
  "extensions": {
    "cost": {
      "requestedQueryCost": 752,
      "actualQueryCost": null,
      "throttleStatus": {
        "maximumAvailable": 2000,
        "currentlyAvailable": 0,
        "restoreRate": 100
      }
    }
  }
}
```

**Fix:** See `shopify-rate-limits` skill for complete backoff implementation.

---

### GraphQL userErrors (200 with Errors)

**Critical: Shopify returns HTTP 200 even when mutations fail.**

```json
{
  "data": {
    "productCreate": {
      "product": null,
      "userErrors": [
        {
          "field": ["title"],
          "message": "Title can't be blank",
          "code": "BLANK"
        }
      ]
    }
  }
}
```

**Always check `userErrors` after every mutation:**
```typescript
const response = await client.request(mutation, { variables });
const result = response.data.productCreate;

if (result.userErrors.length > 0) {
  // These are validation errors, NOT HTTP errors
  for (const err of result.userErrors) {
    console.error(`Field ${err.field?.join(".")}: ${err.message} (${err.code})`);
  }
  throw new Error("Shopify validation failed");
}
```

---

### 5xx Server Errors

**Shopify internal errors — not your fault, but you must handle them.**

```json
{
  "errors": "Internal Server Error"
}
```

**Fix:** Retry with exponential backoff. Include the `X-Request-Id` header value when reporting to Shopify support.

```typescript
// The X-Request-Id header is in every Shopify response
const requestId = error.response?.headers?.["x-request-id"];
console.error(`Shopify 500 error. Request ID: ${requestId}`);
```

## Output

- Error identified by HTTP status or GraphQL userErrors
- Root cause determined
- Fix applied and verified

## Error Handling

| Status | Name | Retryable | Action |
|--------|------|-----------|--------|
| 401 | Unauthorized | No | Re-authenticate, verify token |
| 403 | Forbidden | No | Add missing scope, re-OAuth |
| 404 | Not Found | No | Check URL, API version, resource ID |
| 422 | Unprocessable | No | Fix validation errors in request body |
| 429 | Throttled | Yes | Backoff using `Retry-After` header |
| 500 | Server Error | Yes | Retry with backoff, report X-Request-Id |
| 503 | Unavailable | Yes | Shopify is overloaded, retry later |

## Examples

### Quick Diagnostic Script

```bash
#!/bin/bash
STORE="your-store.myshopify.com"
TOKEN="$SHOPIFY_ACCESS_TOKEN"
VERSION="2024-10"

echo "=== Shopify Diagnostic ==="

# 1. Test auth
echo -n "Auth: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/$VERSION/shop.json"
echo ""

# 2. Check scopes
echo "Scopes:"
curl -s -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/oauth/access_scopes.json" | python3 -m json.tool

# 3. Check API versions
echo "API Versions:"
curl -s -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/versions.json" | python3 -c "
import json, sys
versions = json.load(sys.stdin)['supported_versions']
for v in versions[:5]:
    print(f'  {v[\"handle\"]} {\"(latest)\" if v.get(\"latest\") else \"\"}')"

# 4. Shopify status
echo "Shopify Status: https://www.shopifystatus.com"
```

## Resources

- [Shopify API Response Codes](https://shopify.dev/docs/api/usage/response-codes)
- [GraphQL Error Handling](https://shopify.dev/docs/apps/build/graphql/basics/queries#error-handling)
- [Shopify Status Page](https://www.shopifystatus.com)

## Next Steps

For comprehensive debugging, see `shopify-debug-bundle`.
