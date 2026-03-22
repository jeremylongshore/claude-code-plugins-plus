---
name: instantly-rate-limits
description: |
  Implement Instantly.ai rate limiting, backoff, and request throttling patterns.
  Use when handling 429 errors, implementing retry logic,
  or building high-throughput Instantly integrations.
  Trigger with phrases like "instantly rate limit", "instantly 429",
  "instantly throttle", "instantly backoff", "instantly retry".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, rate-limits, reliability]

---
# Instantly Rate Limits

## Overview
Handle Instantly API v2 rate limits. The API returns `429 Too Many Requests` when limits are exceeded. Most endpoints follow standard limits. The email listing endpoint has a stricter constraint of **20 requests per minute**. Failed webhook deliveries are retried up to **3 times within 30 seconds**.

## Prerequisites
- Completed `instantly-install-auth` setup
- Understanding of exponential backoff patterns

## Known Rate Limits

| Endpoint | Limit | Notes |
|----------|-------|-------|
| Most API endpoints | Standard REST limits | Varies by plan |
| `GET /emails` | 20 req/min | Stricter — email listing |
| Webhook deliveries | 3 retries in 30s | Instantly retries to your endpoint |
| Background jobs | N/A | Async — poll via `GET /background-jobs/{id}` |

## Instructions

### Step 1: Exponential Backoff with Jitter
```typescript
import { InstantlyApiError } from "./src/instantly/client";

interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

const DEFAULT_RETRY: RetryOptions = {
  maxRetries: 5,
  baseDelayMs: 1000,
  maxDelayMs: 30000,
};

async function withBackoff<T>(
  operation: () => Promise<T>,
  opts: Partial<RetryOptions> = {}
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs } = { ...DEFAULT_RETRY, ...opts };

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      const isRetryable =
        err instanceof InstantlyApiError &&
        (err.status === 429 || err.status >= 500);

      if (!isRetryable || attempt === maxRetries) throw err;

      // Parse Retry-After header if available
      let delay = baseDelayMs * Math.pow(2, attempt);
      delay = Math.min(delay, maxDelayMs);

      // Add jitter (10-30% of delay)
      const jitter = delay * (0.1 + Math.random() * 0.2);
      const totalDelay = delay + jitter;

      console.warn(
        `Rate limited (attempt ${attempt + 1}/${maxRetries}). Waiting ${Math.round(totalDelay)}ms...`
      );
      await new Promise((r) => setTimeout(r, totalDelay));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 2: Request Queue with Concurrency Control
```typescript
class RequestQueue {
  private queue: Array<() => Promise<void>> = [];
  private running = 0;
  private readonly maxConcurrent: number;
  private readonly delayBetweenMs: number;

  constructor(maxConcurrent = 5, delayBetweenMs = 200) {
    this.maxConcurrent = maxConcurrent;
    this.delayBetweenMs = delayBetweenMs;
  }

  async add<T>(operation: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await withBackoff(operation);
          resolve(result);
        } catch (err) {
          reject(err);
        } finally {
          this.running--;
          this.processQueue();
        }
      });
      this.processQueue();
    });
  }

  private async processQueue() {
    while (this.running < this.maxConcurrent && this.queue.length > 0) {
      const task = this.queue.shift()!;
      this.running++;
      if (this.delayBetweenMs > 0) {
        await new Promise((r) => setTimeout(r, this.delayBetweenMs));
      }
      task();
    }
  }
}

// Usage — add 500 leads with controlled concurrency
const queue = new RequestQueue(3, 300); // 3 concurrent, 300ms gap

for (const lead of leads) {
  queue.add(() =>
    instantly("/leads", {
      method: "POST",
      body: JSON.stringify({ campaign: campaignId, email: lead.email, ...lead }),
    })
  );
}
```

### Step 3: Rate-Limited Email Listing
```typescript
// The /emails endpoint has a 20 req/min limit
// Use a dedicated throttled fetcher
class ThrottledEmailFetcher {
  private requestTimestamps: number[] = [];
  private readonly maxPerMinute = 18; // leave 2 req margin

  private async waitForSlot() {
    const now = Date.now();
    this.requestTimestamps = this.requestTimestamps.filter(
      (t) => now - t < 60000
    );

    if (this.requestTimestamps.length >= this.maxPerMinute) {
      const oldest = this.requestTimestamps[0];
      const waitMs = 60000 - (now - oldest) + 1000; // +1s buffer
      console.log(`Email API throttle: waiting ${waitMs}ms`);
      await new Promise((r) => setTimeout(r, waitMs));
    }

    this.requestTimestamps.push(Date.now());
  }

  async listEmails(params: {
    campaign_id?: string;
    is_unread?: boolean;
    limit?: number;
    starting_after?: string;
  }) {
    await this.waitForSlot();

    const qs = new URLSearchParams();
    if (params.campaign_id) qs.set("campaign_id", params.campaign_id);
    if (params.is_unread !== undefined) qs.set("is_unread", String(params.is_unread));
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.starting_after) qs.set("starting_after", params.starting_after);

    return instantly(`/emails?${qs}`);
  }
}
```

### Step 4: Batch Operations Pattern
```typescript
// Instead of creating leads one-by-one, batch where possible
async function addLeadsBatched(
  campaignId: string,
  leads: Array<{ email: string; first_name?: string }>,
  batchSize = 10,
  delayBetweenBatchesMs = 1000
) {
  let added = 0;
  let failed = 0;

  for (let i = 0; i < leads.length; i += batchSize) {
    const batch = leads.slice(i, i + batchSize);

    const results = await Promise.allSettled(
      batch.map((lead) =>
        withBackoff(() =>
          instantly("/leads", {
            method: "POST",
            body: JSON.stringify({
              campaign: campaignId,
              email: lead.email,
              first_name: lead.first_name,
              skip_if_in_workspace: true,
            }),
          })
        )
      )
    );

    added += results.filter((r) => r.status === "fulfilled").length;
    failed += results.filter((r) => r.status === "rejected").length;

    console.log(`Batch ${Math.floor(i / batchSize) + 1}: ${added} added, ${failed} failed`);

    if (i + batchSize < leads.length) {
      await new Promise((r) => setTimeout(r, delayBetweenBatchesMs));
    }
  }

  console.log(`\nTotal: ${added} added, ${failed} failed out of ${leads.length}`);
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `429` on lead import | Too many sequential POSTs | Use batch pattern with delays |
| `429` on email listing | >20 req/min | Use `ThrottledEmailFetcher` |
| `5xx` intermittent | Instantly server overload | Backoff + retry; check status.instantly.ai |
| Webhook delivery retries exhausted | Your endpoint too slow | Return 200 immediately, process async |
| Queue memory growing | Too many queued operations | Set max queue size, reject overflow |

## Resources
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [Instantly Blog: API Rate Limits](https://instantly.ai/blog/api-webhooks-custom-integrations-for-outreach/)

## Next Steps
For security patterns, see `instantly-security-basics`.
