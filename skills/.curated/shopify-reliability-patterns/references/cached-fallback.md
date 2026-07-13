# Graceful Degradation with Cached Fallback

Three-tier fallback strategy: live API, cached data, then alternative data source.

```typescript
async function withFallback<T>(
  primary: () => Promise<T>,
  fallback: () => Promise<T>,
  cacheKey?: string
): Promise<{ data: T; source: "live" | "cached" | "fallback" }> {
  try {
    const data = await primary();
    // Update cache for future fallback
    if (cacheKey) {
      await redis.set(`fallback:${cacheKey}`, JSON.stringify(data), "EX", 3600);
    }
    return { data, source: "live" };
  } catch (error) {
    console.warn("Shopify API failed, trying cached data:", (error as Error).message);

    // Try cached data first
    if (cacheKey) {
      const cached = await redis.get(`fallback:${cacheKey}`);
      if (cached) {
        return { data: JSON.parse(cached), source: "cached" };
      }
    }

    // Fall back to alternative data source
    try {
      const data = await fallback();
      return { data, source: "fallback" };
    } catch {
      throw error; // Re-throw original error if all fallbacks fail
    }
  }
}

// Usage
const { data: products, source } = await withFallback(
  () => shopifyQuery(shop, PRODUCTS_QUERY),
  () => db.cachedProducts.findMany({ where: { shop } }),
  `products:${shop}`
);

if (source !== "live") {
  console.warn(`Serving ${source} product data for ${shop}`);
}
```
