# Retry with Exponential Backoff

Generic retry wrapper that handles both REST 429 responses and GraphQL THROTTLED errors with exponential backoff and jitter.

```typescript
async function withShopifyRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const isThrottled =
        error.response?.code === 429 ||
        error.body?.errors?.[0]?.extensions?.code === "THROTTLED";

      if (!isThrottled || attempt === maxRetries) throw error;

      // Use Retry-After header if available (REST), otherwise calculate
      const retryAfter = error.response?.headers?.["retry-after"];
      const delay = retryAfter
        ? parseFloat(retryAfter) * 1000
        : Math.min(1000 * Math.pow(2, attempt) + Math.random() * 500, 30000);

      console.warn(
        `Shopify throttled (attempt ${attempt + 1}/${maxRetries}). ` +
        `Retrying in ${(delay / 1000).toFixed(1)}s`
      );

      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```
