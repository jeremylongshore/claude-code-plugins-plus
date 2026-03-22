---
name: langfuse-rate-limits
description: |
  Implement Langfuse rate limiting, batching, and backoff patterns.
  Use when handling rate limit errors, optimizing trace ingestion,
  or managing high-volume LLM observability workloads.
  Trigger with phrases like "langfuse rate limit", "langfuse throttling",
  "langfuse 429", "langfuse batching", "langfuse high volume".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, observability, llm]

---
# Langfuse Rate Limits

## Overview
Handle Langfuse API rate limits with optimized SDK batching, exponential backoff with jitter, concurrent request limiting, and configurable sampling for ultra-high-volume workloads.

## Prerequisites
- Langfuse SDK installed and configured
- High-volume trace workload (1,000+ events/minute)

## Instructions

### Step 1: Optimize SDK Batching Configuration

The Langfuse SDK batches events internally before sending. Tuning batch settings is the first defense against rate limits.

```typescript
// v3 Legacy: Direct configuration
import { Langfuse } from "langfuse";

const langfuse = new Langfuse({
  flushAt: 50,           // Events per batch (default: 15, max ~200)
  flushInterval: 10000,  // Milliseconds between flushes (default: 10000)
  requestTimeout: 30000, // Timeout per batch request
});

// v4+: Configure via OTel span processor
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

const processor = new LangfuseSpanProcessor({
  exportIntervalMillis: 10000, // Flush interval
  maxExportBatchSize: 50,      // Events per batch
});

const sdk = new NodeSDK({ spanProcessors: [processor] });
sdk.start();
```

### Step 2: Implement Retry with Exponential Backoff

For custom API calls (scores, datasets, prompts) that hit rate limits:

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  options: { maxRetries?: number; baseDelayMs?: number; maxDelayMs?: number } = {}
): Promise<T> {
  const { maxRetries = 5, baseDelayMs = 1000, maxDelayMs = 30000 } = options;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      const status = error?.status || error?.response?.status;

      // Only retry on rate limits (429) and server errors (5xx)
      if (attempt === maxRetries || (status && status < 429)) {
        throw error;
      }

      // Honor Retry-After header if present
      const retryAfter = error?.response?.headers?.["retry-after"];
      let delay: number;

      if (retryAfter) {
        delay = parseInt(retryAfter, 10) * 1000;
      } else {
        // Exponential backoff with jitter
        delay = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);
        delay += Math.random() * 500; // Jitter
      }

      console.warn(`Rate limited. Retry ${attempt + 1}/${maxRetries} in ${Math.round(delay)}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage with Langfuse client operations
const langfuse = new LangfuseClient();

await withRetry(() =>
  langfuse.score.create({
    traceId: "trace-123",
    name: "quality",
    value: 0.95,
    dataType: "NUMERIC",
  })
);
```

### Step 3: Queue-Based Concurrency Limiting

Use `p-queue` to cap concurrent Langfuse API calls:

```typescript
import PQueue from "p-queue";
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

// Max 10 concurrent API calls, 50 per second
const queue = new PQueue({
  concurrency: 10,
  interval: 1000,
  intervalCap: 50,
});

// Queue score submissions
async function queueScore(params: {
  traceId: string;
  name: string;
  value: number;
}) {
  return queue.add(() =>
    langfuse.score.create({
      ...params,
      dataType: "NUMERIC",
    })
  );
}

// Queue dataset item creation
async function queueDatasetItem(datasetName: string, item: any) {
  return queue.add(() =>
    langfuse.api.datasetItems.create({
      datasetName,
      input: item.input,
      expectedOutput: item.expectedOutput,
    })
  );
}

// Monitor queue health
setInterval(() => {
  console.log(`Queue: ${queue.pending} pending, ${queue.size} queued`);
}, 10000);
```

### Step 4: Configurable Sampling for Ultra-High Volume

When tracing volume exceeds rate limits, sample traces instead of dropping them:

```typescript
import { observe, updateActiveObservation, startActiveObservation } from "@langfuse/tracing";

class TraceSampler {
  private rate: number;
  private windowCounts: number[] = [];
  private windowMs = 60000; // 1 minute window
  private maxPerWindow: number;

  constructor(sampleRate: number, maxPerMinute: number) {
    this.rate = sampleRate;
    this.maxPerWindow = maxPerMinute;
  }

  shouldSample(tags?: string[]): boolean {
    // Always sample errors
    if (tags?.includes("error") || tags?.includes("critical")) {
      return true;
    }

    // Check window limit
    const now = Date.now();
    this.windowCounts = this.windowCounts.filter((t) => t > now - this.windowMs);
    if (this.windowCounts.length >= this.maxPerWindow) {
      return false;
    }

    // Probabilistic sampling
    if (Math.random() > this.rate) {
      return false;
    }

    this.windowCounts.push(now);
    return true;
  }
}

// 10% sampling, max 1000 traces/minute
const sampler = new TraceSampler(0.1, 1000);

async function sampledOperation(name: string, fn: () => Promise<any>) {
  if (!sampler.shouldSample()) {
    return fn(); // Run without tracing
  }

  return startActiveObservation(name, async () => {
    updateActiveObservation({ metadata: { sampled: true } });
    return fn();
  });
}
```

## Rate Limit Reference

| Tier | Traces/min | Batch Size | Strategy |
|------|------------|------------|----------|
| Hobby | ~500 | 15 | Default settings |
| Pro | ~5,000 | 50 | Increase `flushAt` |
| Team | ~10,000 | 100 | + Queue-based limiting |
| Enterprise | Custom | Custom | + Sampling |

## Error Handling

| Error | Response | Action |
|-------|----------|--------|
| `429 Too Many Requests` | `Retry-After: N` | Backoff for N seconds |
| `503 Service Unavailable` | Server overloaded | Backoff 30s+ |
| Flush timeout | Large batch | Reduce `flushAt`, increase `requestTimeout` |
| Memory growth | Queue backup | Add `maxSize` to PQueue |

## Resources
- [Event Queuing/Batching](https://langfuse.com/docs/observability/features/queuing-batching)
- [Advanced SDK Configuration](https://langfuse.com/docs/observability/sdk/typescript/advanced-usage)
- [p-queue](https://github.com/sindresorhus/p-queue)
