---
name: langfuse-reference-architecture
description: |
  Production-grade Langfuse architecture patterns and best practices.
  Use when designing LLM observability infrastructure, planning Langfuse deployment,
  or implementing enterprise-grade tracing architecture.
  Trigger with phrases like "langfuse architecture", "langfuse design",
  "langfuse infrastructure", "langfuse enterprise", "langfuse at scale".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, deployment, observability, llm]

---
# Langfuse Reference Architecture

## Overview
Production-grade architecture patterns for Langfuse LLM observability: singleton SDK, context propagation with `AsyncLocalStorage`, cross-service trace correlation, multi-environment configurations, and scale strategies.

## Prerequisites
- Understanding of distributed systems and async patterns
- Node.js 18+ with OpenTelemetry SDK
- For v4+: `@langfuse/tracing`, `@langfuse/otel`, `@opentelemetry/sdk-node`

## Architecture Tiers

| Tier | Scale | Architecture | Langfuse Host |
|------|-------|-------------|---------------|
| Starter | < 100K traces/day | Direct SDK, Cloud | Langfuse Cloud |
| Growth | 100K-1M traces/day | Singleton + batching | Cloud or Self-hosted |
| Enterprise | 1M+ traces/day | Queue-buffered + sampling | Self-hosted (HA) |

## Instructions

### Pattern 1: Singleton SDK with Context Propagation

```typescript
// src/lib/tracing.ts -- Single module for all tracing
import { LangfuseClient } from "@langfuse/client";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { AsyncLocalStorage } from "async_hooks";

// Singleton OTel SDK
let sdk: NodeSDK | null = null;

export function initTracing() {
  if (sdk) return sdk;

  sdk = new NodeSDK({
    spanProcessors: [
      new LangfuseSpanProcessor({
        exportIntervalMillis: 5000,
        maxExportBatchSize: 50,
      }),
    ],
  });
  sdk.start();

  // Graceful shutdown
  for (const signal of ["SIGTERM", "SIGINT"]) {
    process.on(signal, async () => {
      console.log(`Received ${signal}, flushing traces...`);
      await sdk?.shutdown();
      process.exit(0);
    });
  }

  return sdk;
}

// Singleton client for non-tracing operations
let client: LangfuseClient | null = null;

export function getLangfuseClient(): LangfuseClient {
  if (!client) client = new LangfuseClient();
  return client;
}

// Request context for user/session tracking
interface RequestContext {
  userId?: string;
  sessionId?: string;
  requestId: string;
}

const requestStore = new AsyncLocalStorage<RequestContext>();

export function getRequestContext(): RequestContext | undefined {
  return requestStore.getStore();
}

export function runWithContext<T>(ctx: RequestContext, fn: () => T): T {
  return requestStore.run(ctx, fn);
}
```

### Pattern 2: Express Middleware for Automatic Tracing

```typescript
// src/middleware/tracing.ts
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";
import { runWithContext, getRequestContext } from "../lib/tracing";
import { randomUUID } from "crypto";
import type { Request, Response, NextFunction } from "express";

export function langfuseMiddleware() {
  return (req: Request, res: Response, next: NextFunction) => {
    const ctx = {
      requestId: req.headers["x-request-id"]?.toString() || randomUUID(),
      userId: req.headers["x-user-id"]?.toString(),
      sessionId: req.headers["x-session-id"]?.toString(),
    };

    runWithContext(ctx, () => {
      startActiveObservation(`${req.method} ${req.path}`, async () => {
        updateActiveObservation({
          input: {
            method: req.method,
            path: req.path,
            query: req.query,
          },
          metadata: {
            userId: ctx.userId,
            sessionId: ctx.sessionId,
            requestId: ctx.requestId,
          },
        });

        // Capture response
        const originalEnd = res.end.bind(res);
        res.end = function (...args: any[]) {
          updateActiveObservation({
            output: { statusCode: res.statusCode },
          });
          return originalEnd(...args);
        } as any;

        next();
      }).catch(next);
    });
  };
}

// Usage
import express from "express";
import { initTracing } from "./lib/tracing";
import { langfuseMiddleware } from "./middleware/tracing";

initTracing();
const app = express();
app.use(langfuseMiddleware());
```

### Pattern 3: Cross-Service Trace Correlation

For microservices, propagate trace context via HTTP headers:

