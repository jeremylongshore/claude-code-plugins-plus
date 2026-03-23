---
name: sentry-sdk-patterns
description: |
  Best practices for using Sentry SDK in TypeScript and Python.
  Use when implementing structured error context with scopes, breadcrumb
  strategies, beforeSend/beforeBreadcrumb filtering, custom fingerprinting,
  user context, or performance span creation.
  Trigger: "sentry best practices", "sentry patterns", "sentry sdk usage",
  "sentry code structure", "sentry scope", "sentry breadcrumbs",
  "sentry beforeSend", "sentry fingerprint".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, python, typescript, best-practices, error-handling]
---

# Sentry SDK Patterns

Production patterns for `@sentry/node` (v8+) and `sentry-sdk` (Python 2.x+). Covers scoped error context, breadcrumb strategies, event filtering, custom fingerprinting, user context, and performance instrumentation.

## Prerequisites

- Sentry SDK v8+ installed (`@sentry/node`, `@sentry/react`, or `sentry-sdk`)
- `SENTRY_DSN` environment variable configured
- Familiarity with async/await in TypeScript or Python context managers

## Instructions

### Step 1 -- Structured Error Context with Scopes

Use `Sentry.withScope()` (TypeScript) or `sentry_sdk.push_scope()` / `sentry_sdk.new_scope()` (Python) to attach context to individual events without leaking state across requests.

**TypeScript -- Scoped error capture:**

```typescript
import * as Sentry from '@sentry/node';

type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';

interface ErrorOptions {
  severity?: ErrorSeverity;
  tags?: Record<string, string>;
  context?: Record<string, unknown>;
  user?: { id: string; email?: string };
  fingerprint?: string[];
}

const SEVERITY_MAP: Record<ErrorSeverity, Sentry.SeverityLevel> = {
  low: 'info',
  medium: 'warning',
  high: 'error',
  critical: 'fatal',
};

export function captureError(error: Error, options: ErrorOptions = {}) {
  Sentry.withScope((scope) => {
    scope.setLevel(SEVERITY_MAP[options.severity || 'medium']);

    if (options.tags) {
      Object.entries(options.tags).forEach(([key, value]) => {
        scope.setTag(key, value);
      });
    }

    if (options.context) {
      scope.setContext('app', options.context);
    }

    if (options.user) {
      scope.setUser(options.user);
    }

    if (options.fingerprint) {
      scope.setFingerprint(options.fingerprint);
    }

    Sentry.captureException(error);
  });
}
```

**Python -- Scoped error capture:**

```python
import sentry_sdk

def capture_error(error, severity="error", tags=None, context=None, user=None):
    """Capture exception with isolated scope context."""
    with sentry_sdk.new_scope() as scope:
        scope.set_level(severity)
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        if context:
            scope.set_context("app", context)
        if user:
            scope.set_user(user)
        sentry_sdk.capture_exception(error)

# Usage
try:
    process_order(order_id)
except Exception as e:
    capture_error(
        e,
        severity="error",
        tags={"module": "payments", "region": "us-east-1"},
        context={"order_id": order_id, "total": amount},
        user={"id": str(user_id), "email": user_email},
    )
```

**Key rule:** Never call `Sentry.setTag()` or `sentry_sdk.set_tag()` at the module level inside request handlers. Those mutate the global scope and leak between concurrent requests. Always use `withScope()` or `new_scope()`.

### Step 2 -- Breadcrumbs, Filtering, and Fingerprints

#### Structured breadcrumb strategy

Create typed breadcrumb helpers so all breadcrumbs follow a consistent schema:

```typescript
import * as Sentry from '@sentry/node';

export const breadcrumb = {
  auth(action: string, userId?: string) {
    Sentry.addBreadcrumb({
      category: 'auth',
      message: `${action}${userId ? ` for user ${userId}` : ''}`,
      level: 'info',
    });
  },

  db(operation: string, table: string, durationMs?: number) {
    Sentry.addBreadcrumb({
      category: 'db',
      message: `${operation} on ${table}`,
      level: 'info',
      data: { table, operation, ...(durationMs && { duration_ms: durationMs }) },
    });
  },

  http(method: string, url: string, status: number) {
    Sentry.addBreadcrumb({
      category: 'http',
      message: `${method} ${url} -> ${status}`,
      level: status >= 400 ? 'warning' : 'info',
      data: { method, url, status_code: status },
    });
  },

  business(action: string, data?: Record<string, unknown>) {
    Sentry.addBreadcrumb({
      category: 'business',
      message: action,
      level: 'info',
      data,
    });
  },
};

// Usage trail leading up to an error
breadcrumb.auth('login', user.id);
breadcrumb.db('SELECT', 'orders', 12);
breadcrumb.http('POST', '/api/payments', 201);
breadcrumb.business('Order placed', { orderId, total });
```

**Python breadcrumbs:**

