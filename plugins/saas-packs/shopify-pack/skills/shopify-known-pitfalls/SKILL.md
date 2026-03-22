---
name: shopify-known-pitfalls
description: |
  Identify and avoid Shopify API anti-patterns: ignoring userErrors, wrong API version,
  REST instead of GraphQL, missing GDPR webhooks, and webhook timeout issues.
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

- Shopify app codebase to review
- Understanding of GraphQL Admin API patterns

## Instructions

### Pitfall #1: Not Checking userErrors (The #1 Mistake)

Shopify GraphQL mutations return HTTP 200 even when they fail. The errors are in `userErrors`.

```typescript
// WRONG — assumes 200 means success
const response = await client.request(PRODUCT_CREATE, { variables });
const product = response.data.productCreate.product; // null!
console.log(product.title); // TypeError: Cannot read property 'title' of null

// RIGHT — always check userErrors
const response = await client.request(PRODUCT_CREATE, { variables });
const { product, userErrors } = response.data.productCreate;
if (userErrors.length > 0) {
  console.error("Shopify validation failed:", userErrors);
  // [{ field: ["title"], message: "Title can't be blank", code: "BLANK" }]
  throw new ShopifyValidationError(userErrors);
}
console.log(product.title); // Safe
```

---

### Pitfall #2: Using REST When GraphQL Is Required

REST Admin API is legacy as of October 2024. New public apps after April 2025 **must** use GraphQL.

```typescript
// WRONG — REST API (legacy, higher bandwidth, returns all fields)
const { body } = await restClient.get({ path: "products", query: { limit: 250 } });
// Returns EVERYTHING: body_html, template_suffix, published_scope...

// RIGHT — GraphQL (get only what you need)
const response = await graphqlClient.request(`{
  products(first: 50) {
    edges { node { id title status } }
    pageInfo { hasNextPage endCursor }
  }
}`);
```

---

### Pitfall #3: Ignoring API Version Deprecation

Shopify deprecates API versions ~12 months after release. Your app will break silently when your version is removed.

```typescript
// WRONG — hardcoded old version, no monitoring
const shopify = shopifyApi({ apiVersion: "2023-04" }); // DEAD version

// RIGHT — use recent stable version, monitor deprecation
const shopify = shopifyApi({ apiVersion: "2024-10" });

// Monitor for deprecation warnings in responses
function checkDeprecation(headers: Headers): void {
  const warning = headers.get("x-shopify-api-deprecated-reason");
  if (warning) {
    console.warn(`[DEPRECATION] ${warning}`);
    // Alert team to upgrade
  }
}
```

---

### Pitfall #4: Missing Mandatory GDPR Webhooks

Your app **will be rejected** from the App Store without these three webhooks.

```typescript
// WRONG — no GDPR handlers
// shopify.app.toml has no webhook subscriptions
// App Store review: REJECTED

// RIGHT — all three mandatory webhooks
// shopify.app.toml:
// [[webhooks.subscriptions]]
// topics = ["customers/data_request"]
// uri = "/webhooks/gdpr/data-request"
//
// [[webhooks.subscriptions]]
// topics = ["customers/redact"]
// uri = "/webhooks/gdpr/customers-redact"
//
// [[webhooks.subscriptions]]
// topics = ["shop/redact"]
// uri = "/webhooks/gdpr/shop-redact"
```

---

### Pitfall #5: Webhook Handler Takes Too Long

Shopify expects a 200 response within 5 seconds. If your handler does API calls inline, it will time out and Shopify will retry — causing duplicates.

```typescript
// WRONG — processing inline, takes 10+ seconds
app.post("/webhooks", rawBodyParser, async (req, res) => {
  const order = JSON.parse(req.body);
  await syncToERP(order);           // 3 seconds
  await updateInventory(order);      // 2 seconds
  await sendNotification(order);     // 2 seconds
  res.status(200).send("OK");       // 7+ seconds — Shopify considers this failed!
});

// RIGHT — respond immediately, process async
app.post("/webhooks", rawBodyParser, async (req, res) => {
  res.status(200).send("OK"); // Respond within milliseconds

  // Process asynchronously
  const order = JSON.parse(req.body);
  await queue.add("process-order", order);
});
```

---

### Pitfall #6: Using ProductInput on API 2024-10+

The `ProductInput` type was split into `ProductCreateInput` and `ProductUpdateInput` in 2024-10.

```typescript
// WRONG — old ProductInput type (breaks on 2024-10+)
mutation($input: ProductInput!) {  // ERROR: ProductInput is not defined
  productCreate(input: $input) { ... }
}

// RIGHT — separate types for create and update
mutation($input: ProductCreateInput!) {
  productCreate(product: $input) { ... }  // Note: "product:" not "input:"
}

mutation($input: ProductUpdateInput!) {
  productUpdate(product: $input) { ... }
}
```

