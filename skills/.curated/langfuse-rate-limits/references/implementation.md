# Langfuse Rate Limits - Implementation Details

## Optimal Batching Configuration

```typescript
import { Langfuse } from "langfuse";

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  flushAt: 50,
  flushInterval: 5000,
  requestTimeout: 30000,
});
```

## Exponential Backoff

```typescript
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterMs: number;
}

async function withBackoff<T>(
  operation: () => Promise<T>,
  config: RetryConfig = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 30000, jitterMs: 500 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;
      const status = error.status || error.response?.status;
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      const retryAfter = error.headers?.get?.("Retry-After");
      let delay: number;
      if (retryAfter) {
        delay = parseInt(retryAfter) * 1000;
      } else {
        const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * config.jitterMs;
        delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);
      }
      console.warn(`Rate limited. Attempt ${attempt + 1}/${config.maxRetries}. Retrying in ${delay}ms...`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

## Rate Limit-Aware Wrapper

```typescript
class RateLimitedLangfuse {
  private langfuse: Langfuse;
  private pendingEvents: number = 0;
  private maxConcurrent: number = 100;
  private queue: Array<() => void> = [];

  constructor(config?: ConstructorParameters<typeof Langfuse>[0]) {
    this.langfuse = new Langfuse({ ...config, flushAt: 50, flushInterval: 5000 });
  }

  private async waitForCapacity(): Promise<void> {
    if (this.pendingEvents < this.maxConcurrent) { this.pendingEvents++; return; }
    return new Promise((resolve) => {
      this.queue.push(() => { this.pendingEvents++; resolve(); });
    });
  }

  private releaseCapacity(): void {
    this.pendingEvents--;
    const next = this.queue.shift();
    if (next) next();
  }

  async trace(params: Parameters<typeof this.langfuse.trace>[0]) {
    await this.waitForCapacity();
    try { return this.langfuse.trace(params); }
    finally { this.releaseCapacity(); }
  }

  async flush(): Promise<void> { return this.langfuse.flushAsync(); }
  async shutdown(): Promise<void> { return this.langfuse.shutdownAsync(); }
}
```

## Sampling for High Volume

```typescript
class SampledLangfuse {
  private langfuse: Langfuse;
  private config: { rate: number; alwaysSample: (trace: any) => boolean };

  constructor(langfuseConfig: any, samplingConfig = { rate: 1.0, alwaysSample: () => false }) {
    this.langfuse = new Langfuse(langfuseConfig);
    this.config = samplingConfig;
  }

  trace(params: any) {
    if (this.config.alwaysSample(params)) return this.langfuse.trace(params);
    if (Math.random() > this.config.rate) return createNoOpTrace();
    return this.langfuse.trace({
      ...params,
      metadata: { ...params.metadata, sampled: true, sampleRate: this.config.rate },
    });
  }
}

// Usage: Sample 10% of traces, but always sample errors
const sampledLangfuse = new SampledLangfuse(
  { publicKey: "...", secretKey: "..." },
  { rate: 0.1, alwaysSample: (params) => params.tags?.includes("error") || params.level === "ERROR" }
);
```

## Rate Limit Monitor

```typescript
class RateLimitMonitor {
  private remaining: number = 1000;
  private resetAt: Date = new Date();

  updateFromResponse(headers: Headers) {
    const remaining = headers.get("X-RateLimit-Remaining");
    const reset = headers.get("X-RateLimit-Reset");
    if (remaining) this.remaining = parseInt(remaining);
    if (reset) this.resetAt = new Date(parseInt(reset) * 1000);
  }

  shouldThrottle(): boolean { return this.remaining < 10 && new Date() < this.resetAt; }
  getWaitTime(): number { return Math.max(0, this.resetAt.getTime() - Date.now()); }
  getStatus() { return { remaining: this.remaining, resetAt: this.resetAt.toISOString(), shouldThrottle: this.shouldThrottle() }; }
}
```

## Batch Processing Pattern

```typescript
async function processBatchWithRateLimits(items: any[]) {
  const BATCH_SIZE = 50;
  const DELAY_BETWEEN_BATCHES = 1000;

  for (let i = 0; i < items.length; i += BATCH_SIZE) {
    const batch = items.slice(i, i + BATCH_SIZE);
    batch.map((item) => langfuse.trace({ name: "batch-item", input: item }));
    await langfuse.flushAsync();
    if (i + BATCH_SIZE < items.length) {
      await new Promise((r) => setTimeout(r, DELAY_BETWEEN_BATCHES));
    }
  }
}
```

## Queue-Based Rate Limiting

```typescript
import PQueue from "p-queue";

const queue = new PQueue({ concurrency: 10, interval: 1000, intervalCap: 50 });

async function queuedTrace(params: TraceParams) {
  return queue.add(() => langfuse.trace(params));
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
