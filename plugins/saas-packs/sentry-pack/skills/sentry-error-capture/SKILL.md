---
name: sentry-error-capture
description: |
  Advanced error capture and context enrichment with Sentry.
  Use when implementing detailed error tracking, adding context,
  or customizing error capture behavior.
  Trigger with phrases like "sentry error capture", "sentry context",
  "enrich sentry errors", "sentry exception handling".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Error Capture

## Overview
Capture errors with rich context and metadata for better debugging.

## Prerequisites
- Sentry SDK installed and configured
- Understanding of error handling
- Application logging infrastructure

## Instructions

### Step 1: Basic Error Capture
```typescript
import * as Sentry from '@sentry/node';

try {
  await riskyOperation();
} catch (error) {
  const eventId = Sentry.captureException(error);
  console.log(`Error tracked: ${eventId}`);
}
```

### Step 2: Add User Context
```typescript
// Set user for all subsequent errors
Sentry.setUser({
  id: user.id,
  email: user.email,
  username: user.username,
  ip_address: request.ip,
});

// Clear user on logout
Sentry.setUser(null);
```

### Step 3: Add Tags and Extra Data
```typescript
// Tags for filtering
Sentry.setTag('feature', 'checkout');
Sentry.setTag('tenant', tenantId);

// Extra context data
Sentry.setExtra('cart_items', cart.items.length);
Sentry.setExtra('total_amount', cart.total);
```

### Step 4: Contextual Capture
```typescript
Sentry.captureException(error, {
  level: 'error',
  tags: {
    operation: 'payment',
    provider: 'stripe',
  },
  extra: {
    orderId: order.id,
    amount: order.total,
    currency: order.currency,
  },
  user: {
    id: customer.id,
    email: customer.email,
  },
});
```

### Step 5: Custom Fingerprinting
```typescript
Sentry.captureException(error, {
  fingerprint: [
    '{{ default }}',
    String(error.code),
    endpoint,
  ],
});
```

## Output
- Errors with full context in Sentry dashboard
- Filterable tags for issue management
- User attribution for error tracking

## Advanced Techniques

### Breadcrumb Trail
```typescript
// Automatic breadcrumbs (enabled by default)
// Manual breadcrumbs for custom events
Sentry.addBreadcrumb({
  type: 'navigation',
  category: 'route',
  message: `Navigated to ${path}`,
  level: 'info',
});

Sentry.addBreadcrumb({
  type: 'http',
  category: 'api',
  message: `API call to ${endpoint}`,
  data: { method, status },
  level: status >= 400 ? 'warning' : 'info',
});
```

### Attachments
```typescript
Sentry.captureException(error, (scope) => {
  scope.addAttachment({
    filename: 'debug.json',
    data: JSON.stringify(debugInfo),
    contentType: 'application/json',
  });
  return scope;
});
```

### Event Filtering
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  beforeSend(event, hint) {
    // Filter out specific errors
    if (hint.originalException?.message?.includes('Network')) {
      return null; // Don't send
    }

    // Modify event
    event.tags = { ...event.tags, processed: 'true' };
    return event;
  },
});
```

## Examples

### API Error Handler
```typescript
async function apiHandler(req, res, next) {
  try {
    const result = await processRequest(req);
    res.json(result);
  } catch (error) {
    Sentry.withScope((scope) => {
      scope.setTag('api_endpoint', req.path);
      scope.setTag('http_method', req.method);
      scope.setExtra('request_body', req.body);
      scope.setExtra('query_params', req.query);
      scope.setUser({ ip_address: req.ip });
      Sentry.captureException(error);
    });
    next(error);
  }
}
```

### Python Context Manager
```python
from contextlib import contextmanager
import sentry_sdk

@contextmanager
def capture_errors(operation: str, **context):
    try:
        yield
    except Exception as e:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag('operation', operation)
            for key, value in context.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_exception(e)
        raise

# Usage
with capture_errors('sync_users', batch_size=100):
    sync_all_users()
```

## Resources
- [Sentry Enriching Events](https://docs.sentry.io/platforms/javascript/enriching-events/)
- [Sentry Scopes](https://docs.sentry.io/platforms/javascript/enriching-events/scopes/)

## Next Steps
Proceed to `sentry-performance-tracing` for performance monitoring setup.