```typescript
// Service A: Inject trace context into outbound requests
import { context, propagation } from "@opentelemetry/api";

async function callServiceB(data: any) {
  const headers: Record<string, string> = {};

  // OTel propagation injects traceparent header automatically
  propagation.inject(context.active(), headers);

  const response = await fetch("https://service-b.internal/api/process", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...headers, // Includes traceparent, tracestate
    },
    body: JSON.stringify(data),
  });

  return response.json();
}
```

```typescript
// Service B: Extract and continue trace context
import { context, propagation } from "@opentelemetry/api";
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";

app.post("/api/process", async (req, res) => {
  // OTel automatically extracts context from incoming headers
  // when using standard HTTP instrumentation.
  // Any startActiveObservation call will be a child of the extracted trace.

  await startActiveObservation("service-b-process", async () => {
    updateActiveObservation({ input: req.body });
    const result = await processData(req.body);
    updateActiveObservation({ output: result });
    res.json(result);
  });
});
```

### Pattern 4: Multi-Environment Configuration

```typescript
// src/config/langfuse.ts
type Environment = "development" | "staging" | "production";

const configs: Record<Environment, {
  exportIntervalMillis: number;
  maxExportBatchSize: number;
  sampleRate: number;
}> = {
  development: {
    exportIntervalMillis: 1000,   // Immediate visibility
    maxExportBatchSize: 1,
    sampleRate: 1.0,              // Trace everything
  },
  staging: {
    exportIntervalMillis: 5000,
    maxExportBatchSize: 25,
    sampleRate: 0.5,              // 50% sampling
  },
  production: {
    exportIntervalMillis: 10000,
    maxExportBatchSize: 100,
    sampleRate: 0.1,              // 10% sampling
  },
};

export function getTracingConfig() {
  const env = (process.env.NODE_ENV || "development") as Environment;
  return configs[env] || configs.development;
}
```

### Pattern 5: Graceful Degradation

When Langfuse is unavailable, the app must keep running:

```typescript
// The v4+ SDK with OTel handles this gracefully:
// - Failed exports are logged but don't throw
// - Events are buffered in the queue
// - Queue drops oldest events when maxQueueSize is exceeded
//
// For additional safety at the application level:

import { observe, updateActiveObservation } from "@langfuse/tracing";

let tracingHealthy = true;
let consecutiveFailures = 0;
const MAX_FAILURES = 10;

export function safeTrace<T extends (...args: any[]) => Promise<any>>(
  name: string,
  fn: T
): T {
  return (async (...args: Parameters<T>) => {
    if (!tracingHealthy) {
      return fn(...args); // Circuit breaker open
    }

    try {
      const result = await observe({ name }, async () => {
        updateActiveObservation({ input: args });
        const r = await fn(...args);
        updateActiveObservation({ output: r });
        return r;
      })();
      consecutiveFailures = 0;
      return result;
    } catch (error) {
      consecutiveFailures++;
      if (consecutiveFailures >= MAX_FAILURES) {
        tracingHealthy = false;
        console.error("Langfuse tracing disabled (circuit breaker open)");
        // Re-enable after 5 minutes
        setTimeout(() => { tracingHealthy = true; consecutiveFailures = 0; }, 300000);
      }
      return fn(...args);
    }
  }) as T;
}
```

## Architecture Decision Matrix

| Decision | Starter | Growth | Enterprise |
|----------|---------|--------|------------|
| Langfuse host | Cloud | Cloud or Self-hosted | Self-hosted (HA) |
| SDK version | v4+ | v4+ | v4+ with custom processor |
| Sampling | 100% | 50-100% | 5-20% + error always |
| Context propagation | Not needed | AsyncLocalStorage | OTel + HTTP headers |
| Queue buffer | SDK internal | SDK internal | External (SQS/Kafka) |
| Failover | None | Log-and-continue | Circuit breaker |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Multiple SDK instances | No singleton | Centralize in `tracing.ts` module |
| Lost traces on deploy | No SIGTERM handler | Register shutdown handler |
| Cross-service trace gaps | No context propagation | Inject OTel `traceparent` header |
| Scale bottleneck | Direct SDK at high volume | Add queue buffer or increase sampling |

## Resources
- [TypeScript SDK Overview](https://langfuse.com/docs/observability/sdk/typescript/overview)
- [Advanced Configuration](https://langfuse.com/docs/observability/sdk/typescript/advanced-usage)
- [Self-Hosting Guide](https://langfuse.com/self-hosting)
- [OpenTelemetry Context Propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
