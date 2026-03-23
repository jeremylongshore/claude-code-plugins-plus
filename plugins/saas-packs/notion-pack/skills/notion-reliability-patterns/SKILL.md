---
name: notion-reliability-patterns
description: |
  Graceful degradation when Notion is down: offline cache, retry with
  exponential backoff, circuit breaker, health checks, and fallback content.
  Use when building fault-tolerant Notion integrations for production.
  Trigger with phrases like "notion reliability", "notion circuit breaker",
  "notion offline fallback", "notion health check", "notion graceful degradation".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Reliability Patterns

## Overview

Production-grade reliability patterns for Notion integrations. Covers graceful degradation with offline cache when Notion is unavailable, retry with exponential backoff for transient failures, circuit breaker to prevent cascade failures, health check endpoints for monitoring, and fallback content serving when the API is unreachable. All patterns use `Client` from `@notionhq/client` and handle Notion-specific error codes.

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- `lru-cache` for in-memory caching (`npm install lru-cache`)
- Python: `notion-client` installed (`pip install notion-client`)
- `NOTION_TOKEN` environment variable set
- Understanding of circuit breaker and retry patterns

## Instructions

### Step 1: Retry with Exponential Backoff

The Notion SDK has built-in retries, but you can customize the behavior for better control over transient errors (429, 500, 502, 503).

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

// Classify errors as transient (retryable) vs permanent
function isTransientError(error: unknown): boolean {
  if (isNotionClientError(error)) {
    return (
      error.code === APIErrorCode.RateLimited ||
      error.code === APIErrorCode.InternalServerError ||
      error.code === APIErrorCode.ServiceUnavailable ||
      error.code === 'notionhq_client_request_timeout'
    );
  }
  // Network errors are transient
  if (error instanceof Error && error.message.includes('fetch failed')) {
    return true;
  }
  return false;
}

async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  opts: { maxRetries?: number; baseDelayMs?: number; label?: string } = {}
): Promise<T> {
  const { maxRetries = 4, baseDelayMs = 1000, label = 'notion-call' } = opts;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (!isTransientError(error) || attempt === maxRetries) {
        throw error;
      }

      // Exponential backoff: 1s, 2s, 4s, 8s (with jitter)
      const delay = baseDelayMs * Math.pow(2, attempt);
      const jitter = delay * 0.2 * Math.random();
      const waitMs = delay + jitter;

      // Special handling for rate limits: use Retry-After header
      if (isNotionClientError(error) && error.code === APIErrorCode.RateLimited) {
        const retryAfter = parseInt((error as any).headers?.['retry-after'] ?? '1');
        const rateLimitWait = retryAfter * 1000;
        console.warn(`[${label}] Rate limited, waiting ${retryAfter}s (attempt ${attempt + 1}/${maxRetries})`);
        await new Promise(r => setTimeout(r, rateLimitWait));
      } else {
        console.warn(`[${label}] Transient error, retrying in ${Math.round(waitMs)}ms (attempt ${attempt + 1}/${maxRetries})`);
        await new Promise(r => setTimeout(r, waitMs));
      }
    }
  }
  throw new Error('Unreachable');
}

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Usage: any Notion call with automatic retry
const page = await retryWithBackoff(
  () => notion.pages.retrieve({ page_id: 'abc123' }),
  { label: 'get-page', maxRetries: 3 }
);
```

```python
from notion_client import Client, APIResponseError
import time
import random

notion = Client(auth=os.environ["NOTION_TOKEN"])

def is_transient(error):
    if isinstance(error, APIResponseError):
        return error.status in (429, 500, 502, 503)
    return False

def retry_with_backoff(fn, max_retries=4, base_delay=1.0, label="notion"):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            if not is_transient(e) or attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay * 0.2)
            print(f"[{label}] Retry {attempt + 1}/{max_retries} in {delay:.1f}s")
            time.sleep(delay)
```

### Step 2: Circuit Breaker to Prevent Cascade Failures

When Notion has sustained outages, stop hammering the API and fail fast.

```typescript
type CircuitState = 'closed' | 'open' | 'half-open';

class NotionCircuitBreaker {
  private state: CircuitState = 'closed';
  private failureCount = 0;
  private lastFailureTime = 0;
  private successCount = 0;

