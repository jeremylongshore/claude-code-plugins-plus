---
name: customerio-reliability-patterns
description: |
  Implement Customer.io reliability and fault-tolerance patterns.
  Use when building circuit breakers, fallback queues, idempotency,
  or graceful degradation for Customer.io integrations.
  Trigger: "customer.io reliability", "customer.io resilience",
  "customer.io circuit breaker", "customer.io fault tolerance".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, reliability, circuit-breaker, resilience]

---
# Customer.io Reliability Patterns

## Overview

Implement fault-tolerant Customer.io integrations: circuit breaker (stop cascading failures), retry with jitter (handle transient errors), fallback queue (survive outages), idempotency guard (prevent duplicates), and graceful degradation (never crash your app for analytics).

## Prerequisites

- Working Customer.io integration
- Understanding of failure modes (429, 5xx, timeouts, DNS failures)
- Redis (recommended for queue-based patterns)

## Instructions

### Pattern 1: Circuit Breaker

```typescript
// lib/circuit-breaker.ts
type CircuitState = "CLOSED" | "OPEN" | "HALF_OPEN";

export class CircuitBreaker {
  private state: CircuitState = "CLOSED";
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime = 0;

  constructor(
    private readonly failureThreshold: number = 5,
    private readonly successThreshold: number = 3,
    private readonly resetTimeoutMs: number = 30000
  ) {}

  get currentState(): CircuitState {
    if (this.state === "OPEN") {
      // Check if enough time has passed to try again
      if (Date.now() - this.lastFailureTime > this.resetTimeoutMs) {
        this.state = "HALF_OPEN";
        this.successCount = 0;
      }
    }
    return this.state;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.currentState === "OPEN") {
      throw new Error("Circuit breaker is OPEN — Customer.io calls blocked");
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

  private onSuccess(): void {
    this.failureCount = 0;
    if (this.state === "HALF_OPEN") {
      this.successCount++;
      if (this.successCount >= this.successThreshold) {
        this.state = "CLOSED";
        console.log("Circuit breaker: CLOSED (recovered)");
      }
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    if (this.failureCount >= this.failureThreshold) {
      this.state = "OPEN";
      console.warn(
        `Circuit breaker: OPEN (${this.failureCount} failures). ` +
        `Will retry in ${this.resetTimeoutMs / 1000}s`
      );
    }
  }

  getStatus(): { state: CircuitState; failures: number; lastFailure: Date | null } {
    return {
      state: this.currentState,
      failures: this.failureCount,
      lastFailure: this.lastFailureTime ? new Date(this.lastFailureTime) : null,
    };
  }
}
```

### Pattern 2: Retry with Jitter

```typescript
// lib/retry.ts
export async function retryWithJitter<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      const status = err.statusCode ?? err.status;

      // Don't retry client errors (except 429)
      if (status >= 400 && status < 500 && status !== 429) throw err;

      if (attempt === maxRetries) throw err;

      // Exponential backoff: 1s, 2s, 4s + random jitter up to 30%
      const delay = baseDelayMs * Math.pow(2, attempt);
      const jitter = delay * 0.3 * Math.random();
      await new Promise((r) => setTimeout(r, delay + jitter));
    }
  }
  throw new Error("Unreachable");
}
```

### Pattern 3: Fallback Queue

```typescript
// lib/customerio-fallback.ts
import { Queue, Worker } from "bullmq";
import { TrackClient, RegionUS } from "customerio-node";

const REDIS_URL = process.env.REDIS_URL ?? "redis://localhost:6379";

// Queue for operations that fail when circuit breaker is open
const fallbackQueue = new Queue("cio:fallback", {
  connection: { url: REDIS_URL },
  defaultJobOptions: {
    attempts: 10,
    backoff: { type: "exponential", delay: 60000 }, // Start at 1 min
    removeOnComplete: 1000,
    removeOnFail: 5000,
  },
});

export async function enqueueFallback(
  operation: "identify" | "track" | "suppress",
  data: Record<string, any>
): Promise<void> {
  await fallbackQueue.add(operation, data);
  console.log(`CIO fallback: queued ${operation} (circuit open)`);
}

// Worker processes fallback queue when CIO is back up
export function startFallbackWorker(): void {
  const cio = new TrackClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_TRACK_API_KEY!,
    { region: RegionUS }
  );

  new Worker("cio:fallback", async (job) => {
    switch (job.name) {
      case "identify":
        await cio.identify(job.data.userId, job.data.attrs);
        break;
      case "track":
        await cio.track(job.data.userId, job.data.event);
        break;
      case "suppress":
        await cio.suppress(job.data.userId);
        break;
    }
  }, {
    connection: { url: REDIS_URL },
    concurrency: 5,
  });
}
```

