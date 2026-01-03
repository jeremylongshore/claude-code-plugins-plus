---
name: sentry-architecture-variants
description: |
  Sentry architecture patterns for different application types.
  Use when setting up Sentry for monoliths, microservices,
  serverless, or hybrid architectures.
  Trigger with phrases like "sentry monolith setup", "sentry microservices",
  "sentry serverless", "sentry architecture pattern".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Architecture Variants

## Overview
Architecture patterns for integrating Sentry with different application types.

## Monolith Architecture

### Single Project Setup
```
Organization: mycompany
└── Project: monolith-app
    └── Single DSN for entire application
```

### Configuration
```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.GIT_SHA,

  // Tag by module for filtering
  initialScope: {
    tags: {
      app_type: 'monolith',
    },
  },
});

// Tag errors by module
function tagByModule(moduleName: string) {
  return (error: Error) => {
    Sentry.withScope((scope) => {
      scope.setTag('module', moduleName);
      Sentry.captureException(error);
    });
  };
}

// Usage
const captureAuthError = tagByModule('auth');
const capturePaymentError = tagByModule('payments');
```

### Module-Based Filtering
```typescript
// Filter issues by module in dashboard
// Query: tags.module:auth
// Query: tags.module:payments
```

## Microservices Architecture

### Project Per Service
```
Organization: mycompany
├── Project: api-gateway
├── Project: user-service
├── Project: payment-service
├── Project: notification-service
└── Project: frontend-web
```

### Service Configuration
```typescript
// Shared config across services
// packages/sentry-config/index.ts
export function initServiceSentry(serviceName: string) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV,
    release: `${serviceName}@${process.env.GIT_SHA}`,
    serverName: serviceName,

    initialScope: {
      tags: {
        service: serviceName,
        cluster: process.env.K8S_CLUSTER,
        namespace: process.env.K8S_NAMESPACE,
      },
    },
  });
}

// user-service/src/index.ts
import { initServiceSentry } from '@mycompany/sentry-config';
initServiceSentry('user-service');
```

### Distributed Tracing
```typescript
// Propagate trace context between services
// Outgoing request
async function callService(url: string, data: any) {
  const transaction = Sentry.getCurrentHub().getScope()?.getTransaction();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (transaction) {
    headers['sentry-trace'] = transaction.toTraceparent();
    headers['baggage'] = Sentry.baggage.serializeBaggage(
      Sentry.baggage.getDynamicSamplingContextFromClient(
        transaction.traceId,
        Sentry.getCurrentHub().getClient()!
      )
    );
  }

  return fetch(url, { method: 'POST', headers, body: JSON.stringify(data) });
}

// Incoming request
app.use((req, res, next) => {
  const transaction = Sentry.continueTrace(
    { sentryTrace: req.headers['sentry-trace'], baggage: req.headers['baggage'] },
    (ctx) => Sentry.startTransaction({ ...ctx, name: `${req.method} ${req.path}`, op: 'http.server' })
  );
  Sentry.getCurrentHub().configureScope((scope) => scope.setSpan(transaction));
  res.on('finish', () => transaction.finish());
  next();
});
```

## Serverless Architecture

### AWS Lambda
```typescript
import * as Sentry from '@sentry/serverless';

Sentry.AWSLambda.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
});

export const handler = Sentry.AWSLambda.wrapHandler(
  async (event: APIGatewayEvent) => {
    // Your handler code
    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Success' }),
    };
  }
);
```

### Google Cloud Functions
```typescript
import * as Sentry from '@sentry/serverless';

Sentry.GCPFunction.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
});

export const httpFunction = Sentry.GCPFunction.wrapHttpFunction(
  async (req, res) => {
    res.send('Hello World');
  }
);
```

### Vercel Functions
```typescript
import * as Sentry from '@sentry/nextjs';

// next.config.js
const { withSentryConfig } = require('@sentry/nextjs');

module.exports = withSentryConfig({
  // Next.js config
}, {
  silent: true,
});

// API route
export default async function handler(req, res) {
  try {
    // Your code
    res.status(200).json({ success: true });
  } catch (error) {
    Sentry.captureException(error);
    res.status(500).json({ error: 'Internal error' });
  }
}
```

