---
name: sentry-architecture-variants
description: |
  Sentry architecture patterns for different application types.
  Use when setting up Sentry for monoliths, microservices,
  serverless, or hybrid architectures.
  Trigger with phrases like "sentry monolith setup", "sentry microservices",
  "sentry serverless", "sentry architecture pattern".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, serverless, microservices, architecture]

---
# Sentry Architecture Variants

## Prerequisites
- Application architecture documented
- Service inventory available
- Team ownership and deployment model defined
- Tracing requirements understood

## Instructions

### 1. Monolith Architecture

Single application, single Sentry project:

```typescript
// instrument.mjs — monolith setup
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.APP_VERSION,
  tracesSampleRate: 0.1,

  // Use tags to separate modules within the monolith
  initialScope: {
    tags: { app: 'monolith' },
  },
});

// Tag errors by module
function captureModuleError(module: string, error: Error) {
  Sentry.withScope((scope) => {
    scope.setTag('module', module);
    scope.setTag('team', getTeamForModule(module));
    Sentry.captureException(error);
  });
}

// Usage
captureModuleError('auth', new Error('Token expired'));
captureModuleError('billing', new Error('Payment failed'));

// Ownership rules in Sentry dashboard:
// tags.module:auth -> #platform-team
// tags.module:billing -> #payments-team
```

### 2. Microservices Architecture

One Sentry project per service with distributed tracing:

```typescript
// packages/sentry-config/index.ts — shared across all services
import * as Sentry from '@sentry/node';

export function initServiceSentry(serviceName: string) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV,
    release: `${serviceName}@${process.env.APP_VERSION}`,
    serverName: serviceName,
    tracesSampleRate: 0.1,
    sendDefaultPii: false,

    initialScope: {
      tags: {
        service: serviceName,
        cluster: process.env.K8S_CLUSTER || 'default',
        namespace: process.env.K8S_NAMESPACE || 'default',
      },
    },
  });
}

// Each service initializes with its own name:
// api-gateway/instrument.mjs:    initServiceSentry('api-gateway');
// user-service/instrument.mjs:   initServiceSentry('user-service');
// payment-service/instrument.mjs: initServiceSentry('payment-service');
```

**Distributed tracing across services:**
```typescript
// HTTP calls between services automatically propagate trace context
// via sentry-trace and baggage headers (SDK v8 auto-handles this)

// For non-HTTP communication (message queues, gRPC):
import * as Sentry from '@sentry/node';

// Producer service
async function publishEvent(topic: string, payload: object) {
  const span = Sentry.getActiveSpan();
  const headers: Record<string, string> = {};

  if (span) {
    headers['sentry-trace'] = Sentry.spanToTraceHeader(span);
    headers['baggage'] = Sentry.spanToBaggageHeader(span) || '';
  }

  await kafka.send({ topic, messages: [{ value: JSON.stringify(payload), headers }] });
}

// Consumer service
async function handleMessage(message: KafkaMessage) {
  const headers = message.headers || {};

  Sentry.continueTrace(
    {
      sentryTrace: headers['sentry-trace']?.toString(),
      baggage: headers['baggage']?.toString(),
    },
    () => {
      Sentry.startSpan(
        { name: `consume.${message.topic}`, op: 'queue.process' },
        () => processMessage(message)
      );
    }
  );
}
```

### 3. Serverless Architecture (AWS Lambda)

```typescript
// handler.ts — AWS Lambda with Sentry
import * as Sentry from '@sentry/aws-serverless';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.STAGE,
  tracesSampleRate: 0.1,
});

// Wrap handler with Sentry
export const handler = Sentry.wrapHandler(async (event, context) => {
  Sentry.setTag('function', context.functionName);
  Sentry.setTag('region', process.env.AWS_REGION);

  try {
    const result = await processRequest(event);
    return { statusCode: 200, body: JSON.stringify(result) };
  } catch (error) {
    Sentry.captureException(error);
    return { statusCode: 500, body: 'Internal Server Error' };
  }
});
```

