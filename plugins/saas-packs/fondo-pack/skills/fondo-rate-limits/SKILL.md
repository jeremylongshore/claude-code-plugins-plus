---
name: fondo-rate-limits
description: |
  Manage rate limits for Fondo-connected services including Gusto API,
  QuickBooks API, Plaid, and Stripe when building parallel integrations.
  Trigger: "fondo rate limit", "gusto API limits", "QuickBooks throttling".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Rate Limits

## Overview

Fondo itself is a managed tax and accounting service without direct API rate limits, but startups building parallel integrations to the same financial providers Fondo connects to (Gusto, QuickBooks, Plaid, Stripe, Mercury) must coordinate their own API calls to avoid shared-limit conflicts. During Fondo's nightly sync windows, your direct API calls compete for the same provider quotas, making careful scheduling and throttling critical for tax-season workloads and month-end reconciliation batches.

## Rate Limit Reference

| Endpoint / Provider | Limit | Window | Scope |
|---------------------|-------|--------|-------|
| Gusto payroll API | 50 req | 1 minute | Per access token |
| QuickBooks Online API | 500 req, 10 concurrent | 1 minute | Per realm (company) |
| Plaid transactions | 100 req | 1 minute | Per client_id |
| Stripe reads | 100 req/sec | 1 second | Per API key |
| Mercury banking API | 50 req | 1 minute | Per API key |

## Rate Limiter Implementation

```typescript
class MultiProviderLimiter {
  private limiters: Map<string, { tokens: number; max: number; lastRefill: number; rate: number }> = new Map();

  register(provider: string, maxPerMinute: number) {
    this.limiters.set(provider, {
      tokens: maxPerMinute, max: maxPerMinute,
      lastRefill: Date.now(), rate: maxPerMinute / 60_000,
    });
  }

  async acquire(provider: string): Promise<void> {
    const l = this.limiters.get(provider);
    if (!l) throw new Error(`Unknown provider: ${provider}`);
    const now = Date.now();
    l.tokens = Math.min(l.max, l.tokens + (now - l.lastRefill) * l.rate);
    l.lastRefill = now;
    if (l.tokens >= 1) { l.tokens -= 1; return; }
    const waitMs = (1 - l.tokens) / l.rate;
    await new Promise(r => setTimeout(r, waitMs));
    l.tokens = 0;
  }
}

const limiter = new MultiProviderLimiter();
limiter.register("gusto", 40);      // 40/min leaves room for Fondo syncs
limiter.register("quickbooks", 400); // buffer under 500/min
limiter.register("plaid", 80);
```

## Retry Strategy

```typescript
async function providerRetry<T>(
  provider: string, fn: () => Promise<Response>, maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await limiter.acquire(provider);
    const res = await fn();
    if (res.ok) return res.json();
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "15", 10);
      const jitter = Math.random() * 3000;
      await new Promise(r => setTimeout(r, retryAfter * 1000 + jitter));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 2000));
      continue;
    }
    throw new Error(`${provider} API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchReconcile(transactions: any[], provider: string, batchSize = 15) {
  const results: any[] = [];
  for (let i = 0; i < transactions.length; i += batchSize) {
    const batch = transactions.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(txn => providerRetry(provider, () =>
        fetch(`${PROVIDER_URLS[provider]}/transactions`, {
          method: "POST", headers: providerHeaders[provider],
          body: JSON.stringify(txn),
        })
      ))
    );
    results.push(...batchResults);
    if (i + batchSize < transactions.length) await new Promise(r => setTimeout(r, 5000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Gusto 429 during payroll sync | Fondo nightly sync competing | Schedule calls outside midnight UTC window |
| QuickBooks concurrent limit | 10+ parallel requests | Cap concurrency at 8 with p-queue |
| Plaid ITEM_LOGIN_REQUIRED | Token expired mid-batch | Re-authenticate, resume from last offset |
| Stripe idempotency conflict | Duplicate key on retry | Use unique idempotency keys per transaction |
| Mercury timeout on bulk export | Large date range query | Split into monthly chunks |

## Resources

- [Gusto API Rate Limits](https://docs.gusto.com/)
- [QuickBooks API Limits](https://developer.intuit.com/)
- [Stripe Rate Limits](https://stripe.com/docs/rate-limits)

## Next Steps

See `fondo-performance-tuning`.
