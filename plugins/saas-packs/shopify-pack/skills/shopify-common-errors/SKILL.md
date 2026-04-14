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

**Response:** `"[API] Invalid API key or access token (unrecognized login or wrong password)"`

**Causes:** Access token expired (merchant uninstalled/reinstalled), wrong header, or using Storefront token for Admin API.

**Fix:** Verify token format (`shpat_` + 32 hex chars) and test with a simple `shop.json` GET request.

---

### 403 Forbidden

**Response:** `"This action requires merchant approval for read_orders scope."`

**Fix:** Add the needed scope to `shopify.app.toml` under `[access_scopes]` and re-trigger OAuth.

---

### 404 Not Found

**Causes:** Wrong API version in URL, resource was deleted, or store domain is incorrect.

**Fix:** Verify the API version exists by checking `/admin/api/versions.json`.

---

### 422 Unprocessable Entity

**Common triggers:** Missing required fields, duplicate handle/slug, invalid metafield type, price format issues (must be string like `"29.99"`), invalid country/province codes.

**Fix:** Check the `errors` object or `userErrors` array for specific field-level messages.

---

### 429 Too Many Requests (Rate Limited)

REST returns `429` with `Retry-After` header. GraphQL returns `200` with `THROTTLED` error code in the body and zero `currentlyAvailable` points.

**Fix:** See `shopify-rate-limits` skill for complete backoff implementation.

---

### GraphQL userErrors (200 with Errors)

**Critical: Shopify returns HTTP 200 even when mutations fail.** Always check `userErrors` after every mutation:

```typescript
const result = response.data.productCreate;
if (result.userErrors.length > 0) {
  for (const err of result.userErrors) {
    console.error(`Field ${err.field?.join(".")}: ${err.message} (${err.code})`);
  }
  throw new Error("Shopify validation failed");
}
```

---

### 5xx Server Errors

Shopify internal errors -- not your fault. Retry with exponential backoff and capture the `X-Request-Id` header for support tickets.

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

Run auth, scope, and API version checks in one pass.

See [Diagnostic Script](references/diagnostic-script.md) for the complete shell script.

## Resources

- [Shopify API Response Codes](https://shopify.dev/docs/api/usage/response-codes)
- [GraphQL Error Handling](https://shopify.dev/docs/apps/build/graphql/basics/queries#error-handling)
- [Shopify Status Page](https://www.shopifystatus.com)
