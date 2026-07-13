# Circuit Breaker for Shopify API

Full circuit breaker implementation using opossum with Shopify-specific error filtering.

```typescript
import CircuitBreaker from "opossum";

// Create circuit breaker wrapping Shopify API calls
const shopifyCircuit = new CircuitBreaker(
  async (fn: () => Promise<any>) => fn(),
  {
    timeout: 10000,                 // 10s timeout per request
    errorThresholdPercentage: 50,   // Open at 50% error rate
    resetTimeout: 30000,            // Try half-open after 30s
    volumeThreshold: 5,             // Need 5 requests before tripping
    errorFilter: (error: any) => {
      // Don't count 422 validation errors as circuit failures
      // Only count 5xx and timeout errors
      const code = error.response?.code || error.statusCode;
      return code >= 500 || error.code === "ECONNRESET" || error.code === "ETIMEDOUT";
    },
  }
);

shopifyCircuit.on("open", () => {
  console.error("[CIRCUIT OPEN] Shopify API failing — serving cached data");
});
shopifyCircuit.on("halfOpen", () => {
  console.info("[CIRCUIT HALF-OPEN] Testing Shopify recovery...");
});
shopifyCircuit.on("close", () => {
  console.info("[CIRCUIT CLOSED] Shopify API recovered");
});

// Usage
async function resilientShopifyQuery<T>(
  shop: string,
  query: string,
  variables?: Record<string, unknown>
): Promise<T> {
  return shopifyCircuit.fire(async () => {
    const client = getGraphqlClient(shop);
    const response = await client.request(query, { variables });

    // Check for THROTTLED in GraphQL response
    if (response.errors?.some((e: any) => e.extensions?.code === "THROTTLED")) {
      throw new Error("THROTTLED"); // Triggers circuit breaker
    }

    return response.data as T;
  });
}
```
