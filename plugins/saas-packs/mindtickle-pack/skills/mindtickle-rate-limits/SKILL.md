---
name: mindtickle-rate-limits
description: 'Rate Limits for MindTickle.

  Trigger: "mindtickle rate limits".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle Rate Limits

## Overview

MindTickle's API enforces per-API-key rate limits across its sales readiness platform, with content upload and user management endpoints throttled more tightly than read operations on courses and quiz results. Organizations onboarding large sales teams (500+ reps) hit limits fast when bulk-creating user accounts, assigning training modules, and syncing completion data to Salesforce. Quiz result exports and coaching session analytics carry separate lower caps, making it critical to stagger data pulls during quarterly enablement rollouts.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| User create/update | 30 req | 1 minute | Per API key |
| Course assignment | 60 req | 1 minute | Per API key |
| Quiz results export | 20 req | 1 minute | Per API key |
| Content upload | 10 req | 1 minute | Per API key |
| Analytics / reports | 40 req | 1 minute | Per API key |

## Rate Limiter Implementation

```typescript
class MindTickleRateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly max: number;
  private readonly refillRate: number;
  private queue: Array<{ resolve: () => void }> = [];

  constructor(maxPerMinute: number) {
    this.max = maxPerMinute;
    this.tokens = maxPerMinute;
    this.lastRefill = Date.now();
    this.refillRate = maxPerMinute / 60_000;
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens >= 1) { this.tokens -= 1; return; }
    return new Promise(resolve => this.queue.push({ resolve }));
  }

  private refill() {
    const now = Date.now();
    this.tokens = Math.min(this.max, this.tokens + (now - this.lastRefill) * this.refillRate);
    this.lastRefill = now;
    while (this.tokens >= 1 && this.queue.length) {
      this.tokens -= 1;
      this.queue.shift()!.resolve();
    }
  }
}

const userLimiter = new MindTickleRateLimiter(25);
const contentLimiter = new MindTickleRateLimiter(8);
```

## Retry Strategy

```typescript
async function mindtickleRetry<T>(
  limiter: MindTickleRateLimiter, fn: () => Promise<Response>, maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await limiter.acquire();
    const res = await fn();
    if (res.ok) return res.json();
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "20", 10);
      const jitter = Math.random() * 3000;
      await new Promise(r => setTimeout(r, retryAfter * 1000 + jitter));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 2000));
      continue;
    }
    throw new Error(`MindTickle API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchOnboardUsers(users: any[], batchSize = 10) {
  const results: any[] = [];
  for (let i = 0; i < users.length; i += batchSize) {
    const batch = users.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(user => mindtickleRetry(userLimiter, () =>
        fetch(`${MT_BASE}/api/v1/users`, {
          method: "POST", headers,
          body: JSON.stringify({ email: user.email, name: user.name, role: user.role }),
        })
      ))
    );
    results.push(...batchResults);
    if (i + batchSize < users.length) await new Promise(r => setTimeout(r, 15_000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on bulk user create | Exceeded 30 writes/min user cap | Batch in groups of 10 with 15s gaps |
| 429 on content upload | Upload limit (10/min) is very low | Queue uploads serially with 8s spacing |
| 409 duplicate user | Email already exists in org | Upsert: fetch by email first, then update |
| Export timeout | Quiz results for 1000+ reps | Filter by team/date range, paginate |
| 403 on course assign | User lacks required prerequisite | Check prerequisites before assignment |

## Resources

- [MindTickle Platform Integrations](https://www.mindtickle.com/platform/integrations/)

## Next Steps

See `mindtickle-performance-tuning`.
