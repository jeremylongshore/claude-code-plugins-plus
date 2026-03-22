---
name: documenso-rate-limits
description: |
  Implement Documenso rate limiting, backoff, and request throttling patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Documenso.
  Trigger with phrases like "documenso rate limit", "documenso throttling",
  "documenso 429", "documenso retry", "documenso backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, api]

---
# Documenso Rate Limits

## Overview

Documenso uses a fair-use rate limiting model. There are no published per-minute request quotas -- instead, limits are based on your plan's document allowance and general API fair use. The paid plans (Individual and Team) include unlimited signing and API volume. The free plan has a document limit. If you hit a 429, implement exponential backoff and request queuing.

## Prerequisites

- Documenso SDK installed
- Understanding of async/await patterns
- Completed `documenso-install-auth` setup

## Documenso Fair Use Model

| Plan | Documents | API Volume | Signing Volume |
|------|-----------|------------|----------------|
| Free | Limited (per plan) | Fair use | Fair use |
| Individual ($30/mo) | Unlimited | Unlimited | Unlimited |
| Team | Unlimited | Unlimited | Unlimited |
| Enterprise | Unlimited | Unlimited | Unlimited |
| Self-Hosted | Unlimited | No limits | No limits |

Documenso explicitly does not price API usage -- they want developers to build on the platform without API cost concerns. The practical limit is abusive traffic patterns (thousands of requests per second).

## Instructions

### Step 1: Exponential Backoff with Jitter

```typescript
// src/documenso/retry.ts
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

const DEFAULTS: RetryConfig = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 60000 };

export async function withRetry<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs } = { ...DEFAULTS, ...config };
  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      lastError = err;
      const status = err.statusCode ?? err.status;

      // Don't retry client errors (except 429)
      if (status && status >= 400 && status < 500 && status !== 429) {
        throw err;
      }

      if (attempt === maxRetries) break;

      // Exponential backoff with jitter
      const delay = Math.min(baseDelayMs * 2 ** attempt, maxDelayMs);
      const jitter = delay * (0.5 + Math.random() * 0.5);
      console.warn(`Retry ${attempt + 1}/${maxRetries} in ${Math.round(jitter)}ms (status: ${status})`);
      await new Promise((r) => setTimeout(r, jitter));
    }
  }
  throw lastError!;
}
```

### Step 2: Request Queue for Bulk Operations

```typescript
// src/documenso/queue.ts
import PQueue from "p-queue";

// Limit concurrency to avoid overwhelming the API
const queue = new PQueue({ concurrency: 5, interval: 1000, intervalCap: 10 });

export async function queuedRequest<T>(fn: () => Promise<T>): Promise<T> {
  return queue.add(fn) as Promise<T>;
}

// Usage: bulk document creation
async function createBulkDocuments(
  client: Documenso,
  items: Array<{ title: string; pdfPath: string }>
) {
  const results = await Promise.allSettled(
    items.map((item) =>
      queuedRequest(async () => {
        const doc = await client.documents.createV0({ title: item.title });
        const pdf = readFileSync(item.pdfPath);
        await client.documents.setFileV0(doc.documentId, {
          file: new Blob([pdf], { type: "application/pdf" }),
        });
        return doc;
      })
    )
  );

  const succeeded = results.filter((r) => r.status === "fulfilled").length;
  const failed = results.filter((r) => r.status === "rejected").length;
  console.log(`Bulk create: ${succeeded} succeeded, ${failed} failed`);
  return results;
}
```

### Step 3: Circuit Breaker for Outages

```typescript
// src/documenso/circuit-breaker.ts
class CircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: "closed" | "open" | "half-open" = "closed";

  constructor(
    private threshold = 5,         // failures before opening
    private resetTimeMs = 30000    // time before half-open
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.lastFailure > this.resetTimeMs) {
        this.state = "half-open";
      } else {
        throw new Error("Circuit breaker is open — Documenso API unavailable");
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (err) {
      this.onFailure();
      throw err;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = "closed";
  }

  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = "open";
      console.error(`Circuit breaker OPEN after ${this.failures} failures`);
    }
  }
}

// Usage
const breaker = new CircuitBreaker();
const doc = await breaker.execute(() => client.documents.findV0({ page: 1, perPage: 10 }));
```

### Step 4: Python Retry

```python
import time, random

def with_retry(fn, max_retries=5, base_delay=1.0):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status and 400 <= status < 500 and status != 429:
                raise
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2 ** attempt), 60)
            jitter = delay * (0.5 + random.random() * 0.5)
            print(f"Retry {attempt + 1}/{max_retries} in {jitter:.1f}s")
            time.sleep(jitter)

# Usage
docs = with_retry(lambda: client.documents.find_v0(page=1, per_page=10))
```

## Error Handling

| Scenario | Response Code | Action |
|----------|--------------|--------|
| Rate limited | 429 | Exponential backoff with jitter |
| Server error | 500/502/503 | Retry up to 5 times |
| Documenso outage | Persistent 5xx | Circuit breaker, degrade gracefully |
| Auth error | 401/403 | Do NOT retry -- fix credentials |

## Resources

- [Documenso Fair Use Policy](https://docs.documenso.com/users/fair-use)
- [Documenso Pricing](https://documenso.com/pricing)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `documenso-security-basics`.
