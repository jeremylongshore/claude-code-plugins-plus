---
name: customerio-sdk-patterns
description: |
  Apply production-ready Customer.io SDK patterns.
  Use when implementing typed clients, retry logic, event batching,
  or singleton management for customerio-node.
  Trigger: "customer.io best practices", "customer.io patterns",
  "production customer.io", "customer.io architecture", "customer.io singleton".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, sdk, patterns, typescript]

---
# Customer.io SDK Patterns

## Overview

Production-ready patterns for `customerio-node`: type-safe wrappers with enum-constrained events, retry with exponential backoff, event batching for high-volume scenarios, and singleton lifecycle management.

## Prerequisites

- `customerio-node` installed
- TypeScript project (recommended for type-safe patterns)
- Understanding of your event taxonomy

## Instructions

### Pattern 1: Type-Safe Client Wrapper

```typescript
// lib/customerio-typed.ts
import { TrackClient, RegionUS, RegionEU } from "customerio-node";

// Define your event taxonomy as a union type
type CioEvent =
  | { name: "signed_up"; data: { method: string; source?: string } }
  | { name: "plan_changed"; data: { from: string; to: string; mrr: number } }
  | { name: "feature_used"; data: { feature: string; duration_ms?: number } }
  | { name: "checkout_completed"; data: { order_id: string; total: number; items: number } }
  | { name: "subscription_cancelled"; data: { reason: string; feedback?: string } };

// Define user attributes with strict types
interface CioUserAttributes {
  email: string;
  first_name?: string;
  last_name?: string;
  plan?: "free" | "starter" | "pro" | "enterprise";
  company?: string;
  created_at?: number;       // Unix seconds
  last_seen_at?: number;     // Unix seconds
  [key: string]: unknown;    // Allow additional attributes
}

export class TypedCioClient {
  private client: TrackClient;

  constructor(siteId: string, apiKey: string, region: "us" | "eu" = "us") {
    this.client = new TrackClient(siteId, apiKey, {
      region: region === "eu" ? RegionEU : RegionUS,
    });
  }

  async identify(userId: string, attributes: CioUserAttributes): Promise<void> {
    await this.client.identify(userId, {
      ...attributes,
      last_seen_at: Math.floor(Date.now() / 1000),
    });
  }

  async track(userId: string, event: CioEvent): Promise<void> {
    await this.client.track(userId, {
      name: event.name,
      data: { ...event.data, tracked_at: Math.floor(Date.now() / 1000) },
    });
  }

  async suppress(userId: string): Promise<void> {
    await this.client.suppress(userId);
  }

  async destroy(userId: string): Promise<void> {
    await this.client.destroy(userId);
  }
}
```

### Pattern 2: Retry with Exponential Backoff

```typescript
// lib/customerio-retry.ts
interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterFactor: number;  // 0 to 1
}

const DEFAULT_RETRY: RetryOptions = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 30000,
  jitterFactor: 0.3,
};

async function withRetry<T>(
  fn: () => Promise<T>,
  opts: RetryOptions = DEFAULT_RETRY
): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      lastError = err;
      const statusCode = err.statusCode ?? err.status;

      // Don't retry client errors (except 429 rate limit)
      if (statusCode >= 400 && statusCode < 500 && statusCode !== 429) {
        throw err;
      }

      if (attempt === opts.maxRetries) break;

      // Exponential backoff with jitter
      const delay = Math.min(
        opts.baseDelayMs * Math.pow(2, attempt),
        opts.maxDelayMs
      );
      const jitter = delay * opts.jitterFactor * Math.random();
      await new Promise((r) => setTimeout(r, delay + jitter));
    }
  }
  throw lastError;
}

// Usage with Customer.io client
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

// Wrap any operation with retry
await withRetry(() =>
  cio.identify("user-123", { email: "user@example.com" })
);

await withRetry(() =>
  cio.track("user-123", { name: "page_viewed", data: { url: "/pricing" } })
);
```

### Pattern 3: Event Queue with Batching

