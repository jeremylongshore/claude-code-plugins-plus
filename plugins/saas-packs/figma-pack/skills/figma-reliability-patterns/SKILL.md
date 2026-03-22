---
name: figma-reliability-patterns
description: |
  Build resilient Figma integrations with circuit breakers, fallbacks, and graceful degradation.
  Use when implementing fault tolerance, handling Figma outages gracefully,
  or building production-grade reliability into Figma API consumers.
  Trigger with phrases like "figma reliability", "figma circuit breaker",
  "figma fallback", "figma resilience", "figma graceful degradation".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Reliability Patterns

## Overview
Production reliability patterns for Figma REST API integrations. Figma is an external dependency -- your application must handle its outages, rate limits, and slow responses without cascading failures.

## Prerequisites
- Working Figma API integration
- Understanding of circuit breaker pattern
- Cache or file system for fallback data

## Instructions

### Step 1: Circuit Breaker
```typescript
// Prevent cascading failures when Figma is down
class FigmaCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private threshold = 5,        // Open after 5 failures
    private resetTimeMs = 30_000  // Try again after 30s
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.resetTimeMs) {
        this.state = 'half-open';
        console.log('[figma-circuit] State: half-open (testing recovery)');
      } else {
        throw new Error('Figma circuit breaker is OPEN -- failing fast');
      }
    }

    try {
      const result = await fn();
      if (this.state === 'half-open') {
        this.state = 'closed';
        this.failures = 0;
        console.log('[figma-circuit] State: closed (recovered)');
      }
      return result;
    } catch (error) {
      this.failures++;
      this.lastFailure = Date.now();

      if (this.failures >= this.threshold) {
        this.state = 'open';
        console.warn(`[figma-circuit] State: OPEN after ${this.failures} failures`);
      }
      throw error;
    }
  }

  getState() { return this.state; }
}

const figmaBreaker = new FigmaCircuitBreaker();

// Usage
async function safeFigmaCall<T>(fn: () => Promise<T>): Promise<T> {
  return figmaBreaker.execute(fn);
}
```

### Step 2: Cached Fallback
```typescript
import { readFileSync, writeFileSync, existsSync } from 'fs';

// Serve cached data when Figma is unavailable
class FigmaFallbackCache {
  constructor(private cacheDir = '.figma-cache') {}

  private getPath(key: string) {
    return `${this.cacheDir}/${key.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
  }

  save(key: string, data: any) {
    const { mkdirSync } = require('fs');
    mkdirSync(this.cacheDir, { recursive: true });
    writeFileSync(this.getPath(key), JSON.stringify({
      data,
      cachedAt: new Date().toISOString(),
    }));
  }

  load(key: string): { data: any; cachedAt: string } | null {
    const path = this.getPath(key);
    if (!existsSync(path)) return null;
    return JSON.parse(readFileSync(path, 'utf-8'));
  }
}

const fallbackCache = new FigmaFallbackCache();

async function fetchWithFallback<T>(
  cacheKey: string,
  fetcher: () => Promise<T>
): Promise<{ data: T; fromCache: boolean; cachedAt?: string }> {
  try {
    const data = await safeFigmaCall(fetcher);
    // Update cache with fresh data
    fallbackCache.save(cacheKey, data);
    return { data, fromCache: false };
  } catch (error) {
    console.warn(`Figma unavailable, loading cached ${cacheKey}`);
    const cached = fallbackCache.load(cacheKey);
    if (cached) {
      return { data: cached.data as T, fromCache: true, cachedAt: cached.cachedAt };
    }
    throw new Error(`Figma unavailable and no cached data for ${cacheKey}`);
  }
}
```

### Step 3: Retry with Backoff (Respecting Retry-After)
```typescript
async function figmaRetry<T>(
  fn: () => Promise<Response>,
  maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fn();

    if (res.ok) return res.json();

    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
      if (attempt < maxRetries) {
        console.warn(`429 -- waiting ${retryAfter}s (attempt ${attempt + 1}/${maxRetries})`);
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        continue;
      }
    }

    if (res.status >= 500 && attempt < maxRetries) {
      const delay = Math.min(1000 * Math.pow(2, attempt), 30_000);
      const jitter = Math.random() * 1000;
      await new Promise(r => setTimeout(r, delay + jitter));
      continue;
    }

    throw new FigmaApiError(res.status, await res.text());
  }
  throw new Error('Max retries exceeded');
}
```

### Step 4: Request Timeout
```typescript
// Prevent requests from hanging indefinitely
async function figmaFetchWithTimeout(
  path: string,
  token: string,
  timeoutMs = 15_000
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(`https://api.figma.com${path}`, {
      headers: { 'X-Figma-Token': token },
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`Figma request timed out after ${timeoutMs}ms: ${path}`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
```

### Step 5: Health-Aware Request Routing
```typescript
// Only make non-critical Figma calls when the API is healthy
class FigmaHealthTracker {
  private healthy = true;
  private lastCheck = 0;
  private checkIntervalMs = 30_000;

  async isHealthy(token: string): Promise<boolean> {
    if (Date.now() - this.lastCheck < this.checkIntervalMs) {
      return this.healthy;
    }

    try {
      const res = await figmaFetchWithTimeout('/v1/me', token, 5000);
      this.healthy = res.ok;
    } catch {
      this.healthy = false;
    }
    this.lastCheck = Date.now();
    return this.healthy;
  }
}

const healthTracker = new FigmaHealthTracker();

async function conditionalFigmaCall<T>(
  token: string,
  critical: boolean,
  fn: () => Promise<T>,
  fallback: () => Promise<T>
): Promise<T> {
  const healthy = await healthTracker.isHealthy(token);

  if (!healthy && !critical) {
    console.log('Figma unhealthy, using fallback for non-critical call');
    return fallback();
  }

  return fetchWithFallback('default', fn).then(r => r.data);
}
```

## Output
- Circuit breaker preventing cascading failures
- Cached fallback serving stale data during outages
- Retry logic respecting Figma's `Retry-After` header
- Request timeouts preventing hung connections
- Health-aware routing for non-critical calls

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays open | Threshold too low | Increase threshold or decrease reset time |
| Stale fallback data | Cache not refreshed | Refresh cache on successful calls |
| Retry loops | Not respecting Retry-After | Always use the header value |
| Timeout too short | Large file responses | Increase timeout for `/v1/files` calls |

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Figma Rate Limits](https://developers.figma.com/docs/rest-api/rate-limits/)
- [Figma Status Page](https://status.figma.com)

## Next Steps
For policy enforcement, see `figma-policy-guardrails`.