## Hybrid Architecture

### Mixed Monolith + Services
```
Organization: mycompany
├── Project: legacy-monolith     # Original application
├── Project: new-api-service     # Extracted microservice
├── Project: new-worker-service  # Background jobs
└── Project: frontend-spa        # Modern frontend
```

### Cross-System Tracing
```typescript
// Legacy monolith creates trace
const traceId = Sentry.getCurrentHub().getScope()?.getTransaction()?.traceId;

// Pass to new service via header or message queue
await callNewService('/api/process', {
  data: payload,
  metadata: {
    traceId,
    parentSpanId: currentSpanId,
  },
});

// New service continues trace
Sentry.startTransaction({
  name: 'process-data',
  traceId: metadata.traceId,
  parentSpanId: metadata.parentSpanId,
});
```

## Event-Driven Architecture

### Message Queue Integration
```typescript
// Producer (sends message)
async function publishMessage(queue: string, data: any) {
  const transaction = Sentry.getCurrentHub().getScope()?.getTransaction();

  const message = {
    data,
    metadata: {
      sentryTrace: transaction?.toTraceparent(),
      baggage: Sentry.baggage.serializeBaggage(/*...*/),
      timestamp: Date.now(),
    },
  };

  await messageQueue.publish(queue, message);
}

// Consumer (processes message)
async function processMessage(message: Message) {
  const { data, metadata } = message;

  const transaction = Sentry.continueTrace(
    { sentryTrace: metadata.sentryTrace, baggage: metadata.baggage },
    (ctx) => Sentry.startTransaction({
      ...ctx,
      name: 'process-message',
      op: 'queue.process',
    })
  );

  Sentry.getCurrentHub().configureScope((scope) => {
    scope.setSpan(transaction);
    scope.setTag('queue', message.queue);
  });

  try {
    await handleMessage(data);
    transaction.setStatus('ok');
  } catch (error) {
    transaction.setStatus('internal_error');
    Sentry.captureException(error);
    throw error;
  } finally {
    transaction.finish();
  }
}
```

## Multi-Tenant Architecture

### Tenant Isolation
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  beforeSend(event) {
    // Add tenant context
    const tenantId = getCurrentTenantId();
    if (tenantId) {
      event.tags = {
        ...event.tags,
        tenant_id: tenantId,
      };
      event.user = {
        ...event.user,
        tenant: tenantId,
      };
    }
    return event;
  },
});

// Filter by tenant in dashboard
// Query: tags.tenant_id:acme-corp
```

### Per-Tenant Projects (Enterprise)
```
Organization: mycompany
├── Project: platform-shared      # Platform errors
├── Project: tenant-acme         # ACME Corp errors
├── Project: tenant-globex       # Globex errors
└── Project: tenant-initech      # Initech errors
```

## Edge/CDN Architecture

### Edge Function Monitoring
```typescript
// Cloudflare Workers
import * as Sentry from '@sentry/cloudflare';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
});

export default {
  async fetch(request: Request, env: Env) {
    return Sentry.withScope(async (scope) => {
      scope.setTag('edge_location', request.cf?.colo);

      try {
        return await handleRequest(request, env);
      } catch (error) {
        Sentry.captureException(error);
        return new Response('Error', { status: 500 });
      }
    });
  },
};
```

## Architecture Decision Guide

| Architecture | Project Strategy | Tracing | Complexity |
|--------------|------------------|---------|------------|
| Monolith | Single project, tag by module | Simple | Low |
| Microservices | Project per service | Distributed | High |
| Serverless | Project per function group | Per-invocation | Medium |
| Hybrid | Mixed strategy | Cross-system | High |
| Event-Driven | Project per domain | Message-based | High |
| Multi-Tenant | Per-tenant or tags | Tenant-aware | Medium |

## Resources
- [Sentry Architecture Guide](https://docs.sentry.io/product/sentry-basics/integrate-backend/)
- [Distributed Tracing](https://docs.sentry.io/product/performance/distributed-tracing/)
