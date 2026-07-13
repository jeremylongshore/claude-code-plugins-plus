# Response Caching with Webhook Invalidation

LRU cache layer for Shopify API responses with automatic invalidation via webhook events.

```typescript
import { LRUCache } from "lru-cache";

const shopifyCache = new LRUCache<string, any>({
  max: 500,
  ttl: 5 * 60 * 1000, // 5 minutes
  updateAgeOnGet: true,
});

async function cachedQuery<T>(
  cacheKey: string,
  queryFn: () => Promise<T>,
  ttlMs?: number
): Promise<T> {
  const cached = shopifyCache.get(cacheKey);
  if (cached !== undefined) return cached as T;

  const result = await queryFn();
  shopifyCache.set(cacheKey, result, { ttl: ttlMs });
  return result;
}

// Usage — cache product data for 5 minutes
const product = await cachedQuery(
  `product:${productId}`,
  () => shopifyQuery(shop, PRODUCT_QUERY, { id: productId })
);

// Invalidate on webhook
app.post("/webhooks", (req, res) => {
  const topic = req.headers["x-shopify-topic"];
  if (topic === "products/update") {
    const payload = JSON.parse(req.body);
    shopifyCache.delete(`product:gid://shopify/Product/${payload.id}`);
  }
});
```
