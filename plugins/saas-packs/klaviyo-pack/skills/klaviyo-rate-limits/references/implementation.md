# Klaviyo Rate Limits — Full Implementation Walkthrough

This reference holds the complete implementation for the request queue, live
rate-limit monitor, and rate-aware bulk operations. The core `Retry-After` aware
backoff (Step 1) lives in `SKILL.md`; this file layers the sustained-throughput
controls on top of it.

## Step 2: Request Queue (Sustained Throughput)

`withRateLimitRetry` reacts to a 429 *after* it happens. A queue prevents most
429s in the first place by capping how fast requests leave the process. Wrap
every Klaviyo call so both controls compose — the queue paces requests, and the
retry wrapper still absorbs any 429 that slips through.

```typescript
// src/klaviyo/queue.ts
import PQueue from 'p-queue';

// Respect Klaviyo's 75 req/s burst limit
// Leave headroom: target 60 req/s to avoid hitting the wall
const klaviyoQueue = new PQueue({
  concurrency: 10,        // Max parallel requests
  interval: 1000,         // Per second
  intervalCap: 60,        // 60 requests per second (safe margin)
});

export async function queuedKlaviyoCall<T>(
  operation: () => Promise<T>
): Promise<T> {
  return klaviyoQueue.add(() => withRateLimitRetry(operation));
}

// Monitor queue health
klaviyoQueue.on('idle', () => console.log('[Klaviyo] Queue drained'));
console.log(`[Klaviyo] Queue: pending=${klaviyoQueue.pending} size=${klaviyoQueue.size}`);
```

## Step 3: Rate Limit Monitor

The queue paces requests blindly. The monitor reads the `RateLimit-*` response
headers so throttling decisions track the server's real remaining budget rather
than a fixed guess — useful when several processes share one account's quota.

```typescript
// src/klaviyo/monitor.ts

class RateLimitMonitor {
  private burstRemaining = 75;
  private steadyRemaining = 700;
  private burstResetAt = Date.now();
  private steadyResetAt = Date.now();

  updateFromHeaders(headers: Record<string, string>): void {
    const remaining = headers['ratelimit-remaining'];
    const reset = headers['ratelimit-reset'];

    if (remaining !== undefined) {
      this.burstRemaining = parseInt(remaining);
    }
    if (reset !== undefined) {
      this.burstResetAt = Date.now() + parseInt(reset) * 1000;
    }
  }

  shouldThrottle(): boolean {
    return this.burstRemaining < 10 && Date.now() < this.burstResetAt;
  }

  getWaitMs(): number {
    if (!this.shouldThrottle()) return 0;
    return Math.max(0, this.burstResetAt - Date.now());
  }

  getStatus(): { burstRemaining: number; shouldThrottle: boolean } {
    return {
      burstRemaining: this.burstRemaining,
      shouldThrottle: this.shouldThrottle(),
    };
  }
}

export const rateLimitMonitor = new RateLimitMonitor();
```

## Step 4: Bulk Operations with Rate Awareness

Large imports are where accounts hit the steady (1-minute) cap. This helper
batches profiles, routes every write through `queuedKlaviyoCall`, and paces
between batches so a 100k-profile sync completes without a runaway 429 storm.

```typescript
// Process large datasets without hitting rate limits
export async function bulkProfileSync(
  profiles: Array<{ email: string; firstName?: string; properties?: Record<string, any> }>,
  batchSize = 50,    // Profiles per batch
  delayMs = 1000     // Delay between batches
): Promise<{ success: number; failed: number }> {
  let success = 0;
  let failed = 0;

  for (let i = 0; i < profiles.length; i += batchSize) {
    const batch = profiles.slice(i, i + batchSize);

    const results = await Promise.allSettled(
      batch.map(p =>
        queuedKlaviyoCall(() =>
          profilesApi.createOrUpdateProfile({
            data: {
              type: 'profile' as any,
              attributes: {
                email: p.email,
                firstName: p.firstName,
                properties: p.properties,
              },
            },
          })
        )
      )
    );

    success += results.filter(r => r.status === 'fulfilled').length;
    failed += results.filter(r => r.status === 'rejected').length;

    console.log(`[Klaviyo] Batch ${Math.floor(i / batchSize) + 1}: ${success} ok, ${failed} failed`);

    // Pace between batches
    if (i + batchSize < profiles.length) {
      await new Promise(r => setTimeout(r, delayMs));
    }
  }

  return { success, failed };
}
```

## Rate Limit Quick Reference

| Endpoint Category | Burst (1s) | Steady (1m) |
|-------------------|-----------|-------------|
| Most endpoints | 75 | 700 |
| Create Event | 75 | 700 |
| Bulk Subscribe | 75 | 700 |
| Reporting | Lower (varies) | Lower (varies) |
