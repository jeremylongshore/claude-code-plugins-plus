---
name: miro-cost-tuning
description: |
  Optimize Miro API costs through credit monitoring, request reduction,
  and plan selection based on the credit-based rate limiting model.
  Trigger with phrases like "miro cost", "miro billing",
  "reduce miro costs", "miro pricing", "miro credits usage".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, cost-optimization, billing]
compatible-with: claude-code
---

# Miro Cost Tuning

## Overview

Miro's API pricing is based on your plan tier (Free, Business, Enterprise), not per-API-call billing. However, the **credit-based rate limiting** system (100,000 credits/minute) effectively caps throughput. Cost optimization means minimizing API calls to stay within your plan's rate limits and reduce the need for higher-tier upgrades.

## Miro Plan Comparison

| Feature | Free | Business | Enterprise |
|---------|------|----------|------------|
| Price | $0/user | $12-20/user/mo | Custom |
| Boards | 3 editable | Unlimited | Unlimited |
| API access | Yes | Yes | Yes |
| Rate limit | 100K credits/min | 100K credits/min | Higher (negotiable) |
| OAuth scopes | All standard | All standard | All + enterprise scopes |
| SCIM provisioning | No | No | Yes |
| Audit logs API | No | No | Yes |
| SSO/SAML | No | No | Yes |

## Credit Usage Tracking

```typescript
class MiroUsageTracker {
  private minuteCredits = 0;
  private dailyRequests = 0;
  private minuteStart = Date.now();
  private dailyStart = Date.now();

  trackRequest(response: Response): void {
    // Reset minute window
    if (Date.now() - this.minuteStart > 60_000) {
      this.minuteCredits = 0;
      this.minuteStart = Date.now();
    }

    // Reset daily window
    if (Date.now() - this.dailyStart > 86_400_000) {
      this.dailyRequests = 0;
      this.dailyStart = Date.now();
    }

    const limit = parseInt(response.headers.get('X-RateLimit-Limit') ?? '100000');
    const remaining = parseInt(response.headers.get('X-RateLimit-Remaining') ?? '100000');
    this.minuteCredits = limit - remaining;
    this.dailyRequests++;
  }

  getReport(): UsageReport {
    return {
      currentMinuteCredits: this.minuteCredits,
      creditUtilizationPercent: Math.round((this.minuteCredits / 100000) * 100),
      dailyRequests: this.dailyRequests,
      projectedMonthlyRequests: this.dailyRequests * 30,
      recommendation: this.getRecommendation(),
    };
  }

  private getRecommendation(): string {
    if (this.minuteCredits > 80000) {
      return 'CRITICAL: >80% credit usage. Reduce request rate or upgrade to Enterprise.';
    }
    if (this.minuteCredits > 50000) {
      return 'WARNING: >50% credit usage. Consider caching and batching.';
    }
    return 'Healthy credit usage.';
  }
}
```

## Cost Reduction Strategies

### Strategy 1: Reduce Read Requests with Caching

The biggest cost saver. Most Miro board reads return data that changes infrequently.

```typescript
// EXPENSIVE: Fetching board on every page load
app.get('/dashboard', async (req, res) => {
  const board = await miroFetch(`/v2/boards/${boardId}`);        // 1 credit per load
  const items = await miroFetch(`/v2/boards/${boardId}/items`);  // 1 credit per load
  res.render('dashboard', { board, items });
});

// OPTIMIZED: Cache board data for 2 minutes
app.get('/dashboard', async (req, res) => {
  const board = await getCachedBoard(boardId);    // Cache hit = 0 credits
  const items = await getCachedItems(boardId);    // Cache hit = 0 credits
  res.render('dashboard', { board, items });
});

// With webhook-driven invalidation, cache hits can be 95%+
// That is a 20x reduction in API calls
```

### Strategy 2: Filter Items by Type

Don't fetch all items if you only need sticky notes.

```typescript
// EXPENSIVE: Fetch all items, filter client-side
const allItems = await miroFetch(`/v2/boards/${boardId}/items?limit=50`);
const notes = allItems.data.filter(i => i.type === 'sticky_note');

// OPTIMIZED: Server-side type filter
const notes = await miroFetch(`/v2/boards/${boardId}/items?type=sticky_note&limit=50`);
// Fewer items returned = smaller response = faster
```

### Strategy 3: Batch Writes with Controlled Concurrency

```typescript
// EXPENSIVE: Sequential writes (slow + same credits)
for (const note of notes) {
  await createStickyNote(boardId, note);  // 200ms * 50 = 10 seconds
}

// OPTIMIZED: Parallel with concurrency control (same credits, 5x faster)
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 5 });
for (const note of notes) {
  queue.add(() => createStickyNote(boardId, note));
}
await queue.onIdle();  // ~2 seconds
```

### Strategy 4: Use Webhooks Instead of Polling

```typescript
// EXPENSIVE: Poll every 10 seconds (8,640 requests/day)
setInterval(async () => {
  const items = await miroFetch(`/v2/boards/${boardId}/items`);
  detectChanges(items);
}, 10_000);

// OPTIMIZED: Webhook subscription (0 polling requests)
// Miro pushes changes to your endpoint in real-time
// See miro-webhooks-events for setup
```

### Strategy 5: Smart Pagination Limits

```typescript
// WASTEFUL: Small page size = more round trips
let cursor;
do {
  const page = await miroFetch(`/v2/boards/${boardId}/items?limit=10&cursor=${cursor ?? ''}`);
  // 10 items per page = 10 requests for 100 items
} while (cursor);

// OPTIMIZED: Max page size
let cursor;
do {
  const page = await miroFetch(`/v2/boards/${boardId}/items?limit=50&cursor=${cursor ?? ''}`);
  // 50 items per page = 2 requests for 100 items
} while (cursor);
```

## Usage Dashboard Query

If you track API calls in a database:

```sql
SELECT
  DATE_TRUNC('hour', created_at) AS hour,
  endpoint,
  COUNT(*) AS requests,
  AVG(duration_ms) AS avg_latency_ms,
  COUNT(*) FILTER (WHERE status = 429) AS rate_limited
FROM miro_api_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY 1, 2
ORDER BY requests DESC;
```

## Budget Alerts

```typescript
// Alert when approaching credit limit
const tracker = new MiroUsageTracker();

// After each API call
tracker.trackRequest(response);

const report = tracker.getReport();
if (report.creditUtilizationPercent > 80) {
  await sendSlackAlert({
    channel: '#engineering-alerts',
    text: `Miro API credit usage at ${report.creditUtilizationPercent}%. ${report.recommendation}`,
  });
}
```

## When to Upgrade to Enterprise

Consider Enterprise if you need:
- Higher rate limits (negotiated per account)
- SCIM API for automated user provisioning
- Audit logs API for compliance
- Organization-level management endpoints
- SSO/SAML integration APIs
- Dedicated support for API issues

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Hitting 429 frequently | Too many requests | Implement caching + webhooks |
| Credit spikes | Runaway polling loops | Audit all `setInterval` calls |
| Unnecessary full-board fetches | No type filtering | Add `?type=` parameter |
| Small page sizes | Low `limit` parameter | Use `limit=50` (maximum) |

## Resources

- [Miro Pricing](https://miro.com/pricing/)
- [Rate Limiting](https://developers.miro.com/reference/rate-limiting)
- [Miro Enterprise](https://miro.com/enterprise/)

## Next Steps

For architecture patterns, see `miro-reference-architecture`.
