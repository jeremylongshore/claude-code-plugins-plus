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
---
# Langfuse Performance Tuning

## Overview
Optimize Langfuse tracing for minimal overhead and maximum throughput.

## Prerequisites
- Existing Langfuse integration
- Performance baseline measurements
- Understanding of async patterns

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Trace creation overhead | < 1ms | < 5ms |
| Flush latency | < 100ms | < 500ms |
| Memory per trace | < 1KB | < 5KB |
| CPU overhead | < 1% | < 5% |

## Instructions

### Step 1: Measure Baseline Performance

```typescript
// scripts/benchmark-langfuse.ts
import { Langfuse } from "langfuse";
import { performance } from "perf_hooks";

async function benchmark() {
  const langfuse = new Langfuse();
  const iterations = 1000;  # 1000: 1 second in ms

  // Measure trace creation
  const traceTimings: number[] = [];
  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    const trace = langfuse.trace({ name: `benchmark-${i}` });
    traceTimings.push(performance.now() - start);
  }

  // Measure generation creation
  const genTimings: number[] = [];
  const trace = langfuse.trace({ name: "gen-benchmark" });
  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    const gen = trace.generation({
      name: `gen-${i}`,
      model: "gpt-4",
      input: [{ role: "user", content: "test" }],
    });
    gen.end({ output: "response" });
    genTimings.push(performance.now() - start);
  }

  // Measure flush
  const flushStart = performance.now();
  await langfuse.flushAsync();
  const flushTime = performance.now() - flushStart;

  // Calculate stats
  const stats = (arr: number[]) => ({
    mean: arr.reduce((a, b) => a + b) / arr.length,
    p50: arr.sort((a, b) => a - b)[Math.floor(arr.length * 0.5)],
    p95: arr.sort((a, b) => a - b)[Math.floor(arr.length * 0.95)],
    p99: arr.sort((a, b) => a - b)[Math.floor(arr.length * 0.99)],
  });

  console.log("=== Langfuse Performance Benchmark ===");
  console.log(`\nTrace Creation (${iterations} iterations):`);
  console.log(JSON.stringify(stats(traceTimings), null, 2));
  console.log(`\nGeneration Creation (${iterations} iterations):`);
  console.log(JSON.stringify(stats(genTimings), null, 2));
  console.log(`\nFlush Time: ${flushTime.toFixed(2)}ms`);

  await langfuse.shutdownAsync();
}

benchmark();
```

### Step 2: Optimize Batching Configuration

```typescript
// High-throughput configuration
const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,

  // Batching optimization
  flushAt: 100,           // Larger batches = fewer requests
  flushInterval: 10000,   // Less frequent flushes  # 10000: 10 seconds in ms

  // Timeout tuning
  requestTimeout: 30000,  // Allow time for large batches  # 30000: 30 seconds in ms

  // Optional: Disable in development
  enabled: process.env.NODE_ENV === "production",
});
```

### Step 3: Implement Non-Blocking Tracing

```typescript
// Trace wrapper that never blocks the main operation
class NonBlockingLangfuse {
  private langfuse: Langfuse;
  private errorCount = 0;
  private maxErrors = 10;

  constructor(config: ConstructorParameters<typeof Langfuse>[0]) {
    this.langfuse = new Langfuse(config);
  }

  // Fire-and-forget trace
  trace(params: Parameters<typeof this.langfuse.trace>[0]) {
    if (this.errorCount >= this.maxErrors) {
      // Circuit breaker: stop tracing if too many errors
      return this.createNoOpTrace();
    }

    try {
      return this.langfuse.trace(params);
    } catch (error) {
      this.errorCount++;
      console.error("Langfuse trace error:", error);
      return this.createNoOpTrace();
    }
  }

  private createNoOpTrace() {
    return {
      id: "noop",
      span: () => this.createNoOpSpan(),
      generation: () => this.createNoOpGeneration(),
      update: () => {},
      getTraceUrl: () => "",
    };
  }

  private createNoOpSpan() {
    return {
      id: "noop",
      span: () => this.createNoOpSpan(),
      generation: () => this.createNoOpGeneration(),
      end: () => {},
    };
  }

  private createNoOpGeneration() {
    return {
      id: "noop",
      end: () => {},
    };
  }

  // Background flush - don't await in hot path
  flush() {
    this.langfuse.flushAsync().catch((error) => {
      this.errorCount++;
      console.error("Langfuse flush error:", error);
    });
  }

  async shutdown() {
    return this.langfuse.shutdownAsync();
  }
}
```

### Step 4: Optimize Data Payload Size

