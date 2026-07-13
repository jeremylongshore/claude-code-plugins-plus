# Step 4: Scaling Strategies

Deep-dive reference for the `figma-load-scale` skill — extracted from the 'Step 4: Scaling Strategies' step of the workflow.

```typescript
// Strategy 1: Request coalescing
// Multiple callers requesting the same file get a single API call
class RequestCoalescer {
  private pending = new Map<string, Promise<any>>();

  async get(key: string, fetcher: () => Promise<any>): Promise<any> {
    if (this.pending.has(key)) {
      return this.pending.get(key)!;
    }

    const promise = fetcher().finally(() => this.pending.delete(key));
    this.pending.set(key, promise);
    return promise;
  }
}

const coalescer = new RequestCoalescer();

// 10 simultaneous requests for the same file = 1 API call
const results = await Promise.all(
  Array(10).fill(null).map(() =>
    coalescer.get(fileKey, () => figmaClient.getFile(fileKey))
  )
);

// Strategy 2: Stagger requests across time
import PQueue from 'p-queue';

const figmaQueue = new PQueue({
  concurrency: 3,
  interval: 1000,
  intervalCap: 5, // Max 5 requests per second
});

// Strategy 3: Pre-fetch during off-peak hours
// Run design token sync at 3 AM, cache results for the day
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
