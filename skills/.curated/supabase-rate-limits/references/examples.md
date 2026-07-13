## Examples

### Queue-Based Rate Limiting

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 10,
});

async function queuedRequest<T>(operation: () => Promise<T>): Promise<T> {
  return queue.add(operation);
}
```

### Monitor Rate Limit Usage

```typescript
class RateLimitMonitor {
  private remaining: number = 60;
  private resetAt: Date = new Date();

  updateFromHeaders(headers: Headers) {
    this.remaining = parseInt(headers.get('X-RateLimit-Remaining') || '60');
    const resetTimestamp = headers.get('X-RateLimit-Reset');
    if (resetTimestamp) {
      this.resetAt = new Date(parseInt(resetTimestamp) * 1000);
    }
  }

  shouldThrottle(): boolean {
    // Only throttle if low remaining AND reset hasn't happened yet
    return this.remaining < 5 && new Date() < this.resetAt;
  }

  getWaitTime(): number {
    return Math.max(0, this.resetAt.getTime() - Date.now());
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
