# Rate Limit-Aware Retry

Retry logic that respects Shopify's `Retry-After` header and GraphQL throttle status restore rate.

```typescript
async function shopifyRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      const isRetryable =
        error.response?.code === 429 ||
        error.response?.code >= 500 ||
        error.body?.errors?.[0]?.extensions?.code === "THROTTLED";

      if (!isRetryable || attempt === maxRetries) throw error;

      // For REST 429: use Retry-After header
      const retryAfter = error.response?.headers?.["retry-after"];
      // For GraphQL THROTTLED: calculate from available points
      const throttle = error.body?.extensions?.cost?.throttleStatus;
      const waitForPoints = throttle
        ? ((100 - throttle.currentlyAvailable) / throttle.restoreRate) * 1000
        : 0;

      const delay = retryAfter
        ? parseFloat(retryAfter) * 1000
        : Math.max(waitForPoints, 1000 * Math.pow(2, attempt));

      console.warn(`Retry ${attempt + 1}/${maxRetries} in ${(delay / 1000).toFixed(1)}s`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```
