# Shopify Pitfall Code Examples

Complete wrong-way/right-way code examples for each of the 10 most common Shopify API anti-patterns.

## Pitfall #1: Not Checking userErrors

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

## Pitfall #2: Using REST When GraphQL Is Required

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

## Pitfall #3: Ignoring API Version Deprecation

```typescript
// WRONG — hardcoded old version, no monitoring
const shopify = shopifyApi({ apiVersion: "2023-04" }); // DEAD version

// RIGHT — use LATEST_API_VERSION from the SDK
import { LATEST_API_VERSION } from "@shopify/shopify-api";
const shopify = shopifyApi({ apiVersion: LATEST_API_VERSION });

// Monitor for deprecation warnings in responses
function checkDeprecation(headers: Headers): void {
  const warning = headers.get("x-shopify-api-deprecated-reason");
  if (warning) {
    console.warn(`[DEPRECATION] ${warning}`);
    // Alert team to upgrade
  }
}
```

## Pitfall #4: Missing Mandatory GDPR Webhooks

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

## Pitfall #5: Webhook Handler Takes Too Long

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

## Pitfall #6: Using ProductInput on API 2024-10+

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

## Pitfall #7: Not Using Cursor Pagination

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

## Pitfall #8: Requesting 250 Items Per Page

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

## Pitfall #9: Exposing Admin Token in Client-Side Code

```typescript
// WRONG — admin token in React component
const response = await fetch(`https://store.myshopify.com/admin/api/2025-04/graphql.json`, {
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

## Pitfall #10: Not Handling APP_UNINSTALLED Webhook

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