```python
import sentry_sdk

sentry_sdk.add_breadcrumb(
    category="auth",
    message="User logged in",
    level="info",
    data={"user_id": user_id, "method": "oauth"},
)

sentry_sdk.add_breadcrumb(
    category="db",
    message=f"SELECT on orders ({duration_ms}ms)",
    level="info",
    data={"table": "orders", "duration_ms": duration_ms},
)
```

#### beforeSend -- Drop noise, scrub PII

`beforeSend` is the last chance to modify or discard events before they leave the client:

```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,

  beforeSend(event, hint) {
    const error = hint?.originalException;

    // Drop known non-actionable errors
    if (error instanceof Error) {
      if (error.message.includes('ResizeObserver loop')) return null;
      if (error.message.includes('Network request failed')) return null;
    }

    // Scrub PII from user context
    if (event.user) {
      delete event.user.ip_address;
      delete event.user.email;
    }

    // Scrub sensitive cookies
    if (event.request?.cookies) {
      event.request.cookies = '[Filtered]';
    }

    return event;
  },
});
```

**Python beforeSend:**

```python
import sentry_sdk

def before_send(event, hint):
    # Drop expected errors
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, (KeyboardInterrupt, SystemExit)):
            return None
        if isinstance(exc_value, ConnectionError):
            return None

    # Scrub PII
    if "user" in event:
        event["user"].pop("email", None)
        event["user"].pop("ip_address", None)

    return event

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    before_send=before_send,
)
```

#### beforeBreadcrumb -- Filter noisy breadcrumbs

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  beforeBreadcrumb(breadcrumb, hint) {
    // Drop console.log breadcrumbs in production
    if (breadcrumb.category === 'console' && breadcrumb.level === 'log') {
      return null;
    }

    // Redact auth tokens from HTTP breadcrumbs
    if (breadcrumb.category === 'fetch' && breadcrumb.data?.url) {
      const url = new URL(breadcrumb.data.url);
      url.searchParams.delete('token');
      url.searchParams.delete('api_key');
      breadcrumb.data.url = url.toString();
    }

    return breadcrumb;
  },
});
```

#### Custom fingerprints for better issue grouping

By default Sentry groups by stack trace. Override when the same root cause produces different stacks:

```typescript
Sentry.withScope((scope) => {
  // Group all payment gateway timeouts together regardless of stack
  scope.setFingerprint(['payment-gateway-timeout', gatewayName]);

  // Group by error type + endpoint, not full stack
  // scope.setFingerprint(['{{ default }}', req.path]);

  Sentry.captureException(error);
});
```

```python
with sentry_sdk.new_scope() as scope:
    scope.fingerprint = ["payment-gateway-timeout", gateway_name]
    sentry_sdk.capture_exception(error)
```

### Step 3 -- Framework Integration and Performance Spans

#### Express middleware pattern (Sentry v8)

```typescript
import * as Sentry from '@sentry/node';
import express from 'express';

const app = express();

// Sentry v8: use setupExpressErrorHandler instead of Handlers
Sentry.setupExpressErrorHandler(app);

// Custom request context middleware (register BEFORE routes)
app.use((req, res, next) => {
  Sentry.setUser({
    id: req.user?.id,
    ip_address: req.ip,
  });
  Sentry.setTag('route', req.route?.path || req.path);

  Sentry.addBreadcrumb({
    category: 'http',
    message: `${req.method} ${req.path}`,
    data: { query: req.query, params: req.params },
  });

  next();
});

// Custom error handler (register AFTER routes, AFTER Sentry error handler)
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  Sentry.withScope((scope) => {
    scope.setContext('request', {
      method: req.method,
      url: req.originalUrl,
      params: req.params,
      query: req.query,
    });
    Sentry.captureException(err);
  });
  res.status(500).json({ error: 'Internal server error' });
});
```

#### React Error Boundary (browser)

```tsx
import * as Sentry from '@sentry/react';

const SentryErrorBoundary = Sentry.withErrorBoundary(App, {
  fallback: ({ error, resetError }) => (
    <div>
      <h2>Something went wrong</h2>
      <pre>{error.message}</pre>
      <button onClick={resetError}>Try again</button>
    </div>
  ),
  beforeCapture: (scope) => {
    scope.setTag('location', 'error-boundary');
    scope.setLevel('fatal');
  },
});
```

#### Performance spans (TypeScript)

```typescript
import * as Sentry from '@sentry/node';