---

### Pitfall #7: Not Using Cursor Pagination

Shopify uses Relay-style cursor pagination, not page numbers.

```typescript
// WRONG — trying page numbers (doesn't work in GraphQL)
const page1 = await query("products(first: 50, page: 1)"); // ERROR
const page2 = await query("products(first: 50, page: 2)"); // ERROR

// RIGHT — cursor-based pagination
let cursor = null;
let hasMore = true;
while (hasMore) {
  const response = await client.request(`{
    products(first: 50, after: ${cursor ? `"${cursor}"` : "null"}) {
      edges { node { id title } cursor }
      pageInfo { hasNextPage endCursor }
    }
  }`);
  // Process products...
  cursor = response.data.products.pageInfo.endCursor;
  hasMore = response.data.products.pageInfo.hasNextPage;
}
```

---

### Pitfall #8: Requesting 250 Items Per Page

`first: 250` with nested connections creates enormous query costs that THROTTLE immediately.

```typescript
// WRONG — cost explosion
// products(first: 250) × variants(first: 100) = 25,000 point cost
const response = await client.request(`{
  products(first: 250) {
    edges { node {
      variants(first: 100) { edges { node { id price } } }
    }}
  }
}`);
// Result: THROTTLED immediately

// RIGHT — reasonable page sizes
const response = await client.request(`{
  products(first: 50) {
    edges { node {
      variants(first: 10) { edges { node { id price } } }
    }}
    pageInfo { hasNextPage endCursor }
  }
}`);
```

---

### Pitfall #9: Exposing Admin Token in Client-Side Code

Admin API tokens have full access. Never send them to the browser.

```typescript
// WRONG — admin token in React component
const response = await fetch(`https://store.myshopify.com/admin/api/2024-10/graphql.json`, {
  headers: { "X-Shopify-Access-Token": "shpat_xxx" }, // Visible in browser devtools!
});

// RIGHT — proxy through your server
// Client calls your API, your server calls Shopify
const response = await fetch("/api/shopify/products"); // Your server

// Server-side only
app.get("/api/shopify/products", async (req, res) => {
  const { admin } = await authenticate.admin(req);
  const data = await admin.graphql(PRODUCTS_QUERY);
  res.json(data);
});
```

---

### Pitfall #10: Not Handling APP_UNINSTALLED Webhook

When a merchant uninstalls your app, you need to clean up sessions. Otherwise, stale sessions cause auth loops.

```typescript
// WRONG — no cleanup on uninstall
// Result: when merchant reinstalls, old stale session is found,
// API calls fail with 401, auth redirect loop

// RIGHT — clean up on uninstall
async function handleAppUninstalled(shop: string): Promise<void> {
  // Delete session from database
  await prisma.session.deleteMany({ where: { shop } });
  // Disable features for this shop
  await prisma.appSettings.update({
    where: { shop },
    data: { active: false },
  });
  console.log(`Cleaned up data for uninstalled shop: ${shop}`);
  // shop/redact webhook will fire 48 hours later for full data deletion
}
```

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

```bash
# Run these against your Shopify codebase
echo "=== Shopify Pitfall Scan ==="
echo -n "REST API usage: "; grep -rc "clients.Rest\|admin-rest" app/ src/ 2>/dev/null | grep -v ":0" | wc -l
echo -n "Missing userErrors check: "; grep -rn "mutation\|Mutation" app/ src/ --include="*.ts" | wc -l
echo -n "Old API versions: "; grep -rn "2023-\|2022-" app/ src/ --include="*.ts" 2>/dev/null | wc -l
echo -n "Hardcoded tokens: "; grep -rc "shpat_" app/ src/ 2>/dev/null | grep -v ":0" | wc -l
echo -n "first: 250: "; grep -rn "first: 250\|first:250" app/ src/ --include="*.ts" 2>/dev/null | wc -l
```

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
| Old API version | `grep "2023-"` | Update to `2024-10` |
| Missing GDPR webhooks | App Store rejection | Add 3 mandatory webhook handlers |
| Webhook timeout | Retry storms, duplicates | Respond 200 immediately, queue processing |
| ProductInput on 2024-10 | Type error | Use `ProductCreateInput` / `ProductUpdateInput` |
| Page-number pagination | Query errors | Use cursor-based with `pageInfo` |
| `first: 250` with nesting | THROTTLED | Use `first: 50` or smaller |
| Admin token in browser | Security scan | Server-side proxy only |
| No APP_UNINSTALLED | Auth loop on reinstall | Clean up sessions on uninstall |