```typescript
// lib/customerio-batch.ts
import { TrackClient, RegionUS } from "customerio-node";

interface QueuedEvent {
  userId: string;
  name: string;
  data?: Record<string, any>;
}

export class CioBatchTracker {
  private queue: QueuedEvent[] = [];
  private timer: NodeJS.Timeout | null = null;
  private client: TrackClient;

  constructor(
    private readonly batchSize: number = 50,
    private readonly flushIntervalMs: number = 5000
  ) {
    this.client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_TRACK_API_KEY!,
      { region: RegionUS }
    );
    this.startTimer();
  }

  enqueue(userId: string, name: string, data?: Record<string, any>): void {
    this.queue.push({ userId, name, data });
    if (this.queue.length >= this.batchSize) {
      this.flush();
    }
  }

  async flush(): Promise<void> {
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0, this.batchSize);
    const concurrency = 10;

    for (let i = 0; i < batch.length; i += concurrency) {
      const chunk = batch.slice(i, i + concurrency);
      await Promise.allSettled(
        chunk.map((event) =>
          this.client.track(event.userId, {
            name: event.name,
            data: event.data,
          })
        )
      );
    }
  }

  private startTimer(): void {
    this.timer = setInterval(() => this.flush(), this.flushIntervalMs);
  }

  async shutdown(): Promise<void> {
    if (this.timer) clearInterval(this.timer);
    await this.flush();
  }
}

// Usage
const tracker = new CioBatchTracker(50, 5000);

// Non-blocking — events are queued and flushed automatically
tracker.enqueue("user-1", "page_viewed", { url: "/home" });
tracker.enqueue("user-2", "button_clicked", { button: "cta" });

// On process exit
process.on("SIGTERM", async () => {
  await tracker.shutdown();
  process.exit(0);
});
```

### Pattern 4: Singleton with Validation

```typescript
// lib/customerio-singleton.ts
import { TrackClient, APIClient, RegionUS, RegionEU } from "customerio-node";

class CioClientFactory {
  private static trackInstance: TrackClient | null = null;
  private static appInstance: APIClient | null = null;

  static getTrackClient(): TrackClient {
    if (!this.trackInstance) {
      const siteId = process.env.CUSTOMERIO_SITE_ID;
      const apiKey = process.env.CUSTOMERIO_TRACK_API_KEY;
      if (!siteId || !apiKey) {
        throw new Error(
          "Missing CUSTOMERIO_SITE_ID or CUSTOMERIO_TRACK_API_KEY. " +
          "Set these in your environment or .env file."
        );
      }
      const region = process.env.CUSTOMERIO_REGION === "eu" ? RegionEU : RegionUS;
      this.trackInstance = new TrackClient(siteId, apiKey, { region });
    }
    return this.trackInstance;
  }

  static getAppClient(): APIClient {
    if (!this.appInstance) {
      const appKey = process.env.CUSTOMERIO_APP_API_KEY;
      if (!appKey) {
        throw new Error(
          "Missing CUSTOMERIO_APP_API_KEY. " +
          "Set this in your environment or .env file."
        );
      }
      const region = process.env.CUSTOMERIO_REGION === "eu" ? RegionEU : RegionUS;
      this.appInstance = new APIClient(appKey, { region });
    }
    return this.appInstance;
  }

  /** Reset for testing */
  static reset(): void {
    this.trackInstance = null;
    this.appInstance = null;
  }
}

// Usage — same instance everywhere
const cio = CioClientFactory.getTrackClient();
const api = CioClientFactory.getAppClient();
```

## Pattern Summary

| Pattern | When to Use | Key Benefit |
|---------|------------|-------------|
| Typed Client | Always | Compile-time safety on events + attributes |
| Retry + Backoff | Production API calls | Handles transient 5xx and 429 errors |
| Batch Queue | High-volume tracking (>100 events/sec) | Reduces connection overhead, respects rate limits |
| Singleton Factory | Multi-module apps | Prevents connection leaks, validates config once |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Type mismatch | Wrong event data shape | Use TypeScript union types for events |
| Queue memory growth | Events produced faster than flushed | Lower `batchSize`, increase flush frequency |
| Retry exhausted (3x) | Persistent API failure | Check credentials, Customer.io status page |
| Singleton null credentials | Env vars not loaded | Ensure `dotenv` loads before client creation |

## Resources

- [customerio-node SDK](https://github.com/customerio/customerio-node)
- [Track API Rate Limits](https://docs.customer.io/integrations/api/track/)
- [About Customer.io APIs](https://docs.customer.io/integrations/api/customerio-apis/)

## Next Steps

After implementing patterns, proceed to `customerio-primary-workflow` for messaging workflows.