```typescript
// Reduce trace payload size
function optimizeTraceInput(input: any): any {
  // Truncate large strings
  const MAX_STRING_LENGTH = 10000;  # 10000: 10 seconds in ms

  if (typeof input === "string") {
    return input.length > MAX_STRING_LENGTH
      ? input.slice(0, MAX_STRING_LENGTH) + "...[truncated]"
      : input;
  }

  if (Array.isArray(input)) {
    // Limit array size
    const MAX_ARRAY_LENGTH = 100;
    const truncated = input.slice(0, MAX_ARRAY_LENGTH);
    return truncated.map(optimizeTraceInput);
  }

  if (typeof input === "object" && input !== null) {
    // Remove large binary data
    const optimized: Record<string, any> = {};
    for (const [key, value] of Object.entries(input)) {
      if (value instanceof Buffer || value instanceof Uint8Array) {
        optimized[key] = `[Binary: ${value.length} bytes]`;
      } else {
        optimized[key] = optimizeTraceInput(value);
      }
    }
    return optimized;
  }

  return input;
}

// Use in traces
const trace = langfuse.trace({
  name: "optimized-trace",
  input: optimizeTraceInput(largeInput),
});
```

### Step 5: Implement Sampling for Ultra-High Volume

```typescript
interface SamplingStrategy {
  shouldSample(params: TraceParams): boolean;
}

// Deterministic sampling based on trace attributes
class DeterministicSampler implements SamplingStrategy {
  private rate: number;

  constructor(rate: number) {
    this.rate = rate;
  }

  shouldSample(params: TraceParams): boolean {
    // Always sample errors
    if (params.level === "ERROR" || params.tags?.includes("error")) {
      return true;
    }

    // Deterministic hash-based sampling
    const hash = this.hashString(params.name + (params.userId || ""));
    return (hash % 100) < (this.rate * 100);
  }

  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash);
  }
}

// Adaptive sampling based on throughput
class AdaptiveSampler implements SamplingStrategy {
  private windowMs = 60000;  # 60000: 1 minute in ms
  private maxPerWindow = 1000;  # 1000: 1 second in ms
  private counts: number[] = [];

  shouldSample(params: TraceParams): boolean {
    const now = Date.now();
    const windowStart = now - this.windowMs;

    // Clean old counts
    this.counts = this.counts.filter((t) => t > windowStart);

    // Check if under limit
    if (this.counts.length < this.maxPerWindow) {
      this.counts.push(now);
      return true;
    }

    // Over limit - only sample important traces
    return params.level === "ERROR";
  }
}

// Apply sampling
const sampler = new DeterministicSampler(0.1); // 10% sampling

function sampledTrace(params: TraceParams) {
  if (!sampler.shouldSample(params)) {
    return createNoOpTrace();
  }

  return langfuse.trace({
    ...params,
    metadata: {
      ...params.metadata,
      sampled: true,
    },
  });
}
```

### Step 6: Memory Management

```typescript
// Prevent memory leaks with trace cleanup
class ManagedLangfuse {
  private langfuse: Langfuse;
  private activeTraces: Map<string, { createdAt: Date }> = new Map();
  private maxTraceAge = 300000; // 5 minutes  # 300000 = configured value

  constructor(config: ConstructorParameters<typeof Langfuse>[0]) {
    this.langfuse = new Langfuse(config);

    // Periodic cleanup
    setInterval(() => this.cleanupStaleTraces(), 60000);  # 60000: 1 minute in ms
  }

  trace(params: Parameters<typeof this.langfuse.trace>[0]) {
    const trace = this.langfuse.trace(params);
    this.activeTraces.set(trace.id, { createdAt: new Date() });
    return trace;
  }

  private cleanupStaleTraces() {
    const now = Date.now();
    let cleaned = 0;

    for (const [id, meta] of this.activeTraces) {
      if (now - meta.createdAt.getTime() > this.maxTraceAge) {
        this.activeTraces.delete(id);
        cleaned++;
      }
    }

    if (cleaned > 0) {
      console.log(`Cleaned up ${cleaned} stale trace references`);
    }
  }

  getStats() {
    return {
      activeTraces: this.activeTraces.size,
      heapUsed: process.memoryUsage().heapUsed / 1024 / 1024,  # 1024: 1 KB
    };
  }
}
```

## Output
- Baseline performance measurements
- Optimized batching configuration
- Non-blocking trace wrapper
- Payload size optimization
- Sampling strategies for high volume
- Memory leak prevention

## Performance Optimization Checklist

| Optimization | Impact | Effort |
|--------------|--------|--------|
| Increase `flushAt` | High | Low |
| Non-blocking traces | High | Medium |
| Payload truncation | Medium | Low |
| Sampling | High | Medium |
| Memory management | Medium | Medium |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High latency | Small batch size | Increase `flushAt` |
| Memory growth | No cleanup | Add trace cleanup |
| Request timeouts | Large payloads | Truncate inputs |
| High CPU | Sync operations | Use async patterns |

## Resources
- [Langfuse SDK Configuration](https://langfuse.com/docs/sdk)
- [Node.js Performance](https://nodejs.org/en/docs/guides/dont-block-the-event-loop)
- [Sampling Strategies](https://opentelemetry.io/docs/concepts/sampling/)

## Next Steps
For cost optimization, see `langfuse-cost-tuning`.

## Examples

**Basic usage**: Apply langfuse performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize langfuse performance tuning for production environments with multiple constraints and team-specific requirements.