// Wrap an operation in a span
async function processOrder(orderId: string) {
  return Sentry.startSpan(
    { name: 'processOrder', op: 'task', attributes: { orderId } },
    async (span) => {
      // Child span for DB read
      const order = await Sentry.startSpan(
        { name: 'db.getOrder', op: 'db.query' },
        () => db.orders.findById(orderId),
      );

      // Child span for payment
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

#### Performance spans (Python)

```python
import sentry_sdk
from functools import wraps

def sentry_traced(op="function"):
    """Decorator to wrap functions in Sentry spans."""
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

@sentry_traced(op="task")
def process_order(order_id: str):
    order = get_user(order_id)  # Creates child span automatically
    charge_payment(order)
```

#### Async error handling with concurrent operations

```typescript
async function processItems(items: Item[]) {
  const results = await Promise.allSettled(
    items.map((item) =>
      Sentry.startSpan(
        { name: `process.${item.type}`, op: 'task' },
        () => processItem(item),
      ),
    ),
  );

  const failures = results.filter(
    (r): r is PromiseRejectedResult => r.status === 'rejected',
  );

  if (failures.length > 0) {
    Sentry.withScope((scope) => {
      scope.setTag('batch_size', String(items.length));
      scope.setTag('failure_count', String(failures.length));
      scope.setContext('failures', {
        reasons: failures.map((f) => f.reason?.message || String(f.reason)),
      });
      Sentry.captureMessage(
        `${failures.length}/${items.length} items failed`,
        'warning',
      );
    });
    failures.forEach((f) => Sentry.captureException(f.reason));
  }
}
```

#### Django middleware (Python)

```python
import sentry_sdk

class SentryUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            sentry_sdk.set_user({
                "id": str(request.user.id),
                "email": request.user.email,
                "username": request.user.username,
            })
        response = self.get_response(request)
        return response
```

#### Testing Sentry integration

```typescript
import * as Sentry from '@sentry/node';

vi.mock('@sentry/node', () => ({
  captureException: vi.fn(),
  captureMessage: vi.fn(),
  withScope: vi.fn((cb) =>
    cb({
      setTag: vi.fn(),
      setContext: vi.fn(),
      setUser: vi.fn(),
      setLevel: vi.fn(),
      setFingerprint: vi.fn(),
    }),
  ),
  addBreadcrumb: vi.fn(),
  setUser: vi.fn(),
  setTag: vi.fn(),
  startSpan: vi.fn((opts, cb) => cb({ setStatus: vi.fn() })),
}));

it('captures payment errors with correct context', async () => {
  await processPayment({ amount: -1 });
  expect(Sentry.captureException).toHaveBeenCalledWith(
    expect.objectContaining({
      message: expect.stringContaining('Invalid amount'),
    }),
  );
});
```

## Output

After applying these patterns you will have:

- Centralized error handler module with typed severity and scoped context
- Structured breadcrumb helpers for auth, db, http, and business events
- `beforeSend` filter that drops noise and scrubs PII
- `beforeBreadcrumb` callback that redacts sensitive query parameters
- Custom fingerprinting for accurate issue grouping
- Framework error boundaries for Express and React
- Performance spans for tracing critical code paths
- Test mocks for verifying Sentry integration

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Scope leaking between requests | Global scope mutations in async handlers | Use `withScope()` / `new_scope()` for per-event context; never call `Sentry.setTag()` in request handlers |
| Duplicate events | Error caught and re-thrown, captured at two layers | Capture at one level only -- either middleware or handler, not both |
| Missing breadcrumbs on errors | Breadcrumbs cleared after max count (default 100) | Set `maxBreadcrumbs` in `Sentry.init()`; keep breadcrumbs focused on relevant categories |
| `beforeSend` returns `undefined` | Missing return statement | Always return `event` or `null` explicitly |
| Events grouped incorrectly | Default stack-trace fingerprinting | Use `scope.setFingerprint()` with semantic keys for known error classes |
| `Sentry is not defined` | SDK not imported | Verify `import * as Sentry from '@sentry/node'` and package installation |
| `DSN parse error` | Malformed DSN string | Copy DSN from Sentry project settings at `sentry.io` |
| Spans not appearing | Missing tracing integration | Set `tracesSampleRate` in `Sentry.init()` (e.g., `0.1` for 10% sampling) |

## Examples

See [examples.md](references/examples.md) for full worked scenarios including context managers and decorator patterns.

## Resources

- [Sentry JavaScript SDK Best Practices](https://docs.sentry.io/platforms/javascript/best-practices/)
- [Scopes and Context](https://docs.sentry.io/platforms/javascript/enriching-events/scopes/)
- [Express Integration Guide](https://docs.sentry.io/platforms/javascript/guides/express/)
- [Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [Custom Fingerprinting](https://docs.sentry.io/platforms/javascript/enriching-events/fingerprinting/)
- [Performance Monitoring](https://docs.sentry.io/platforms/javascript/tracing/)

## Next Steps

- **sentry-error-capture** -- Deep dive on `captureException` vs `captureMessage` semantics
- **sentry-performance-tracing** -- Full distributed tracing setup with `tracesSampleRate` and custom instrumentation
- **sentry-data-handling** -- PII scrubbing, data residency, and GDPR-compliant Sentry configuration
- **sentry-common-errors** -- Troubleshooting guide for frequent SDK issues
