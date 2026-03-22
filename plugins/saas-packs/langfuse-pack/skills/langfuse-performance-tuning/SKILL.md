---
name: langfuse-performance-tuning
description: |
  Optimize Langfuse tracing performance for high-throughput applications.
  Use when experiencing latency issues, optimizing trace overhead,
  or scaling Langfuse for production workloads.
  Trigger with phrases like "langfuse performance", "optimize langfuse",
  "langfuse latency", "langfuse overhead", "langfuse slow".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, performance, scaling, tracing]

---
# Langfuse Performance Tuning

## Overview
Optimize Langfuse tracing for minimal overhead and maximum throughput: benchmark measurement, batch tuning, non-blocking patterns, payload optimization, sampling, and memory management.

## Prerequisites
- Existing Langfuse integration
- Performance baseline to compare against
- Understanding of async patterns

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Trace creation overhead | < 1ms | < 5ms |
| Flush latency (batch) | < 100ms | < 500ms |
| Memory per active trace | < 1KB | < 5KB |
| CPU overhead | < 1% | < 5% |

## Instructions

### Step 1: Benchmark Current Performance

```typescript
// scripts/benchmark-langfuse.ts
import { performance } from "perf_hooks";
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

async function benchmark() {
  const sdk = new NodeSDK({
    spanProcessors: [new LangfuseSpanProcessor()],
  });
  sdk.start();

  const iterations = 1000;

  // Measure trace creation
  const timings: number[] = [];
  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await startActiveObservation(`bench-${i}`, async () => {
      updateActiveObservation({ input: { i }, output: { done: true } });
    });
    timings.push(performance.now() - start);
  }

  const sorted = timings.sort((a, b) => a - b);
  console.log("=== Langfuse Performance Benchmark ===");
  console.log(`Iterations: ${iterations}`);
  console.log(`Mean:  ${(sorted.reduce((a, b) => a + b) / sorted.length).toFixed(3)}ms`);
  console.log(`P50:   ${sorted[Math.floor(sorted.length * 0.5)].toFixed(3)}ms`);
  console.log(`P95:   ${sorted[Math.floor(sorted.length * 0.95)].toFixed(3)}ms`);
  console.log(`P99:   ${sorted[Math.floor(sorted.length * 0.99)].toFixed(3)}ms`);

  const flushStart = performance.now();
  await sdk.shutdown();
  console.log(`Flush: ${(performance.now() - flushStart).toFixed(1)}ms`);
}

benchmark();
```

### Step 2: Optimize Batch Configuration

```typescript
// v4+: Tune OTel span processor
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

const processor = new LangfuseSpanProcessor({
  exportIntervalMillis: 10000,  // Flush every 10s (default: 5000)
  maxExportBatchSize: 100,      // Larger batches = fewer API calls
  maxQueueSize: 4096,           // Buffer more events before dropping
});

const sdk = new NodeSDK({ spanProcessors: [processor] });
sdk.start();
```

```typescript
// v3: Direct configuration
const langfuse = new Langfuse({
  flushAt: 100,           // Larger batches
  flushInterval: 10000,   // Less frequent flushes
  requestTimeout: 30000,  // Allow time for large batches
});
```

| Setting | Low Volume | High Volume | Ultra-High |
|---------|-----------|-------------|------------|
| Batch size | 15 | 50-100 | 200 |
| Flush interval | 5s | 10s | 30s |
| Queue size | 1024 | 4096 | 8192 |

### Step 3: Non-Blocking Trace Wrapper

Ensure tracing never blocks your application's critical path:

```typescript
import { observe, updateActiveObservation } from "@langfuse/tracing";

// The observe wrapper is already non-blocking for the trace submission.
// But protect against SDK crashes:
function safeObserve<T extends (...args: any[]) => Promise<any>>(
  name: string,
  fn: T
): T {
  return (async (...args: Parameters<T>) => {
    try {
      return await observe({ name }, async () => {
        updateActiveObservation({ input: args });
        const result = await fn(...args);
        updateActiveObservation({ output: result });
        return result;
      })();
    } catch (error) {
      // If tracing throws, run function without tracing
      console.warn(`Tracing failed for ${name}:`, error);
      return fn(...args);
    }
  }) as T;
}
```

