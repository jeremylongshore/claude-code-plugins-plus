---
name: finta-rate-limits
description: 'Understand Finta usage limits and plan tiers.

  Trigger with phrases like "finta limits", "finta plan limits".

  '
allowed-tools: Read
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- fundraising-crm
- investor-management
- finta
compatibility: Designed for Claude Code
---
# Finta Rate Limits

## Overview

Use provider responses and observed traffic to prevent avoidable throttling while preserving data correctness and safe retries.

## Prerequisites

- Aggregate request, error, and queue-age telemetry with no raw investor payloads.
- A configured concurrency limit, retry bound, and exception-queue owner.
- Synthetic test data and a rollback switch for worker configuration changes.

## Instructions

1. Treat documented or returned throttle signals as authoritative; do not hard-code assumptions about provider limits.
2. Bound concurrency, use exponential backoff with jitter, and honor explicit retry-after guidance when present.
3. Attach idempotency keys to externally visible actions so retries cannot duplicate communications or records.
4. Move exhausted retries to a reviewed queue, alert on backlog growth, and reduce load before resuming.

## Output

Produce a redacted rate-control receipt showing the measurement window, concurrency, retry policy, throttle count, duplicate-prevention outcome, and any manually reviewed failures.

## Examples

Replay synthetic jobs at a small concurrency. When a simulated throttle response appears, the worker waits, retries once under its idempotency key, and places a repeated failure in the review queue rather than increasing traffic.

Finta operates as a web-first fundraising platform without a traditional REST API, so rate limits manifest as plan-tier usage caps rather than HTTP request quotas. When building integrations through Finta's webhook events or Zapier connectors, the bottleneck is typically the number of investor pipeline records, deal room operations, and Aurora AI suggestion calls you can make within your plan tier. Teams running active fundraising rounds need to understand these ceilings to avoid mid-raise disruptions.

## Rate Limit Reference

| Endpoint / Feature | Limit | Window | Scope |
|---------------------|-------|--------|-------|
| Investor pipeline records | 50 (Free) / Unlimited (Pro) | Rolling | Per workspace |
| Deal room creation | 1 (Free) / Unlimited (Pro) | Rolling | Per workspace |
| Aurora AI suggestions | 10/day (Free) / 100/day (Pro) | 24 hours | Per user |
| Webhook event delivery | 100 events | 1 minute | Per workspace |
| Data room file uploads | 25 (Free) / Unlimited (Pro) | Rolling | Per deal room |

## Rate Limiter Implementation

```typescript
class FintaUsageTracker {
  private counts: Map<string, { used: number; limit: number; resetAt: number }> = new Map();

  register(resource: string, limit: number, windowMs: number) {
    this.counts.set(resource, { used: 0, limit, resetAt: Date.now() + windowMs });
  }

  async acquire(resource: string): Promise<boolean> {
    const entry = this.counts.get(resource);
    if (!entry) throw new Error(`Unknown resource: ${resource}`);
    if (Date.now() > entry.resetAt) { entry.used = 0; entry.resetAt = Date.now() + 86_400_000; }
    if (entry.used >= entry.limit) return false;
    entry.used++;
    return true;
  }

  remaining(resource: string): number {
    const entry = this.counts.get(resource);
    return entry ? entry.limit - entry.used : 0;
  }
}

const tracker = new FintaUsageTracker();
tracker.register("aurora_suggestions", 100, 86_400_000);
tracker.register("webhook_events", 100, 60_000);
```

## Retry Strategy

```typescript
async function fintaWebhookRetry(payload: any, webhookUrl: string, maxRetries = 3): Promise<void> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) return;
      if (res.status === 429) {
        const delay = Math.pow(2, attempt) * 5000 + Math.random() * 2000;
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw new Error(`Webhook delivery failed: ${res.status}`);
    } catch (err) {
      if (attempt === maxRetries) throw err;
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 3000));
    }
  }
}
```

## Batch Processing

```typescript
async function batchSyncInvestors(investors: any[], batchSize = 20) {
  const results: any[] = [];
  for (let i = 0; i < investors.length; i += batchSize) {
    const batch = investors.slice(i, i + batchSize);
    for (const investor of batch) {
      const allowed = await tracker.acquire("webhook_events");
      if (!allowed) { await new Promise(r => setTimeout(r, 60_000)); }
      results.push(await fintaWebhookRetry(investor, WEBHOOK_URL));
    }
    if (i + batchSize < investors.length) await new Promise(r => setTimeout(r, 3000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Plan limit reached | Free tier investor cap (50) | Upgrade to Pro or archive inactive investors |
| Aurora AI unavailable | Daily suggestion quota exhausted | Wait for 24h reset or upgrade plan |
| Webhook delivery 429 | Burst of pipeline events | Queue events, deliver with 1s spacing |
| Deal room locked | Free plan single-room limit | Close existing room before opening new one |
| File upload rejected | Data room storage cap on Free tier | Compress files or upgrade plan |

## Resources

- [Finta Pricing](https://www.trustfinta.com/pricing)

## Next Steps

See `finta-performance-tuning`.
