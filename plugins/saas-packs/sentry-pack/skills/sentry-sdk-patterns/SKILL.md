---
name: sentry-sdk-patterns
description: |
  Best practices for using Sentry SDK in TypeScript and Python.
  Use when implementing error handling patterns, structuring Sentry code,
  or optimizing SDK usage.
  Trigger with phrases like "sentry best practices", "sentry patterns",
  "sentry sdk usage", "sentry code structure".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, python, typescript, best-practices]

---
# Sentry SDK Patterns

## Prerequisites
- Sentry SDK v8 installed and initialized
- Understanding of async/await patterns
- Familiarity with error handling in TypeScript or Python

## Instructions

### 1. Centralized Error Handler Module

Create a single module that wraps all Sentry interactions:

```typescript
// lib/error-handler.ts
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

export function captureMessage(
  message: string,
  level: Sentry.SeverityLevel = 'info',
  tags?: Record<string, string>
) {
  Sentry.withScope((scope) => {
    if (tags) {
      Object.entries(tags).forEach(([k, v]) => scope.setTag(k, v));
    }
    Sentry.captureMessage(message, level);
  });
}
```

### 2. Framework Error Boundaries

**Express middleware pattern:**
```typescript
// middleware/sentry-error.ts
import * as Sentry from '@sentry/node';
import { Request, Response, NextFunction } from 'express';

export function sentryRequestContext(req: Request, res: Response, next: NextFunction) {
  Sentry.setUser({
    id: req.user?.id,
    ip_address: req.ip,
  });

  Sentry.setTag('route', req.route?.path || req.path);
  Sentry.setTag('method', req.method);

  Sentry.addBreadcrumb({
    category: 'http',
    message: `${req.method} ${req.path}`,
    data: { query: req.query, params: req.params },
  });

  next();
}

// Register AFTER routes, BEFORE Sentry error handler
export function applicationErrorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  Sentry.withScope((scope) => {
    scope.setContext('request', {
      method: req.method,
      url: req.originalUrl,
      params: req.params,
      query: req.query,
    });
    Sentry.captureException(err);
  });
  next(err);
}
```

**React Error Boundary (browser):**
```tsx
import * as Sentry from '@sentry/react';

// Sentry v8 provides a built-in error boundary
const SentryErrorBoundary = Sentry.withErrorBoundary(App, {
  fallback: ({ error, resetError }) => (
    <div>
      <h2>Something went wrong</h2>
      <button onClick={resetError}>Try again</button>
    </div>
  ),
  beforeCapture: (scope) => {
    scope.setTag('location', 'error-boundary');
  },
});
```

### 3. Structured Breadcrumb Strategy

```typescript
// lib/breadcrumbs.ts
import * as Sentry from '@sentry/node';

export const breadcrumb = {
  auth(action: string, userId?: string) {
    Sentry.addBreadcrumb({
      category: 'auth',
      message: `${action}${userId ? ` for user ${userId}` : ''}`,
      level: 'info',
    });
  },

  db(operation: string, table: string, duration?: number) {
    Sentry.addBreadcrumb({
      category: 'db',
      message: `${operation} on ${table}`,
      level: 'info',
      data: { table, operation, ...(duration && { duration_ms: duration }) },
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

// Usage
breadcrumb.auth('login', user.id);
breadcrumb.db('SELECT', 'users', 12);
breadcrumb.http('POST', '/api/orders', 201);
breadcrumb.business('Order placed', { orderId, total });
```

### 4. Async Error Handling Patterns

```typescript
// Pattern: wrap async route handlers
function asyncHandler(fn: (req: Request, res: Response) => Promise<void>) {
  return (req: Request, res: Response, next: NextFunction) => {
    fn(req, res).catch((error) => {
      Sentry.captureException(error);
      next(error);
    });
  };
}

app.get('/api/data', asyncHandler(async (req, res) => {
  const data = await fetchData();
  res.json(data);
}));

// Pattern: concurrent operations with error isolation
async function processItems(items: Item[]) {
  const results = await Promise.allSettled(
    items.map((item) =>
      Sentry.startSpan({ name: `process.${item.type}`, op: 'task' }, () =>
        processItem(item)
      )
    )
  );

  const failures = results.filter(
    (r): r is PromiseRejectedResult => r.status === 'rejected'
  );

  if (failures.length > 0) {
    Sentry.captureMessage(`${failures.length}/${items.length} items failed`, 'warning');
    failures.forEach((f) => Sentry.captureException(f.reason));
  }
}
```

### 5. Python SDK Patterns

```python
# lib/sentry_utils.py
import sentry_sdk
from functools import wraps

def capture_error(error, severity="error", tags=None, context=None):
    """Centralized error capture with context."""
    with sentry_sdk.new_scope() as scope:
        scope.set_level(severity)
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        if context:
            scope.set_context("app", context)
        sentry_sdk.capture_exception(error)

def sentry_traced(op="function"):
    """Decorator to wrap functions in Sentry spans."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with sentry_sdk.start_span(op=op, name=func.__name__):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@sentry_traced(op="db.query")
def get_user(user_id: str):
    return db.users.find_one({"_id": user_id})

# Django middleware
class SentryUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            sentry_sdk.set_user({
                "id": str(request.user.id),
                "email": request.user.email,
            })
        return self.get_response(request)
```

### 6. Testing Sentry Integration

```typescript
// Mocking Sentry in tests
import * as Sentry from '@sentry/node';

vi.mock('@sentry/node', () => ({
  captureException: vi.fn(),
  captureMessage: vi.fn(),
  withScope: vi.fn((cb) => cb({
    setTag: vi.fn(),
    setContext: vi.fn(),
    setUser: vi.fn(),
    setLevel: vi.fn(),
    setFingerprint: vi.fn(),
  })),
  addBreadcrumb: vi.fn(),
  setUser: vi.fn(),
  setTag: vi.fn(),
}));

it('captures payment errors with correct context', async () => {
  await processPayment({ amount: -1 });
  expect(Sentry.captureException).toHaveBeenCalledWith(
    expect.objectContaining({ message: expect.stringContaining('Invalid amount') })
  );
});
```

## Output
- Centralized error handler module with consistent context
- Framework-specific error boundaries (Express, React)
- Structured breadcrumb strategy for debugging
- Async error handling with proper scope propagation
- Testable Sentry integration with mock patterns

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Scope leaking between requests | Global scope mutations in async context | Use `withScope()` for per-event context, never `Sentry.setTag()` globally in request handlers |
| Duplicate events | Error caught and re-thrown, captured twice | Capture at one level only — either middleware or handler, not both |
| Missing breadcrumbs | Breadcrumbs from wrong request | Sentry isolates breadcrumbs per async context in v8 |
| `beforeSend` returns undefined | Missing return statement | Always return `event` or `null` explicitly |

## Resources
- [SDK Best Practices](https://docs.sentry.io/platforms/javascript/best-practices/)
- [Scopes & Context](https://docs.sentry.io/platforms/javascript/enriching-events/scopes/)
- [Express Guide](https://docs.sentry.io/platforms/javascript/guides/express/)
- [Python SDK](https://docs.sentry.io/platforms/python/)
