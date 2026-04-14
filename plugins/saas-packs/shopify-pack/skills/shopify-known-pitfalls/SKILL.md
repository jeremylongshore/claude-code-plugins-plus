---
name: shopify-known-pitfalls
description: |
  Identify and avoid Shopify API anti-patterns: ignoring userErrors, wrong API version,
  REST instead of GraphQL, missing GDPR webhooks, and webhook timeout issues.
  Use when reviewing a Shopify codebase, preparing for App Store submission, or debugging mysterious API failures.
  Trigger with phrases like "shopify mistakes", "shopify anti-patterns",
  "shopify pitfalls", "shopify what not to do", "shopify code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Known Pitfalls

## Overview

The 10 most common mistakes when building Shopify apps, with real API examples showing the wrong way and the right way.

## Prerequisites

- Existing Shopify app codebase to review or audit
- Familiarity with GraphQL Admin API query patterns and response shapes
- Access scopes configured for the APIs your app uses
- `@shopify/shopify-api` v9+ installed (for code examples)

## Instructions

Each pitfall includes a wrong-way and right-way code example. See [Pitfall Examples](references/pitfall-examples.md) for all 10 complete code comparisons.

### Pitfall #1: Not Checking userErrors (The #1 Mistake)

Shopify GraphQL mutations return HTTP 200 even when they fail. The errors are in `userErrors`. Always check `userErrors.length > 0` before accessing the result.

### Pitfall #2: Using REST When GraphQL Is Required

REST Admin API is legacy as of October 2024. New public apps after April 2025 **must** use GraphQL. GraphQL also lets you request only the fields you need.

### Pitfall #3: Ignoring API Version Deprecation

Shopify deprecates API versions ~12 months after release. Use `LATEST_API_VERSION` from `@shopify/shopify-api` and monitor `x-shopify-api-deprecated-reason` response headers.

### Pitfall #4: Missing Mandatory GDPR Webhooks

Your app **will be rejected** from the App Store without `customers/data_request`, `customers/redact`, and `shop/redact` webhook handlers.

### Pitfall #5: Webhook Handler Takes Too Long

Shopify expects a 200 response within 5 seconds. Respond immediately and queue work asynchronously, otherwise Shopify retries and creates duplicates.

### Pitfall #6: Using ProductInput on API 2024-10+

The `ProductInput` type was split into `ProductCreateInput` and `ProductUpdateInput` in 2024-10. Use the specific type for each operation.

### Pitfall #7: Not Using Cursor Pagination

Shopify uses Relay-style cursor pagination, not page numbers. Use `after` / `endCursor` with `pageInfo`.

### Pitfall #8: Requesting 250 Items Per Page

`first: 250` with nested connections creates enormous query costs that THROTTLE immediately. Use `first: 50` or smaller with nested resources.

### Pitfall #9: Exposing Admin Token in Client-Side Code

Admin API tokens have full access. Never send them to the browser — proxy through your server.

### Pitfall #10: Not Handling APP_UNINSTALLED Webhook

When a merchant uninstalls your app, clean up sessions immediately. Stale sessions cause auth redirect loops on reinstall.

## Output

- Anti-patterns identified in codebase
- Fixes prioritized (security first, then correctness)
- Prevention measures in place (linting, CI checks)

## Error Handling

| Pitfall | How to Detect | Prevention |
|---------|--------------|------------|
| Missing userErrors check | Null pointer crashes | ESLint rule or wrapper function |
| REST usage | `grep -r "clients.Rest" src/` | Migration guide + lint rule |
| Old API version | `grep -r "apiVersion" src/` | CI check against supported versions |
| Missing GDPR webhooks | App Store rejection | Pre-submit compliance checker |
| Webhook timeout | Shopify retry storms | Queue-based processing |
| ProductInput on 2024-10 | GraphQL type error | Update mutations |
| Page-based pagination | Query errors | Use cursor pagination pattern |
| `first: 250` | THROTTLED responses | Query cost budgets |
| Admin token in client | Security audit | Server-side proxy |
| No APP_UNINSTALLED | Auth loops on reinstall | Webhook handler + session cleanup |

## Examples

### Quick Pitfall Scan

Run automated detection against your Shopify codebase to find REST usage, missing userErrors checks, old API versions, hardcoded tokens, and oversized page requests.

See [Pitfall Scan Script](references/pitfall-scan-script.md) for the complete scan script.

## Resources

- [Shopify App Requirements](https://shopify.dev/docs/apps/launch/app-requirements)
- [GraphQL Migration Guide](https://shopify.dev/docs/apps/build/graphql/migrate/learn-how)
- [2024-10 Breaking Changes](https://shopify.dev/docs/api/release-notes/2024-10)
- [Webhook Best Practices](https://shopify.dev/docs/apps/build/webhooks)

## Quick Reference Card

| Pitfall | Detection | Fix |
|---------|-----------|-----|
| No userErrors check | Null crashes on mutations | Always check `userErrors.length > 0` |
| REST instead of GraphQL | `grep "clients.Rest"` | Migrate to `clients.Graphql` |
| Old API version | `grep "2023-"` | Use `LATEST_API_VERSION` from SDK |
| Missing GDPR webhooks | App Store rejection | Add 3 mandatory webhook handlers |
| Webhook timeout | Retry storms, duplicates | Respond 200 immediately, queue processing |
| ProductInput on 2024-10 | Type error | Use `ProductCreateInput` / `ProductUpdateInput` |
| Page-number pagination | Query errors | Use cursor-based with `pageInfo` |
| `first: 250` with nesting | THROTTLED | Use `first: 50` or smaller |
| Admin token in browser | Security scan | Server-side proxy only |
| No APP_UNINSTALLED | Auth loop on reinstall | Clean up sessions on uninstall |
