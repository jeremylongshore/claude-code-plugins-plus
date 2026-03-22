---
name: sentry-error-capture
description: |
  Implement advanced error capture and context enrichment with Sentry.
  Use when implementing detailed error tracking, adding context,
  or customizing error capture behavior.
  Trigger with phrases like "sentry error capture", "sentry context",
  "enrich sentry errors", "sentry exception handling".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, error-tracking, context, breadcrumbs]

---
# Sentry Error Capture

## Prerequisites
- Sentry SDK v8 installed and initialized
- Understanding of try/catch and async error handling
- Application logging infrastructure in place

## Instructions

### 1. captureException — The Core Method

Always pass real `Error` objects, never plain strings:

```typescript
import * as Sentry from '@sentry/node';

// CORRECT — full stack trace preserved
try {
  await riskyOperation();
} catch (error) {
  Sentry.captureException(error);
}

// WRONG — no stack trace, hard to debug
Sentry.captureException('something went wrong');

// Wrapping non-Error values
Sentry.captureException(new Error(`API returned ${statusCode}: ${body}`));
```

### 2. captureMessage — For Informational Events

```typescript
// Severity levels: 'fatal' | 'error' | 'warning' | 'info' | 'debug' | 'log'
Sentry.captureMessage('Payment processed successfully', 'info');
Sentry.captureMessage('Deprecated API endpoint accessed', 'warning');
Sentry.captureMessage('Database connection pool exhausted', 'fatal');
```

### 3. Scoped Context with withScope

Use `withScope` to attach context to a single event without polluting the global scope:

```typescript
Sentry.withScope((scope) => {
  scope.setTag('payment_provider', 'stripe');
  scope.setTag('payment_type', 'subscription');
  scope.setLevel('error');

  scope.setContext('payment', {
    amount: 9999,
    currency: 'USD',
    customer_id: 'cus_abc123',
    idempotency_key: 'idem_xyz789',
  });

  scope.setUser({
    id: user.id,
    email: user.email,
    subscription: user.plan,
  });

  scope.setFingerprint(['payment-failure', paymentProvider]);

  Sentry.captureException(error);
});
// Scope is automatically cleaned up — global scope unchanged
```

### 4. Breadcrumbs for Debugging Context

Breadcrumbs create a trail of events leading up to an error:

```typescript
// Manual breadcrumbs
Sentry.addBreadcrumb({
  category: 'auth',
  message: `User ${userId} logged in via ${provider}`,
  level: 'info',
  data: { provider, method: 'oauth2' },
});

Sentry.addBreadcrumb({
  category: 'navigation',
  message: 'User navigated to /checkout',
  level: 'info',
});

Sentry.addBreadcrumb({
  category: 'transaction',
  message: 'Payment initiated',
  level: 'info',
  data: { amount: 49.99, items: 3 },
});

// The next captured error includes all breadcrumbs above
```

### 5. Custom Fingerprinting for Issue Grouping

Override Sentry's default grouping to control how errors are grouped into issues:

```typescript
Sentry.withScope((scope) => {
  // Group all timeout errors for /api/search into one issue
  scope.setFingerprint(['api-timeout', 'search-endpoint']);
  Sentry.captureException(new Error('Search API timeout'));
});

// Group by error type + HTTP status
Sentry.withScope((scope) => {
  scope.setFingerprint(['http-error', String(response.status), endpoint]);
  Sentry.captureException(error);
});
```

### 6. beforeSend for Global Filtering and Enrichment

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  beforeSend(event, hint) {
    const error = hint?.originalException;

    // Drop specific error types
    if (error instanceof AbortError) return null;
    if (error?.message?.match(/ResizeObserver loop/)) return null;

    // Scrub sensitive data from event
    if (event.request?.headers) {
      delete event.request.headers['Authorization'];
      delete event.request.headers['Cookie'];
    }

    // Add custom context based on error type
    if (error instanceof DatabaseError) {
      event.tags = { ...event.tags, subsystem: 'database' };
      event.level = 'fatal';
    }

    return event; // Must return event or null
  },

  // Filter noisy errors by pattern
  ignoreErrors: [
    'ResizeObserver loop',
    'Non-Error promise rejection',
    /Loading chunk \d+ failed/,
    'Network request failed',
  ],
});
```

### 7. Express Error Handler

```typescript
import express from 'express';
import * as Sentry from '@sentry/node';

const app = express();

// Sentry request handler — must be first middleware
Sentry.setupExpressErrorHandler(app);

// Your routes
app.get('/api/users/:id', async (req, res) => {
  Sentry.setUser({ id: req.params.id });

  try {
    const user = await getUser(req.params.id);
    res.json(user);
  } catch (error) {
    Sentry.withScope((scope) => {
      scope.setContext('request', {
        params: req.params,
        query: req.query,
        method: req.method,
      });
      Sentry.captureException(error);
    });
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

### 8. Async Error Handling

```typescript
// Promise rejections — Sentry captures unhandled rejections automatically
// For handled promises, capture explicitly:
async function processQueue(items: QueueItem[]) {
  const results = await Promise.allSettled(
    items.map(item => processItem(item))
  );

  results.forEach((result, index) => {
    if (result.status === 'rejected') {
      Sentry.withScope((scope) => {
        scope.setTag('queue_item_index', index);
        scope.setContext('item', items[index]);
        Sentry.captureException(result.reason);
      });
    }
  });
}
```

### 9. Domain-Specific Error Classes

```typescript
class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public severity: Sentry.SeverityLevel = 'error',
    public context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AppError';
  }
}

function captureAppError(error: AppError) {
  Sentry.withScope((scope) => {
    scope.setTag('error_code', error.code);
    scope.setLevel(error.severity);
    if (error.context) {
      scope.setContext('app_error', error.context);
    }
    Sentry.captureException(error);
  });
}

// Usage
throw new AppError('Insufficient funds', 'PAYMENT_001', 'warning', {
  balance: 10.00,
  required: 49.99,
});
```

## Output
- Errors with full stack traces and context in Sentry dashboard
- Scoped tags and context for filtering and search
- Breadcrumb trails showing user actions before errors
- Custom fingerprinting grouping related errors into single issues
- Clean error filtering via beforeSend and ignoreErrors

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Missing stack trace | String passed instead of Error object | Always use `new Error()` or extend Error class |
| Events not grouped properly | Default fingerprinting insufficient | Use `scope.setFingerprint()` for custom grouping |
| `beforeSend` dropping all events | Function returns `undefined` instead of event | Ensure `beforeSend` always returns `event` or explicitly `null` |
| Scope leaking between requests | Using global scope in async context | Use `withScope()` for per-request context |
| Too many events | No filtering configured | Add `ignoreErrors`, `beforeSend` filters, or `sampleRate` |

## Resources
- [Capturing Errors](https://docs.sentry.io/platforms/javascript/usage/)
- [Scopes & Context](https://docs.sentry.io/platforms/javascript/enriching-events/scopes/)
- [Breadcrumbs](https://docs.sentry.io/platforms/javascript/enriching-events/breadcrumbs/)
- [Filtering Events](https://docs.sentry.io/platforms/javascript/configuration/filtering/)
- [Issue Grouping](https://docs.sentry.io/product/data-management-settings/event-grouping/)
