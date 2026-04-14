Four strategies for reducing Shopify API costs and improving efficiency.

**Strategy 1: Replace REST with GraphQL** (get only what you need)

```typescript
// REST returns ALL fields — 5KB+ per product
// GET /admin/api/{version}/products/123.json
// Returns: title, body_html, vendor, product_type, handle, template_suffix,
//          published_scope, tags, admin_graphql_api_id, variants[], images[],
//          options[], ... (everything)

// GraphQL returns ONLY requested fields — 200 bytes
const response = await client.request(`{
  product(id: "gid://shopify/Product/123") {
    title
    status
    totalInventory
  }
}`);
```

**Strategy 2: Use Bulk Operations for exports**

```typescript
// Instead of 200 paginated queries (200 * ~100 cost = 20,000 points):
// Use 1 bulk operation (minimal cost, runs in background)
await client.request(`
  mutation { bulkOperationRunQuery(query: """
    { products { edges { node { id title } } } }
  """) { bulkOperation { id status } userErrors { message } } }
`);
```

**Strategy 3: Cache and invalidate via webhooks**

```typescript
// Instead of re-querying products every request:
// Cache products, invalidate only when products/update webhook fires
// Saves: hundreds of queries per hour for read-heavy apps
```

**Strategy 4: Use Storefront API for public data**

```typescript
// Storefront API has separate rate limits
// Use it for: product listings, collections, search
// Keep Admin API for: order management, customer data, fulfillments
```
