---
name: clay-rate-limits
description: |
  Handle Clay rate limits, webhook throttling, and credit pacing strategies.
  Use when hitting 429 errors, managing webhook submission rates,
  or optimizing throughput within Clay's plan limits.
  Trigger with phrases like "clay rate limit", "clay throttling",
  "clay 429", "clay slow", "clay records per hour".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, api]

---
# Clay Rate Limits

## Overview

Clay enforces rate limits at the plan level, webhook level, and enrichment provider level. Understanding these limits prevents data loss, credit waste, and integration failures.

## Prerequisites

- Clay account with known plan tier
- Webhook URL(s) for your tables
- Understanding of your data volume requirements

## Instructions

### Step 1: Understand Clay Rate Limit Tiers

| Plan | Records/Hour | Webhook Limit | HTTP API Columns | Enterprise API |
|------|-------------|---------------|-----------------|----------------|
| Free | Limited | 50K lifetime per webhook | Not available | Not available |
| Starter | Standard | 50K lifetime per webhook | Not available | Not available |
| Explorer | 400/hour | 50K lifetime per webhook | Not available | Not available |
| Pro | Unlimited | 50K lifetime per webhook | Available | Not available |
| Enterprise | Unlimited | 50K lifetime per webhook | Available | Available |

**Key insight:** The 50K webhook submission limit is per-webhook, not per-table. Once exhausted, create a new webhook on the same table.

### Step 2: Implement Webhook Rate Limiting

```typescript
// src/clay/rate-limiter.ts — respect Clay's plan-level rate limits
import PQueue from 'p-queue';

interface RateLimiterConfig {
  maxPerHour: number;     // Plan limit (e.g., 400 for Explorer)
  maxPerSecond: number;   // Practical burst limit
  webhookLimit: number;   // 50K per webhook lifetime
}

const PLAN_LIMITS: Record<string, RateLimiterConfig> = {
  explorer: { maxPerHour: 400, maxPerSecond: 2, webhookLimit: 50_000 },
  pro:      { maxPerHour: Infinity, maxPerSecond: 10, webhookLimit: 50_000 },
  enterprise: { maxPerHour: Infinity, maxPerSecond: 20, webhookLimit: 50_000 },
};

class ClayRateLimiter {
  private queue: PQueue;
  private submissionCount = 0;
  private hourlyCount = 0;
  private hourlyResetAt: Date;
  private config: RateLimiterConfig;

  constructor(plan: keyof typeof PLAN_LIMITS) {
    this.config = PLAN_LIMITS[plan];
    this.queue = new PQueue({
      concurrency: 1,
      interval: 1000,
      intervalCap: this.config.maxPerSecond,
    });
    this.hourlyResetAt = new Date(Date.now() + 3600_000);
  }

  async submit(webhookUrl: string, data: Record<string, unknown>): Promise<Response> {
    // Check webhook lifetime limit
    if (this.submissionCount >= this.config.webhookLimit) {
      throw new Error(
        `Webhook submission limit (${this.config.webhookLimit}) reached. Create a new webhook.`
      );
    }

    // Check hourly limit
    if (Date.now() > this.hourlyResetAt.getTime()) {
      this.hourlyCount = 0;
      this.hourlyResetAt = new Date(Date.now() + 3600_000);
    }
    if (this.hourlyCount >= this.config.maxPerHour) {
      const waitMs = this.hourlyResetAt.getTime() - Date.now();
      console.log(`Hourly limit reached. Waiting ${(waitMs / 1000).toFixed(0)}s...`);
      await new Promise(r => setTimeout(r, waitMs));
      this.hourlyCount = 0;
    }

    return this.queue.add(async () => {
      const res = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (res.status === 429) {
        const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
        console.log(`429 rate limited. Waiting ${retryAfter}s...`);
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        return this.submit(webhookUrl, data); // Retry
      }

      this.submissionCount++;
      this.hourlyCount++;
      return res;
    });
  }

  getStats() {
    return {
      totalSubmissions: this.submissionCount,
      hourlyRemaining: this.config.maxPerHour - this.hourlyCount,
      webhookRemaining: this.config.webhookLimit - this.submissionCount,
    };
  }
}
```

### Step 3: Handle 429 Responses with Backoff

```typescript
// src/clay/backoff.ts
async function withClayBackoff<T>(
  operation: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === maxRetries) throw error;

      // Clay returns 429 for plan-level rate limits
      const status = error.status || error.response?.status;
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      const baseDelay = 1000 * Math.pow(2, attempt); // 1s, 2s, 4s, 8s, 16s
      const jitter = Math.random() * 500;
      const delay = Math.min(baseDelay + jitter, 60_000); // Max 60s

      console.log(`Clay rate limited (attempt ${attempt + 1}). Retrying in ${(delay / 1000).toFixed(1)}s`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Manage Webhook Lifecycle

```typescript
// src/clay/webhook-manager.ts
interface WebhookState {
  url: string;
  submissionCount: number;
  createdAt: Date;
}

class WebhookManager {
  private webhooks: Map<string, WebhookState> = new Map();
  private readonly LIMIT = 50_000;
  private readonly WARN_THRESHOLD = 45_000;

  registerWebhook(tableId: string, url: string) {
    this.webhooks.set(tableId, { url, submissionCount: 0, createdAt: new Date() });
  }

  async getWebhookUrl(tableId: string): Promise<string> {
    const state = this.webhooks.get(tableId);
    if (!state) throw new Error(`No webhook registered for table ${tableId}`);

    if (state.submissionCount >= this.LIMIT) {
      throw new Error(
        `Webhook for table ${tableId} exhausted (${this.LIMIT} submissions). ` +
        `Create a new webhook in Clay UI: Table > + Add > Webhooks > Monitor webhook`
      );
    }

    if (state.submissionCount >= this.WARN_THRESHOLD) {
      console.warn(
        `Webhook for ${tableId} at ${state.submissionCount}/${this.LIMIT} submissions. ` +
        `Plan to create a replacement soon.`
      );
    }

    return state.url;
  }

  recordSubmission(tableId: string) {
    const state = this.webhooks.get(tableId);
    if (state) state.submissionCount++;
  }
}
```

### Step 5: Enrichment Provider Rate Limits

Enrichment providers within Clay have their own limits. When using Clay's managed accounts, Clay handles throttling internally. When using your own API keys, you inherit the provider's rate limits:

| Provider | Typical Rate Limit | Credits per Lookup |
|----------|-------------------|-------------------|
| Apollo | 100 req/min | 2 (own key: 0) |
| Clearbit | 600 req/min | 2-5 (own key: 0) |
| Hunter.io | 15 req/sec | 2 (own key: 0) |
| People Data Labs | 100 req/min | 3 (own key: 0) |
| Prospeo | 200 req/min | 2 (own key: 0) |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Plan-level hourly limit | Reduce submission rate, upgrade plan |
| Webhook silently stops | 50K submission limit hit | Create new webhook on same table |
| Enrichment stuck | Provider rate limit | Wait or connect your own API key |
| Explorer 400/hr limit | Plan restriction | Queue submissions, upgrade to Pro |

## Resources

- [Clay Plans & Billing](https://university.clay.com/docs/plans-and-billing)
- [Clay University -- Sources](https://university.clay.com/docs/sources)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `clay-security-basics`.
