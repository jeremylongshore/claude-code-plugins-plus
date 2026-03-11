---
name: openevidence-rate-limits
description: |
  Implement OpenEvidence rate limiting, backoff, and request optimization.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for clinical queries.
  Trigger with phrases like "openevidence rate limit", "openevidence throttling",
  "openevidence 429", "openevidence retry", "openevidence backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# OpenEvidence Rate Limits

## Overview
Rate limit management for OpenEvidence clinical query API. Clinical decision support queries are latency-sensitive but also expensive (web-scale medical literature search per query), requiring careful throughput management.

## Prerequisites
- OpenEvidence API access
- Understanding of clinical workflow request patterns
- Redis for rate tracking (recommended)

## OpenEvidence Rate Limits

| Endpoint | Limit | Window | Burst |
|----------|-------|--------|-------|
| Clinical Query | 60/min | Per API key | 10 concurrent |
| DeepConsult | 10/min | Per API key | 2 concurrent |
| Feedback | 120/min | Per API key | 20 concurrent |

## Instructions

### Step 1: Per-Endpoint Rate Limiter

Clinical queries and DeepConsult have different limits. Track separately.

```typescript
class OpenEvidenceRateLimiter {
  private limits: Record<string, { rpm: number; concurrent: number }> = {
    'query': { rpm: 60, concurrent: 10 },
    'deepconsult': { rpm: 10, concurrent: 2 },
    'feedback': { rpm: 120, concurrent: 20 },
  };
  private active: Map<string, number> = new Map();
  private requests: Map<string, number[]> = new Map();

  async acquire(endpoint: string): Promise<void> {
    const limit = this.limits[endpoint];
    if (!limit) throw new Error(`Unknown endpoint: ${endpoint}`);

    // Check concurrent
    const active = this.active.get(endpoint) || 0;
    if (active >= limit.concurrent) {
      await this.waitForSlot(endpoint);
    }

    // Check RPM
    const now = Date.now();
    const times = (this.requests.get(endpoint) || []).filter(t => now - t < 60000);
    if (times.length >= limit.rpm) {
      const waitMs = 60000 - (now - times[0]);
      await new Promise(r => setTimeout(r, waitMs + 100));
    }

    this.active.set(endpoint, (this.active.get(endpoint) || 0) + 1);
    times.push(Date.now());
    this.requests.set(endpoint, times);
  }

  release(endpoint: string): void {
    this.active.set(endpoint, Math.max(0, (this.active.get(endpoint) || 0) - 1));
  }
}
```

### Step 2: Clinical Query Priority Queue

Stat queries should preempt routine queries.

```typescript
class ClinicalQueryQueue {
  private statQueue: Array<() => Promise<any>> = [];
  private routineQueue: Array<() => Promise<any>> = [];
  private limiter = new OpenEvidenceRateLimiter();

  async submit(query: any, urgency: 'stat' | 'routine'): Promise<any> {
    return new Promise((resolve, reject) => {
      const task = async () => {
        await this.limiter.acquire('query');
        try {
          const result = await openevidence.query(query);
          resolve(result);
        } catch (e) { reject(e); }
        finally { this.limiter.release('query'); }
      };
      if (urgency === 'stat') this.statQueue.push(task);
      else this.routineQueue.push(task);
      this.process();
    });
  }

  private async process() {
    const task = this.statQueue.shift() || this.routineQueue.shift();
    if (task) await task();
  }
}
```

### Step 3: Backoff Strategy for 429 Responses

```typescript
async function queryWithBackoff(query: any, maxRetries = 3): Promise<any> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await openevidence.query(query);
    } catch (e: any) {
      if (e.status === 429 && attempt < maxRetries) {
        const retryAfter = parseInt(e.headers?.['retry-after'] || '5');
        await new Promise(r => setTimeout(r, retryAfter * 1000));
      } else { throw e; }
    }
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 on clinical query | Exceeded 60 RPM | Queue with priority, backoff |
| DeepConsult rejected | Exceeded 10 RPM or 2 concurrent | Queue deep consults separately |
| Stat query delayed | Behind routine queries | Implement priority queue |
| Concurrent limit hit | Too many parallel queries | Track and limit active requests |

## Examples

### Usage Dashboard
```typescript
const status = {
  query: { active: limiter.active.get('query'), rpm_used: limiter.requests.get('query')?.length },
  deepconsult: { active: limiter.active.get('deepconsult'), rpm_used: limiter.requests.get('deepconsult')?.length }
};
```

## Resources
- [OpenEvidence API](https://www.openevidence.com)
