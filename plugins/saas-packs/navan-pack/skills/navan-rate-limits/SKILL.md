---
name: navan-rate-limits
description: 'Implement adaptive rate-limiting for the Navan REST API with exponential
  backoff and request queuing.

  Use when building bulk data operations or encountering 429 errors from Navan.

  Trigger with "navan rate limits", "navan throttling", "navan 429".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Rate Limits

## Overview
Navan does not publicly document its API rate limits. Developers typically discover thresholds empirically when bulk data pulls or batch operations begin returning HTTP 429 responses. This skill implements defensive rate-limiting patterns that adapt to server responses rather than relying on fixed quotas — inspecting response headers, applying exponential backoff with jitter, and queuing requests to prevent flooding.

## Prerequisites
- Active Navan OAuth 2.0 credentials (see `navan-install-auth`)
- Node.js 18+ (examples use native fetch)
- Understanding of HTTP 429 status code and Retry-After header semantics

## Instructions

### Step 1: Build an Adaptive Retry Wrapper
```typescript
interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

async function navanFetch(
  url: string,
  options: RequestInit,
  retry: RetryOptions = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 30000 }
): Promise<Response> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retry.maxRetries; attempt++) {
    const response = await fetch(url, options);

    // Log rate limit headers when present (undocumented but sometimes returned)
    const remaining = response.headers.get('X-RateLimit-Remaining');
    const limit = response.headers.get('X-RateLimit-Limit');
    if (remaining !== null) {
      console.log(`Rate limit: ${remaining}/${limit} remaining`);
    }

    if (response.status !== 429) return response;

    // Extract delay from Retry-After header or calculate exponential backoff
    const retryAfter = response.headers.get('Retry-After');
    let delayMs: number;

    if (retryAfter) {
      delayMs = parseInt(retryAfter, 10) * 1000;
      console.log(`429 received — Retry-After: ${retryAfter}s`);
    } else {
      // Exponential backoff with jitter
      delayMs = Math.min(
        retry.baseDelayMs * Math.pow(2, attempt) + Math.random() * 1000,
        retry.maxDelayMs
      );
      console.log(`429 received — backoff: ${Math.round(delayMs)}ms (attempt ${attempt + 1})`);
    }

    await new Promise(resolve => setTimeout(resolve, delayMs));
    lastError = new Error(`Rate limited after ${attempt + 1} attempts`);
  }

  throw lastError ?? new Error('Max retries exceeded');
}
```

### Step 2: Implement a Request Queue for Bulk Operations
```typescript
class NavanRequestQueue {
  private queue: Array<() => Promise<void>> = [];
  private running = 0;
  private readonly concurrency: number;
  private readonly delayBetweenMs: number;

  constructor(concurrency = 3, delayBetweenMs = 500) {
    this.concurrency = concurrency;
    this.delayBetweenMs = delayBetweenMs;
  }

  async add<T>(fn: () => Promise<T>): Promise<T> {
    while (this.running >= this.concurrency) {
      await new Promise(r => setTimeout(r, 100));
    }
    this.running++;
    try {
      const result = await fn();
      await new Promise(r => setTimeout(r, this.delayBetweenMs));
      return result;
    } finally {
      this.running--;
    }
  }

  async drain(): Promise<void> {
    while (this.running > 0) {
      await new Promise(r => setTimeout(r, 100));
    }
  }
}
```

### Step 3: Use the Queue for Batch Data Pulls
```typescript
const queue = new NavanRequestQueue(3, 500); // 3 concurrent, 500ms gap
const accessToken = process.env.NAVAN_ACCESS_TOKEN!;

async function fetchAllExpenses(startDate: string, endDate: string) {
  let page = 1;
  let hasMore = true;
  const allExpenses: any[] = [];

  while (hasMore) {
    const currentPage = page;
    const result = await queue.add(async () => {
      const res = await navanFetch(
        `https://api.navan.com/v1/expenses?page=${currentPage}&start_date=${startDate}&end_date=${endDate}`,
        { headers: { 'Authorization': `Bearer ${accessToken}` } }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      return res.json();
    });

    allExpenses.push(...result.data);
    hasMore = result.has_more;
    page++;
  }

  return allExpenses;
}
```

### Step 4: Log and Monitor Rate Limit Signals
```typescript
function logRateLimitHeaders(response: Response, endpoint: string): void {
  const headers = [
    'X-RateLimit-Limit',
    'X-RateLimit-Remaining',
    'X-RateLimit-Reset',
    'Retry-After'
  ];

  const found: Record<string, string> = {};
  for (const h of headers) {
    const val = response.headers.get(h);
    if (val) found[h] = val;
  }

  if (Object.keys(found).length > 0) {
    console.log(`[${endpoint}] Rate limit headers:`, found);
  }
}
```

## Output
A resilient API client that handles Navan's undocumented rate limits through adaptive retry logic and controlled concurrency. The queue prevents bulk operations from triggering 429 responses, and the retry wrapper recovers gracefully when limits are hit.

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Too Many Requests | 429 | Retry with exponential backoff; inspect Retry-After header |
| Gateway Timeout | 504 | Reduce concurrency in queue; retry after 5-10 seconds |
| Service Unavailable | 503 | Navan maintenance window; retry with longer backoff (30-60s) |
| Unauthorized | 401 | Token expired during long batch operation; refresh OAuth token and retry |
| Bad Gateway | 502 | Transient upstream error; retry once after 2 seconds |

## Examples

**Quick test for rate limit headers:**
```bash
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $NAVAN_ACCESS_TOKEN" \
  https://api.navan.com/v1/users?limit=1 2>&1 | grep -i 'rate\|retry'
```

**Bulk export with throttling (Python):**
```python
import time
import requests

def navan_get(url, token, max_retries=5):
    for attempt in range(max_retries):
        resp = requests.get(url, headers={'Authorization': f'Bearer {token}'})
        if resp.status_code != 429:
            return resp
        delay = int(resp.headers.get('Retry-After', 2 ** attempt))
        print(f'Rate limited — waiting {delay}s (attempt {attempt + 1})')
        time.sleep(delay)
    raise Exception('Max retries exceeded')
```

## Resources
- [Navan Help Center](https://app.navan.com/app/helpcenter) — Official documentation and support articles
- [Navan Integrations](https://navan.com/integrations) — Integration partner ecosystem
- [HTTP 429 Specification (RFC 6585)](https://datatracker.ietf.org/doc/html/rfc6585#section-4) — Standard for rate limiting responses

## Next Steps
After implementing rate limiting, see `navan-security-basics` for credential rotation and token management, or `navan-data-sync` for building paginated data export pipelines.
