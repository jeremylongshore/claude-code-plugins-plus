---
name: canva-reliability-patterns
description: |
  Implement reliability patterns for Canva Connect API — circuit breakers, idempotency, graceful degradation.
  Use when building fault-tolerant Canva integrations, implementing retry strategies,
  or adding resilience to production Canva services.
  Trigger with phrases like "canva reliability", "canva circuit breaker",
  "canva resilience", "canva fallback", "canva fault tolerance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Reliability Patterns

## Overview

Production-grade reliability patterns for the Canva Connect API. The API has async operations (exports, uploads, autofills) that can fail or timeout, OAuth tokens that expire every 4 hours, and rate limits that require backoff.

## Circuit Breaker

```typescript
import CircuitBreaker from 'opossum';

const canvaBreaker = new CircuitBreaker(
  async (fn: () => Promise<any>) => fn(),
  {
    timeout: 30000,              // 30s before failure
    errorThresholdPercentage: 50, // Open after 50% failure rate
    resetTimeout: 60000,          // Try again after 60s
    volumeThreshold: 5,           // Min 5 requests before evaluating
  }
);

canvaBreaker.on('open', () => {
  console.warn('[canva] Circuit OPEN — Canva API unreachable, failing fast');
});

canvaBreaker.on('halfOpen', () => {
  console.info('[canva] Circuit HALF-OPEN — testing Canva recovery');
});

canvaBreaker.on('close', () => {
  console.info('[canva] Circuit CLOSED — Canva API recovered');
});

// Usage
async function createDesignSafe(body: object, token: string) {
  return canvaBreaker.fire(async () => {
    return canvaAPI('/designs', token, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  });
}
```

## Graceful Degradation

```typescript
// When Canva is down, degrade gracefully instead of breaking the entire app
async function getDesignWithFallback(
  designId: string,
  token: string,
  cache: LRUCache<string, any>
): Promise<{ data: any; source: 'live' | 'cache' | 'placeholder' }> {
  try {
    const data = await canvaBreaker.fire(async () =>
      canvaAPI(`/designs/${designId}`, token)
    );
    cache.set(designId, data);
    return { data, source: 'live' };
  } catch {
    // Try cached version
    const cached = cache.get(designId);
    if (cached) {
      return { data: cached, source: 'cache' };
    }

    // Return placeholder
    return {
      data: {
        design: {
          id: designId,
          title: 'Design temporarily unavailable',
          urls: { edit_url: '#', view_url: '#' },
        },
      },
      source: 'placeholder',
    };
  }
}
```

## Async Job Resilience

```typescript
// Export, upload, and autofill jobs can fail — wrap with retry
async function resilientExport(
  designId: string,
  format: object,
  token: string,
  maxRetries = 2
): Promise<string[]> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // Start export
      const { job } = await canvaAPI('/exports', token, {
        method: 'POST',
        body: JSON.stringify({ design_id: designId, format }),
      });

      // Poll with timeout
      const urls = await pollWithTimeout(job.id, token, 60000);
      return urls;
    } catch (error: any) {
      if (attempt === maxRetries) throw error;

      // Don't retry on client errors (400, 403, 404)
      if (error.status && error.status < 500 && error.status !== 429) throw error;

      const delay = 5000 * Math.pow(2, attempt);
      console.warn(`Export attempt ${attempt + 1} failed, retrying in ${delay / 1000}s`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}

async function pollWithTimeout(
  exportId: string,
  token: string,
  timeoutMs: number
): Promise<string[]> {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const { job } = await canvaAPI(`/exports/${exportId}`, token);
    if (job.status === 'success') return job.urls;
    if (job.status === 'failed') throw new Error(`Export failed: ${job.error?.code}`);
    await new Promise(r => setTimeout(r, 2000));
  }

  throw new Error('Export polling timeout');
}
```

## Token Refresh Resilience

```typescript
// Token refresh is critical — handle every failure mode
async function resilientTokenRefresh(
  refreshToken: string,
  config: { clientId: string; clientSecret: string }
): Promise<{ accessToken: string; refreshToken: string; expiresAt: number } | null> {
  const basicAuth = Buffer.from(`${config.clientId}:${config.clientSecret}`).toString('base64');

  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const res = await fetch('https://api.canva.com/rest/v1/oauth/token', {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${basicAuth}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'refresh_token',
          refresh_token: refreshToken,
        }),
        signal: AbortSignal.timeout(10000),
      });

      if (res.ok) {
        const data = await res.json();
        return {
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          expiresAt: Date.now() + data.expires_in * 1000,
        };
      }

      if (res.status === 400 || res.status === 401) {
        // Invalid refresh token — user must re-authorize
        console.error('[canva] Refresh token invalid — user must re-authorize');
        return null; // Signal caller to initiate new OAuth flow
      }

      // 5xx — retry
    } catch {
      // Network error — retry
    }

    await new Promise(r => setTimeout(r, 2000 * Math.pow(2, attempt)));
  }

  console.error('[canva] Token refresh failed after 3 attempts');
  return null;
}
```

## Dead Letter Queue for Failed Operations

```typescript
interface FailedOperation {
  id: string;
  operation: 'export' | 'autofill' | 'upload';
  payload: any;
  userId: string;
  error: string;
  attempts: number;
  lastAttempt: Date;
}

class CanvaDeadLetterQueue {
  constructor(private db: Database) {}

  async add(op: Omit<FailedOperation, 'id' | 'lastAttempt'>): Promise<void> {
    await this.db.dlq.insert({
      ...op,
      id: crypto.randomUUID(),
      lastAttempt: new Date(),
    });
  }

  async processNext(getToken: (userId: string) => Promise<string | null>): Promise<boolean> {
    const entry = await this.db.dlq.findOne({ attempts: { $lt: 5 } });
    if (!entry) return false;

    const token = await getToken(entry.userId);
    if (!token) {
      console.warn(`DLQ: User ${entry.userId} has no valid token — skipping`);
      return false;
    }

    try {
      await this.retryOperation(entry, token);
      await this.db.dlq.delete(entry.id);
      return true;
    } catch {
      await this.db.dlq.update(entry.id, {
        attempts: entry.attempts + 1,
        lastAttempt: new Date(),
      });
      return false;
    }
  }

  private async retryOperation(entry: FailedOperation, token: string) {
    switch (entry.operation) {
      case 'export': return canvaAPI('/exports', token, { method: 'POST', body: JSON.stringify(entry.payload) });
      case 'autofill': return canvaAPI('/autofills', token, { method: 'POST', body: JSON.stringify(entry.payload) });
    }
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays open | Threshold too low | Increase volumeThreshold |
| Token refresh fails | Single-use refresh token reused | Always store new token |
| Export retries waste quota | Re-starting export | Track export job IDs |
| DLQ growing | Persistent issue | Investigate root cause |

## Resources

- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Opossum](https://nodeshift.dev/opossum/)
- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)

## Next Steps

For policy enforcement, see `canva-policy-guardrails`.