### Step 4: Payload Size Optimization

Large trace payloads slow down flush and increase costs:

```typescript
function truncateForTrace(input: any, maxStringLen = 5000, maxArrayLen = 50): any {
  if (typeof input === "string") {
    return input.length > maxStringLen
      ? input.slice(0, maxStringLen) + `...[truncated ${input.length - maxStringLen} chars]`
      : input;
  }

  if (Array.isArray(input)) {
    return input.slice(0, maxArrayLen).map((item) => truncateForTrace(item));
  }

  if (input instanceof Buffer || input instanceof Uint8Array) {
    return `[Binary: ${input.length} bytes]`;
  }

  if (typeof input === "object" && input !== null) {
    const result: Record<string, any> = {};
    for (const [key, value] of Object.entries(input)) {
      result[key] = truncateForTrace(value);
    }
    return result;
  }

  return input;
}

// Usage
await startActiveObservation("process", async () => {
  updateActiveObservation({
    input: truncateForTrace(largeInput),  // Truncated for trace
  });
  const result = await process(largeInput); // Full input to function
  updateActiveObservation({ output: truncateForTrace(result) });
});
```

### Step 5: Sampling for Ultra-High Volume

When you cannot afford to trace every request:

```typescript
class TraceSampler {
  private rate: number;
  private windowMs = 60000;
  private maxPerWindow: number;
  private timestamps: number[] = [];

  constructor(rate: number, maxPerMinute: number) {
    this.rate = rate;
    this.maxPerWindow = maxPerMinute;
  }

  shouldSample(isError = false): boolean {
    if (isError) return true; // Always trace errors

    const now = Date.now();
    this.timestamps = this.timestamps.filter((t) => t > now - this.windowMs);

    if (this.timestamps.length >= this.maxPerWindow) return false;
    if (Math.random() > this.rate) return false;

    this.timestamps.push(now);
    return true;
  }
}

const sampler = new TraceSampler(0.1, 1000); // 10%, max 1000/min

async function maybeTrace<T>(name: string, fn: () => Promise<T>, isError = false): Promise<T> {
  if (!sampler.shouldSample(isError)) {
    return fn(); // Skip tracing
  }

  return startActiveObservation(name, async () => {
    updateActiveObservation({ metadata: { sampled: true } });
    return fn();
  });
}
```

### Step 6: Memory Management

```typescript
// Monitor trace-related memory usage
function logMemoryStats() {
  const mem = process.memoryUsage();
  console.log({
    heapUsedMB: (mem.heapUsed / 1024 / 1024).toFixed(1),
    rssMB: (mem.rss / 1024 / 1024).toFixed(1),
    externalMB: (mem.external / 1024 / 1024).toFixed(1),
  });
}

// Log every minute in production
setInterval(logMemoryStats, 60000);
```

## Optimization Impact Matrix

| Optimization | Latency Impact | Throughput Impact | Effort |
|-------------|---------------|-------------------|--------|
| Increase batch size | High | High | Low |
| Non-blocking wrapper | High | Medium | Low |
| Payload truncation | Medium | Medium | Low |
| Sampling | High | Very High | Medium |
| Memory monitoring | Low | Low | Low |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High P99 latency | Sync flush in hot path | Use non-blocking wrapper |
| Memory growth | No payload limits | Truncate inputs/outputs |
| Request timeouts | Batch too large | Reduce batch size or increase timeout |
| Dropped spans | Queue full | Increase `maxQueueSize` |

## Resources
- [Event Queuing/Batching](https://langfuse.com/docs/observability/features/queuing-batching)
- [Advanced SDK Configuration](https://langfuse.com/docs/observability/sdk/typescript/advanced-usage)
- [Token & Cost Tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking)
