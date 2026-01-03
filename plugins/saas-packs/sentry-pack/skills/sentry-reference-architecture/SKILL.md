---
name: sentry-reference-architecture
description: |
  Best-practice Sentry architecture patterns.
  Use when designing Sentry integration architecture,
  structuring projects, or planning enterprise rollout.
  Trigger with phrases like "sentry architecture", "sentry best practices",
  "design sentry integration", "sentry project structure".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Reference Architecture

## Overview
Best-practice patterns for Sentry integration at scale.

## Project Structure

### Single Application
```
Organization: mycompany
└── Project: myapp-production
    └── DSN for all services
```

### Microservices
```
Organization: mycompany
├── Project: api-gateway
├── Project: user-service
├── Project: payment-service
├── Project: notification-service
└── Project: frontend-web
```

### Multi-Environment
```
Organization: mycompany
├── Team: backend
│   ├── Project: api-production
│   ├── Project: api-staging
│   └── Project: api-development
└── Team: frontend
    ├── Project: web-production
    └── Project: web-staging
```

## Configuration Patterns

### Centralized Config Module
```typescript
// lib/sentry.ts
import * as Sentry from '@sentry/node';

interface SentryConfig {
  serviceName: string;
  environment: string;
  release?: string;
}

export function initSentry(config: SentryConfig): void {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: config.environment,
    release: config.release || process.env.SENTRY_RELEASE,
    serverName: config.serviceName,

    // Standard settings
    tracesSampleRate: config.environment === 'production' ? 0.1 : 1.0,
    sendDefaultPii: false,
    attachStacktrace: true,

    // Standard integrations
    integrations: [
      new Sentry.Integrations.Http({ tracing: true }),
    ],

    // Standard filtering
    ignoreErrors: [
      'ResizeObserver loop',
      'Network request failed',
    ],

    // Standard tags
    initialScope: {
      tags: {
        service: config.serviceName,
      },
    },
  });
}

export { Sentry };
```

### Usage Across Services
```typescript
// user-service/src/index.ts
import { initSentry, Sentry } from '@mycompany/shared/sentry';

initSentry({
  serviceName: 'user-service',
  environment: process.env.NODE_ENV,
  release: process.env.GIT_SHA,
});
```

## Error Handling Architecture

### Global Error Handler
```typescript
// middleware/errorHandler.ts
import { Sentry } from '@mycompany/shared/sentry';

export function errorHandler(
  error: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Capture in Sentry
  Sentry.withScope((scope) => {
    scope.setTag('endpoint', req.path);
    scope.setTag('method', req.method);
    scope.setUser({ ip_address: req.ip });
    scope.setExtra('query', req.query);
    Sentry.captureException(error);
  });

  // Respond to client
  res.status(500).json({
    error: 'Internal server error',
    requestId: res.sentry, // Sentry event ID
  });
}
```

### Domain-Specific Handlers
```typescript
// errors/PaymentError.ts
export class PaymentError extends Error {
  constructor(
    message: string,
    public code: string,
    public provider: string,
    public transactionId?: string
  ) {
    super(message);
    this.name = 'PaymentError';
  }
}

// When caught
if (error instanceof PaymentError) {
  Sentry.withScope((scope) => {
    scope.setTag('error_type', 'payment');
    scope.setTag('payment_provider', error.provider);
    scope.setExtra('transaction_id', error.transactionId);
    Sentry.captureException(error);
  });
}
```

## Distributed Tracing Architecture

### Service-to-Service
```typescript
// Outgoing request (client)
async function callService(url: string, data: unknown) {
  const transaction = Sentry.getCurrentHub().getScope()?.getTransaction();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Propagate trace context
  if (transaction) {
    headers['sentry-trace'] = transaction.toTraceparent();
    headers['baggage'] = Sentry.getBaggage()?.toString() || '';
  }

  return fetch(url, { method: 'POST', headers, body: JSON.stringify(data) });
}

// Incoming request (server)
app.use((req, res, next) => {
  const transaction = Sentry.continueTrace(
    {
      sentryTrace: req.headers['sentry-trace'],
      baggage: req.headers['baggage'],
    },
    (ctx) =>
      Sentry.startTransaction({
        ...ctx,
        name: `${req.method} ${req.path}`,
        op: 'http.server',
      })
  );

  Sentry.getCurrentHub().configureScope((scope) => {
    scope.setSpan(transaction);
  });

  res.on('finish', () => transaction.finish());
  next();
});
```

## Alerting Architecture

### Alert Hierarchy
```
Critical (Page immediately)
├── Error rate > 10% (5 min)
├── P0 issue detected
└── Service down

Warning (Slack notification)
├── Error rate > 5%
├── New error type
└── Performance degradation

Info (Daily digest)
├── Resolved issues
├── Release health
└── Trend reports
```

### Issue Routing
```yaml
# Alert rules by team
backend-team:
  - path:match("/api/*")
  - tag:service IN [user-service, payment-service]

frontend-team:
  - platform:javascript
  - tag:service = web-frontend

devops-team:
  - tag:category = infrastructure
  - level:fatal
```

## Best Practices Summary

1. **One project per service** in microservices
2. **Centralized config module** for consistency
3. **Environment separation** (prod/staging/dev)
4. **Distributed tracing** across services
5. **Standard error handling** patterns
6. **Team-based alert routing**
7. **Release tracking** for every deploy

## Resources
- [Sentry Best Practices](https://docs.sentry.io/product/issues/best-practices/)
- [Distributed Tracing](https://docs.sentry.io/product/performance/distributed-tracing/)
