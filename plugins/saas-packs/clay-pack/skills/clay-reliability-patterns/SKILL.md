---
name: clay-reliability-patterns
description: |
  Build fault-tolerant Clay integrations with circuit breakers, dead letter queues, and graceful degradation.
  Use when building production Clay pipelines that need resilience,
  implementing retry strategies, or adding fault tolerance to enrichment workflows.
  Trigger with phrases like "clay reliability", "clay circuit breaker", "clay resilience",
  "clay fallback", "clay fault tolerance", "clay dead letter queue".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, clay-reliability]

---
# Clay Reliability Patterns

## Overview

Production reliability patterns for Clay data enrichment pipelines. Clay's async enrichment model, credit-based billing, and dependency on 150+ external data providers require specific resilience strategies: credit budget circuit breakers, webhook delivery tracking, dead letter queues for failed batches, and graceful degradation when Clay is unavailable.

## Prerequisites

- Clay integration in production or pre-production
- Redis or similar for state tracking
- Understanding of Clay's async enrichment model
- Monitoring infrastructure (see `clay-observability`)

## Instructions

### Step 1: Credit Budget Circuit Breaker

Stop processing when credit burn exceeds budget to prevent runaway costs:

```typescript
// src/clay/circuit-breaker.ts
class CreditCircuitBreaker {
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private dailyCreditsUsed = 0;
  private failureCount = 0;
  private lastFailureAt: Date | null = null;
  private readonly cooldownMs: number;

  constructor(
    private dailyLimit: number,
    private failureThreshold: number = 5,
    cooldownMinutes: number = 15,
  ) {
    this.cooldownMs = cooldownMinutes * 60 * 1000;
  }

  canProcess(estimatedCredits: number): { allowed: boolean; reason?: string } {
    // Check circuit state
    if (this.state === 'open') {
      // Check if cooldown has elapsed
      if (this.lastFailureAt && Date.now() - this.lastFailureAt.getTime() > this.cooldownMs) {
        this.state = 'half-open';
        console.log('Circuit breaker: half-open (testing)');
      } else {
        return { allowed: false, reason: `Circuit OPEN. Cooldown until ${new Date(this.lastFailureAt!.getTime() + this.cooldownMs).toISOString()}` };
      }
    }

    // Check budget
    if (this.dailyCreditsUsed + estimatedCredits > this.dailyLimit) {
      return { allowed: false, reason: `Daily credit limit reached: ${this.dailyCreditsUsed}/${this.dailyLimit}` };
    }

    return { allowed: true };
  }

  recordSuccess(creditsUsed: number) {
    this.dailyCreditsUsed += creditsUsed;
    if (this.state === 'half-open') {
      this.state = 'closed';
      this.failureCount = 0;
      console.log('Circuit breaker: closed (recovered)');
    }
  }

  recordFailure() {
    this.failureCount++;
    this.lastFailureAt = new Date();
    if (this.failureCount >= this.failureThreshold) {
      this.state = 'open';
      console.error(`Circuit breaker: OPEN after ${this.failureCount} failures`);
    }
  }

  resetDaily() {
    this.dailyCreditsUsed = 0;
  }
}
```

### Step 2: Dead Letter Queue for Failed Submissions

```typescript
// src/clay/dead-letter-queue.ts
interface DLQEntry {
  row: Record<string, unknown>;
  error: string;
  webhookUrl: string;
  failedAt: string;
  retryCount: number;
  maxRetries: number;
}

class ClayDLQ {
  private entries: DLQEntry[] = [];

  addToQueue(row: Record<string, unknown>, error: string, webhookUrl: string): void {
    this.entries.push({
      row,
      error,
      webhookUrl,
      failedAt: new Date().toISOString(),
      retryCount: 0,
      maxRetries: 3,
    });
    console.warn(`DLQ: Added row (${this.entries.length} total). Error: ${error}`);
  }

  async retryAll(): Promise<{ retried: number; succeeded: number; permanentFailures: number }> {
    let succeeded = 0, permanentFailures = 0;
    const remaining: DLQEntry[] = [];

    for (const entry of this.entries) {
      if (entry.retryCount >= entry.maxRetries) {
        permanentFailures++;
        continue;
      }

      try {
        const res = await fetch(entry.webhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(entry.row),
        });

        if (res.ok) {
          succeeded++;
        } else {
          entry.retryCount++;
          remaining.push(entry);
        }
      } catch {
        entry.retryCount++;
        remaining.push(entry);
      }

      await new Promise(r => setTimeout(r, 500)); // Pace retries
    }

    this.entries = remaining;
    return { retried: this.entries.length + succeeded + permanentFailures, succeeded, permanentFailures };
  }

  getStats() {
    return {
      pending: this.entries.length,
      byError: this.entries.reduce((acc, e) => {
        acc[e.error] = (acc[e.error] || 0) + 1;
        return acc;
      }, {} as Record<string, number>),
    };
  }
}
```