  constructor(
    private readonly failureThreshold = 5,     // Open after 5 consecutive failures
    private readonly resetTimeoutMs = 30_000,   // Try again after 30 seconds
    private readonly halfOpenSuccesses = 2      // Need 2 successes to close
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.resetTimeoutMs) {
        this.state = 'half-open';
        this.successCount = 0;
        console.log('[circuit] Half-open: testing Notion API');
      } else {
        throw new CircuitOpenError(
          `Circuit open: Notion API disabled for ${Math.round((this.resetTimeoutMs - (Date.now() - this.lastFailureTime)) / 1000)}s`
        );
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure(error);
      throw error;
    }
  }

  private onSuccess() {
    this.failureCount = 0;
    if (this.state === 'half-open') {
      this.successCount++;
      if (this.successCount >= this.halfOpenSuccesses) {
        this.state = 'closed';
        console.log('[circuit] Closed: Notion API restored');
      }
    }
  }

  private onFailure(error: unknown) {
    // Only trip on transient errors, not client errors (400/401/404)
    if (!isTransientError(error)) return;

    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === 'half-open' || this.failureCount >= this.failureThreshold) {
      this.state = 'open';
      console.warn(`[circuit] OPEN after ${this.failureCount} failures — API calls disabled`);
    }
  }

  getState(): { state: CircuitState; failures: number; lastFailure: Date | null } {
    return {
      state: this.state,
      failures: this.failureCount,
      lastFailure: this.lastFailureTime ? new Date(this.lastFailureTime) : null,
    };
  }
}

class CircuitOpenError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CircuitOpenError';
  }
}

const circuit = new NotionCircuitBreaker();

// All Notion calls go through the circuit breaker
const query = await circuit.execute(() =>
  notion.databases.query({ database_id: dbId, page_size: 100 })
);
```

### Step 3: Graceful Degradation with Offline Cache, Health Checks, and Fallback Content

When Notion is down, serve cached data instead of errors. Include health check endpoints for monitoring.

```typescript
import { LRUCache } from 'lru-cache';

// Offline cache with long TTL — stale data beats no data
const offlineCache = new LRUCache<string, { data: any; timestamp: number }>({
  max: 1000,
  ttl: 3600_000, // 1 hour — keep serving even if API is down
});

interface QueryResult<T> {
  data: T;
  source: 'live' | 'cache';
  cacheAge?: number; // seconds since last live fetch
}

async function queryWithFallback<T>(
  cacheKey: string,
  fn: () => Promise<T>
): Promise<QueryResult<T>> {
  try {
    const data = await circuit.execute(() => retryWithBackoff(fn));

    // Update cache on success
    offlineCache.set(cacheKey, { data, timestamp: Date.now() });
    return { data, source: 'live' };
  } catch (error) {
    // Circuit is open or all retries exhausted — try cache
    const cached = offlineCache.get(cacheKey);
    if (cached) {
      const ageSeconds = Math.round((Date.now() - cached.timestamp) / 1000);
      console.warn(`[fallback] Serving cached data (${ageSeconds}s old) for ${cacheKey}`);
      return { data: cached.data as T, source: 'cache', cacheAge: ageSeconds };
    }

    // No cache — provide fallback content
    throw error;
  }
}

// Usage: query database with automatic fallback
const { data: pages, source } = await queryWithFallback(
  `db-query:${dbId}:active`,
  () => notion.databases.query({
    database_id: dbId,
    filter: { property: 'Status', select: { equals: 'Active' } },
  })
);

if (source === 'cache') {
  console.log('Showing cached data — Notion API is currently unavailable');
}

// Health check endpoint for monitoring
async function notionHealthCheck(): Promise<{
  status: 'healthy' | 'degraded' | 'down';
  circuit: CircuitState;
  latencyMs: number | null;
  cacheSize: number;
}> {
  const cacheSize = offlineCache.size;
  const circuitState = circuit.getState();

  if (circuitState.state === 'open') {
    return { status: 'down', circuit: 'open', latencyMs: null, cacheSize };
  }

  const start = Date.now();
  try {
    await notion.users.me({});
    const latencyMs = Date.now() - start;
    return {
      status: latencyMs > 2000 ? 'degraded' : 'healthy',
      circuit: circuitState.state,
      latencyMs,
      cacheSize,
    };
  } catch {
    return { status: 'down', circuit: circuitState.state, latencyMs: null, cacheSize };
  }
}