**Google Cloud Functions:**
```typescript
import * as Sentry from '@sentry/google-cloud-serverless';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
});

export const myFunction = Sentry.wrapCloudEventFunction(async (event, context) => {
  // Function logic
});
```

### 4. Next.js / Full-Stack Framework

```typescript
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  integrations: [
    Sentry.replayIntegration(),
    Sentry.browserTracingIntegration(),
  ],
});

// sentry.server.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
});

// sentry.edge.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
});
```

### 5. Multi-Tenant SaaS

```typescript
// Isolate tenant data in Sentry
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,

  beforeSend(event) {
    // Tag every event with tenant for filtering
    // But NEVER include tenant-specific PII
    return event;
  },
});

// Middleware: set tenant context per request
app.use((req, res, next) => {
  const tenantId = req.headers['x-tenant-id'] || 'unknown';

  Sentry.setTag('tenant_id', tenantId);
  Sentry.setTag('tenant_plan', getTenantPlan(tenantId));

  // Set user as tenant, not individual
  Sentry.setUser({ id: `tenant:${tenantId}` });

  next();
});

// Filter by tenant in Sentry dashboard:
// Issues > Search: tags.tenant_id:acme-corp
```

### 6. Worker / Queue Architecture

```typescript
// Background job processor with Sentry
import * as Sentry from '@sentry/node';

class JobProcessor {
  async processJob(job: Job) {
    return Sentry.withScope(async (scope) => {
      scope.setTag('job.type', job.type);
      scope.setTag('job.queue', job.queue);
      scope.setTag('job.attempt', String(job.attempts));
      scope.setContext('job', {
        id: job.id,
        data: sanitizeJobData(job.data),
        scheduled_at: job.scheduledAt,
      });

      try {
        const result = await Sentry.startSpan(
          { name: `job.${job.type}`, op: 'queue.task' },
          () => this.execute(job)
        );
        return result;
      } catch (error) {
        scope.setLevel(job.attempts >= job.maxAttempts ? 'error' : 'warning');
        Sentry.captureException(error);
        throw error;
      }
    });
  }
}

// Periodic flush for long-running workers
setInterval(() => Sentry.flush(2000), 30_000);
```

### 7. Hybrid Architecture Decision Matrix

| Architecture | Projects | Tracing | Key Pattern |
|-------------|----------|---------|-------------|
| Monolith | 1 project | Single-service spans | Module tags + ownership rules |
| Microservices | 1 per service | Distributed tracing | Shared config package + trace headers |
| Serverless | 1 per function group | Per-invocation spans | Wrapper function + cold start tracking |
| Next.js | 1 project, 3 configs | Client + server + edge | Framework SDK with 3 config files |
| Multi-tenant | 1 project | Per-tenant tagging | Tenant ID tags, no tenant PII |
| Workers | 1 per worker type | Per-job spans | withScope per job, periodic flush |

## Output
- Architecture-appropriate Sentry configuration for each pattern
- Distributed tracing configured across services (HTTP and message queue)
- Serverless wrappers for AWS Lambda and Google Cloud Functions
- Multi-tenant isolation using tags and scope
- Worker pattern with per-job context and periodic flush

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Distributed traces broken | Missing header propagation | Verify `sentry-trace` and `baggage` headers in all inter-service calls |
| Lambda cold starts missing events | SDK not flushed before return | Use `Sentry.wrapHandler()` which auto-flushes |
| Multi-tenant data leakage | Global scope pollution | Use `withScope()` per request, never `setTag()` globally |
| Worker events lost | No periodic flush | Add `setInterval(() => Sentry.flush(2000), 30000)` |

## Resources
- [Node.js Guide](https://docs.sentry.io/platforms/javascript/guides/node/)
- [Express Guide](https://docs.sentry.io/platforms/javascript/guides/express/)
- [Next.js Guide](https://docs.sentry.io/platforms/javascript/guides/nextjs/)
- [AWS Lambda](https://docs.sentry.io/platforms/javascript/guides/aws-lambda/)
- [Google Cloud Functions](https://docs.sentry.io/platforms/javascript/guides/gcp-functions/)
- [Distributed Tracing](https://docs.sentry.io/product/performance/distributed-tracing/)