### Step 3: Webhook Health Monitor

```typescript
// src/clay/health-monitor.ts
class WebhookHealthMonitor {
  private successCount = 0;
  private failureCount = 0;
  private lastCheck: Date = new Date();
  private readonly windowMs = 5 * 60 * 1000; // 5-minute window

  record(success: boolean) {
    if (success) this.successCount++;
    else this.failureCount++;
  }

  getHealthScore(): { score: number; status: 'healthy' | 'degraded' | 'unhealthy' } {
    const total = this.successCount + this.failureCount;
    if (total === 0) return { score: 100, status: 'healthy' };

    const score = (this.successCount / total) * 100;

    // Reset window periodically
    if (Date.now() - this.lastCheck.getTime() > this.windowMs) {
      this.successCount = 0;
      this.failureCount = 0;
      this.lastCheck = new Date();
    }

    return {
      score,
      status: score > 95 ? 'healthy' : score > 80 ? 'degraded' : 'unhealthy',
    };
  }
}
```

### Step 4: Graceful Degradation When Clay Is Down

```typescript
// src/clay/fallback.ts
interface FallbackConfig {
  cacheEnrichedData: boolean;     // Cache previously enriched domains
  queueForLater: boolean;         // Queue submissions for when Clay recovers
  useLocalFallback: boolean;      // Fall back to local enrichment (limited)
}

class ClayWithFallback {
  private cache = new Map<string, Record<string, unknown>>();
  private offlineQueue: Record<string, unknown>[] = [];

  async enrichOrFallback(
    lead: Record<string, unknown>,
    webhookUrl: string,
    config: FallbackConfig,
  ): Promise<{ data: Record<string, unknown>; source: 'clay' | 'cache' | 'queued' | 'local' }> {
    // Try Clay first
    try {
      const res = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lead),
        signal: AbortSignal.timeout(10_000),
      });

      if (res.ok) {
        return { data: lead, source: 'clay' };
      }
    } catch {
      console.warn('Clay webhook unavailable — using fallback');
    }

    // Fallback 1: Check cache for this domain
    const domain = lead.domain as string;
    if (config.cacheEnrichedData && this.cache.has(domain)) {
      return { data: { ...lead, ...this.cache.get(domain) }, source: 'cache' };
    }

    // Fallback 2: Queue for later processing
    if (config.queueForLater) {
      this.offlineQueue.push(lead);
      return { data: lead, source: 'queued' };
    }

    // Fallback 3: Minimal local enrichment (domain -> company guess)
    if (config.useLocalFallback) {
      return {
        data: { ...lead, company_name: domain.replace(/\.\w+$/, '').replace(/-/g, ' ') },
        source: 'local',
      };
    }

    return { data: lead, source: 'local' };
  }

  async drainOfflineQueue(webhookUrl: string): Promise<number> {
    let drained = 0;
    while (this.offlineQueue.length > 0) {
      const lead = this.offlineQueue.shift()!;
      try {
        await fetch(webhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(lead),
        });
        drained++;
        await new Promise(r => setTimeout(r, 200));
      } catch {
        this.offlineQueue.unshift(lead); // Put back
        break;
      }
    }
    return drained;
  }
}
```

### Step 5: Combine All Patterns

```typescript
// src/clay/reliable-pipeline.ts
const circuitBreaker = new CreditCircuitBreaker(500); // 500 credits/day
const dlq = new ClayDLQ();
const healthMonitor = new WebhookHealthMonitor();

async function reliableEnrich(lead: Record<string, unknown>, webhookUrl: string): Promise<void> {
  // Check circuit breaker
  const { allowed, reason } = circuitBreaker.canProcess(6); // ~6 credits/lead
  if (!allowed) {
    dlq.addToQueue(lead, `Circuit breaker: ${reason}`, webhookUrl);
    return;
  }

  try {
    const res = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(lead),
    });

    if (res.ok) {
      circuitBreaker.recordSuccess(6);
      healthMonitor.record(true);
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    circuitBreaker.recordFailure();
    healthMonitor.record(false);
    dlq.addToQueue(lead, (err as Error).message, webhookUrl);
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Runaway credit spend | No budget circuit breaker | Implement credit budget limiter |
| Lost leads during outage | No DLQ | Queue failed submissions for retry |
| Silent webhook failures | No health monitoring | Track success/failure rates |
| Clay outage blocks pipeline | No fallback | Implement cache + queue fallback |

## Resources

- [Clay Community](https://community.clay.com)
- [BullMQ Dead Letter Queue](https://docs.bullmq.io/guide/dead-letter-queue)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)

## Next Steps

For policy guardrails, see `clay-policy-guardrails`.