### Pattern 4: Resilient Client (All Patterns Combined)

```typescript
// lib/customerio-resilient.ts
import { TrackClient, RegionUS } from "customerio-node";
import { CircuitBreaker } from "./circuit-breaker";
import { retryWithJitter } from "./retry";
import { enqueueFallback } from "./customerio-fallback";

export class ResilientCioClient {
  private client: TrackClient;
  private breaker: CircuitBreaker;

  constructor(siteId: string, apiKey: string) {
    this.client = new TrackClient(siteId, apiKey, { region: RegionUS });
    this.breaker = new CircuitBreaker(5, 3, 30000);
  }

  async identify(userId: string, attrs: Record<string, any>): Promise<void> {
    try {
      await this.breaker.execute(() =>
        retryWithJitter(() => this.client.identify(userId, attrs))
      );
    } catch (err: any) {
      if (err.message.includes("Circuit breaker is OPEN")) {
        await enqueueFallback("identify", { userId, attrs });
        return; // Queued for later — don't throw
      }
      // For non-circuit errors, log but don't crash the app
      console.error(`CIO identify failed for ${userId}: ${err.message}`);
    }
  }

  async track(
    userId: string,
    name: string,
    data?: Record<string, any>
  ): Promise<void> {
    try {
      await this.breaker.execute(() =>
        retryWithJitter(() =>
          this.client.track(userId, { name, data })
        )
      );
    } catch (err: any) {
      if (err.message.includes("Circuit breaker is OPEN")) {
        await enqueueFallback("track", { userId, event: { name, data } });
        return;
      }
      console.error(`CIO track failed for ${userId}/${name}: ${err.message}`);
    }
  }

  getHealthStatus() {
    return this.breaker.getStatus();
  }
}
```

### Pattern 5: Idempotency Guard

```typescript
// lib/idempotency.ts
import { createHash } from "crypto";

const processedOps = new Map<string, number>();
const MAX_ENTRIES = 100_000;
const TTL_MS = 5 * 60 * 1000;  // 5 minutes

export function isIdempotent(
  operation: string,
  userId: string,
  data: any
): boolean {
  const hash = createHash("sha256")
    .update(`${operation}:${userId}:${JSON.stringify(data)}`)
    .digest("hex")
    .substring(0, 16);

  const existing = processedOps.get(hash);
  if (existing && Date.now() - existing < TTL_MS) {
    return true; // Already processed within TTL
  }

  processedOps.set(hash, Date.now());

  // Prune old entries
  if (processedOps.size > MAX_ENTRIES) {
    const cutoff = Date.now() - TTL_MS;
    for (const [key, time] of processedOps) {
      if (time < cutoff) processedOps.delete(key);
    }
  }

  return false;
}
```

### Pattern 6: Health Check Endpoint

```typescript
// routes/health.ts — include circuit breaker status
import { ResilientCioClient } from "../lib/customerio-resilient";

const cio = new ResilientCioClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!
);

app.get("/health/customerio", (_req, res) => {
  const status = cio.getHealthStatus();
  const healthy = status.state === "CLOSED";

  res.status(healthy ? 200 : 503).json({
    customerio: {
      circuit_state: status.state,
      failure_count: status.failures,
      last_failure: status.lastFailure?.toISOString() ?? null,
    },
  });
});
```

## Pattern Selection Guide

| Scenario | Pattern | Priority |
|----------|---------|----------|
| Transient 5xx errors | Retry with jitter | Must have |
| Extended Customer.io outage | Circuit breaker + fallback queue | Must have |
| Duplicate events from retries | Idempotency guard | Should have |
| App must never crash for tracking | Graceful degradation (catch all) | Must have |
| Need visibility into reliability | Health check endpoint | Should have |

## Reliability Checklist

- [ ] Circuit breaker implemented with reasonable thresholds
- [ ] Retry with exponential backoff and jitter
- [ ] Fallback queue for circuit-open operations
- [ ] Idempotency guard for retried operations
- [ ] All Customer.io calls wrapped in try/catch (never crash the app)
- [ ] Health check exposes circuit breaker state
- [ ] Graceful shutdown drains queues and flushes buffers
- [ ] Timeout configured on HTTP calls

## Resources

- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Exponential Backoff with Jitter (AWS)](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- [BullMQ Documentation](https://bullmq.io/)

## Next Steps

After reliability patterns, proceed to `customerio-load-scale` for load testing and scaling.
