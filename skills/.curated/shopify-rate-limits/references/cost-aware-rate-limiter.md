# Cost-Aware GraphQL Rate Limiter

Client-side rate limiter that tracks Shopify's calculated query cost bucket and pre-emptively waits before sending requests that would be throttled.

```typescript
interface ShopifyThrottleStatus {
  maximumAvailable: number;
  currentlyAvailable: number;
  restoreRate: number;
}

class ShopifyRateLimiter {
  private available: number;
  private restoreRate: number;
  private lastUpdate: number;

  constructor(maxAvailable = 1000, restoreRate = 50) {
    this.available = maxAvailable;
    this.restoreRate = restoreRate;
    this.lastUpdate = Date.now();
  }

  updateFromResponse(throttleStatus: ShopifyThrottleStatus): void {
    this.available = throttleStatus.currentlyAvailable;
    this.restoreRate = throttleStatus.restoreRate;
    this.lastUpdate = Date.now();
  }

  async waitIfNeeded(estimatedCost: number): Promise<void> {
    // Estimate current available based on restore rate
    const elapsed = (Date.now() - this.lastUpdate) / 1000;
    const estimated = Math.min(
      this.available + elapsed * this.restoreRate,
      1000
    );

    if (estimated < estimatedCost) {
      const waitSeconds = (estimatedCost - estimated) / this.restoreRate;
      console.log(`Rate limit: waiting ${waitSeconds.toFixed(1)}s for ${estimatedCost} points`);
      await new Promise((r) => setTimeout(r, waitSeconds * 1000));
    }
  }
}

// Usage
const limiter = new ShopifyRateLimiter();

async function rateLimitedQuery(client: any, query: string, variables?: any) {
  await limiter.waitIfNeeded(100); // estimate cost

  const response = await client.request(query, { variables });

  // Update limiter from actual response
  if (response.extensions?.cost?.throttleStatus) {
    limiter.updateFromResponse(response.extensions.cost.throttleStatus);
  }

  return response;
}
```
