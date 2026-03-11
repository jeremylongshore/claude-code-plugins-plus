# Langfuse Reference Architecture - Implementation Details

## Singleton SDK Pattern

```typescript
import { Langfuse } from "langfuse";

class LangfuseClient {
  private static instance: Langfuse | null = null;

  static getInstance(): Langfuse {
    if (!LangfuseClient.instance) {
      LangfuseClient.instance = new Langfuse({
        publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
        secretKey: process.env.LANGFUSE_SECRET_KEY!,
        baseUrl: process.env.LANGFUSE_HOST,
        flushAt: parseInt(process.env.LANGFUSE_FLUSH_AT || "25"),
        flushInterval: parseInt(process.env.LANGFUSE_FLUSH_INTERVAL || "5000"),
        requestTimeout: 15000,
      });
      LangfuseClient.registerShutdown();
    }
    return LangfuseClient.instance;
  }

  private static registerShutdown() {
    const shutdown = async (signal: string) => {
      if (LangfuseClient.instance) {
        await LangfuseClient.instance.shutdownAsync();
        LangfuseClient.instance = null;
      }
    };
    process.on("SIGTERM", () => shutdown("SIGTERM"));
    process.on("SIGINT", () => shutdown("SIGINT"));
  }
}

export const langfuse = LangfuseClient.getInstance();
```

## Trace Context Propagation

```typescript
import { AsyncLocalStorage } from "async_hooks";

interface TraceContext {
  traceId: string;
  parentSpanId?: string;
  userId?: string;
  sessionId?: string;
}

const traceStorage = new AsyncLocalStorage<TraceContext>();

export function withTraceContext<T>(context: TraceContext, fn: () => T): T {
  return traceStorage.run(context, fn);
}

export function getTraceContext(): TraceContext | undefined {
  return traceStorage.getStore();
}

// Express middleware
export function langfuseMiddleware() {
  return (req, res, next) => {
    const trace = langfuse.trace({
      name: `${req.method} ${req.path}`,
      userId: req.user?.id,
      sessionId: req.session?.id,
    });

    const context = { traceId: trace.id, userId: req.user?.id, sessionId: req.session?.id };
    withTraceContext(context, () => {
      req.langfuseTrace = trace;
      res.on("finish", () => {
        trace.update({ output: { statusCode: res.statusCode }, level: res.statusCode >= 400 ? "ERROR" : undefined });
      });
      next();
    });
  };
}
```

## Queue-Based Ingestion

```typescript
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";

// Producer
class QueuedLangfuseProducer {
  private sqs = new SQSClient({});
  private queueUrl = process.env.LANGFUSE_QUEUE_URL!;

  async trace(params) {
    await this.sqs.send(new SendMessageCommand({
      QueueUrl: this.queueUrl,
      MessageBody: JSON.stringify({ ...params, timestamp: new Date().toISOString() }),
    }));
  }
}

// Consumer
class QueuedLangfuseConsumer {
  private langfuse = new Langfuse();

  async processBatch(messages) {
    for (const message of messages) {
      this.langfuse.trace({ ...message, timestamp: new Date(message.timestamp) });
    }
    await this.langfuse.flushAsync();
  }
}
```

## Multi-Environment Configuration

```typescript
type Environment = "development" | "staging" | "production";

const ENVIRONMENT_CONFIGS: Record<Environment, LangfuseEnvironmentConfig> = {
  development: {
    flushAt: 1,
    flushInterval: 1000,
    sampling: { rate: 1.0, alwaysSampleErrors: true },
  },
  staging: {
    flushAt: 15,
    flushInterval: 5000,
    sampling: { rate: 0.5, alwaysSampleErrors: true },
  },
  production: {
    flushAt: 25,
    flushInterval: 5000,
    sampling: { rate: 0.1, alwaysSampleErrors: true },
  },
};
```

## Service Mesh Tracing

```typescript
// Inject trace headers on outgoing requests
function injectTraceHeaders(headers: Headers) {
  const context = getTraceContext();
  if (context) {
    headers.set("x-langfuse-trace-id", context.traceId);
    if (context.parentSpanId) headers.set("x-langfuse-parent-id", context.parentSpanId);
    if (context.sessionId) headers.set("x-langfuse-session-id", context.sessionId);
  }
}

// Extract trace context from incoming requests
function extractTraceContext(request: Request): TraceContext | null {
  const traceId = request.headers.get("x-langfuse-trace-id");
  if (!traceId) return null;
  return { traceId, parentSpanId: request.headers.get("x-langfuse-parent-id") || undefined };
}
```

## Architecture Diagrams

### Basic Cloud Architecture
```
Application Layer (API, Workers, Cron)
  → Langfuse SDK (Singleton)
  → Langfuse Cloud (Ingestion → Processing → PostgreSQL → Dashboard)
```

### High-Scale with Buffer
```
Regional Application Clusters
  → Langfuse SDK (Batched)
  → Message Queue (SQS/Kafka)
  → Ingestion Workers
  → Langfuse (Cloud/Self-Hosted)
```
