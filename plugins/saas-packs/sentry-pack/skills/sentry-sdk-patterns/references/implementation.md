# Implementation Guide

## Pattern Checklist

1. Create a centralized error handler module wrapping `Sentry.withScope()` / `sentry_sdk.new_scope()`
2. Implement structured breadcrumb helpers by category (auth, db, http, business)
3. Configure `beforeSend` to drop non-actionable errors and scrub PII
4. Configure `beforeBreadcrumb` to redact sensitive data from breadcrumb payloads
5. Set custom fingerprints for error classes where stack-trace grouping is insufficient
6. Implement framework error boundaries (Express middleware, React `withErrorBoundary`)
7. Add performance spans for critical code paths using `Sentry.startSpan()`
8. Mock Sentry in tests to verify context is attached correctly

## Pattern 1: Centralized Error Handler (TypeScript)

```typescript
import * as Sentry from '@sentry/node';

export function captureError(
  error: Error,
  context?: Record<string, unknown>
): string {
  return Sentry.captureException(error, {
    extra: context,
    tags: { handler: 'centralized' },
  });
}

export function captureWarning(
  message: string,
  context?: Record<string, unknown>
): void {
  Sentry.captureMessage(message, {
    level: 'warning',
    extra: context,
  });
}
```

## Pattern 2: Scoped Context (TypeScript)

```typescript
Sentry.withScope((scope) => {
  scope.setTag('module', 'payments');
  scope.setLevel('error');
  scope.setContext('order', { id: orderId, total: amount });
  scope.setUser({ id: userId });
  scope.setFingerprint(['payment-failure', gatewayName]);
  Sentry.captureException(error);
});
```

## Pattern 3: beforeSend Filter (TypeScript)

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  beforeSend(event, hint) {
    const error = hint?.originalException;
    if (error instanceof Error) {
      if (error.message.includes('ResizeObserver loop')) return null;
      if (error.message.includes('Network request failed')) return null;
    }
    if (event.user) {
      delete event.user.ip_address;
      delete event.user.email;
    }
    return event;
  },
});
```

## Pattern 4: Structured Breadcrumbs (TypeScript)

```typescript
Sentry.addBreadcrumb({
  category: 'payment',
  message: `Processing payment of $${amount}`,
  level: 'info',
  data: { userId, amount, gateway: 'stripe' },
});

try {
  await processPayment(userId, amount);
} catch (error) {
  Sentry.captureException(error);
  // Breadcrumbs above will appear in the event timeline
}
```

## Pattern 5: Performance Spans (TypeScript)

```typescript
async function processOrder(orderId: string) {
  return Sentry.startSpan(
    { name: 'processOrder', op: 'task', attributes: { orderId } },
    async (span) => {
      const order = await Sentry.startSpan(
        { name: 'db.getOrder', op: 'db.query' },
        () => db.orders.findById(orderId),
      );
      await Sentry.startSpan(
        { name: 'payment.charge', op: 'http.client' },
        () => chargePayment(order),
      );
      span.setStatus({ code: 1, message: 'ok' });
      return order;
    },
  );
}
```

## Pattern 6: Python Decorator for Spans

```python
import sentry_sdk
from functools import wraps

def sentry_traced(op="function"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with sentry_sdk.start_span(op=op, name=func.__name__):
                return func(*args, **kwargs)
        return wrapper
    return decorator

@sentry_traced(op="db.query")
def get_user(user_id: str):
    return db.users.find_one({"_id": user_id})
```

## Pattern 7: Express Error Middleware (Sentry v8)

```typescript
import * as Sentry from '@sentry/node';
import express from 'express';

const app = express();
Sentry.setupExpressErrorHandler(app);

app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  Sentry.withScope((scope) => {
    scope.setContext('request', {
      method: req.method,
      url: req.originalUrl,
      params: req.params,
    });
    Sentry.captureException(err);
  });
  res.status(500).json({ error: 'Internal server error' });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