// Fallback content when API is down AND cache is empty
function getFallbackContent(context: string): any {
  const fallbacks: Record<string, any> = {
    'task-list': {
      message: 'Notion is currently unavailable. Please check status.notion.com',
      results: [],
      source: 'fallback',
    },
    'page-content': {
      message: 'This content is temporarily unavailable.',
      blocks: [],
      source: 'fallback',
    },
  };
  return fallbacks[context] ?? { message: 'Service temporarily unavailable', source: 'fallback' };
}

// Combined resilient query with all patterns
async function resilientQuery<T>(
  cacheKey: string,
  fn: () => Promise<T>,
  fallbackContext?: string
): Promise<QueryResult<T>> {
  try {
    return await queryWithFallback(cacheKey, fn);
  } catch (error) {
    if (fallbackContext) {
      return { data: getFallbackContent(fallbackContext), source: 'cache', cacheAge: -1 };
    }
    throw error;
  }
}
```

```python
from functools import lru_cache
import time

# Simple in-memory cache for fallback
_cache: dict[str, tuple[any, float]] = {}

def query_with_fallback(cache_key: str, fn, ttl: float = 3600):
    """Execute query with cache fallback on failure."""
    try:
        result = retry_with_backoff(fn)
        _cache[cache_key] = (result, time.time())
        return {"data": result, "source": "live"}
    except Exception:
        if cache_key in _cache:
            data, ts = _cache[cache_key]
            age = int(time.time() - ts)
            print(f"[fallback] Serving cached data ({age}s old)")
            return {"data": data, "source": "cache", "cache_age": age}
        raise

def health_check():
    """Check Notion API health."""
    start = time.time()
    try:
        notion.users.me()
        latency = (time.time() - start) * 1000
        return {"status": "degraded" if latency > 2000 else "healthy", "latency_ms": round(latency)}
    except Exception as e:
        return {"status": "down", "error": str(e)}
```

## Output

- Retry with exponential backoff handling 429, 500, 502, 503 errors
- Circuit breaker preventing cascade failures (5 failures = circuit opens)
- Offline cache serving stale data when API is unavailable
- Health check endpoint returning healthy/degraded/down status
- Fallback content for zero-downtime user experience
- Combined resilient query pattern composing all layers

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays open | Threshold too low for occasional errors | Increase `failureThreshold` to 10 |
| Stale cached data | Long TTL during extended outage | Add freshness indicator in UI, reduce TTL |
| `CircuitOpenError` in logs | API is down, circuit protecting | Expected behavior, check status.notion.com |
| Retries not helping | Error is permanent (400/401/404) | `isTransientError` filters these out |
| Health check shows degraded | Notion API latency > 2s | Normal during peak load, monitor trend |
| Memory growing | Large cache | Set `max` on LRU cache, reduce TTL |

## Examples

### System Health Dashboard

```typescript
// Expose as API endpoint: GET /api/health/notion
async function handleHealthCheck(req: Request): Promise<Response> {
  const health = await notionHealthCheck();
  const statusCode = health.status === 'healthy' ? 200 : health.status === 'degraded' ? 200 : 503;

  return new Response(JSON.stringify({
    service: 'notion',
    ...health,
    circuit: circuit.getState(),
    timestamp: new Date().toISOString(),
  }), { status: statusCode, headers: { 'Content-Type': 'application/json' } });
}
```

### Monitoring Alert Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: notion-reliability
    rules:
      - alert: NotionCircuitOpen
        expr: notion_circuit_state == 2  # 0=closed, 1=half-open, 2=open
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Notion API circuit breaker is open"

      - alert: NotionHighCacheRate
        expr: rate(notion_cache_hits[5m]) / rate(notion_total_requests[5m]) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Over 50% of Notion requests served from cache"
```

## Resources

- [Notion Status Page](https://status.notion.com)
- [Notion Request Limits](https://developers.notion.com/reference/request-limits)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)

## Next Steps

For governance and policy enforcement, see `notion-policy-guardrails`.
For scaling beyond single-token limits, see `notion-load-scale`.
