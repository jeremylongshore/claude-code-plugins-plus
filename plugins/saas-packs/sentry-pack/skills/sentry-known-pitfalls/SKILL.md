---
name: sentry-known-pitfalls
description: |
  Common Sentry pitfalls and how to avoid them.
  Use when troubleshooting Sentry issues, reviewing configurations,
  or preventing common mistakes.
  Trigger with phrases like "sentry mistakes", "sentry pitfalls",
  "sentry common issues", "sentry anti-patterns".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Known Pitfalls

## Overview
Common mistakes and anti-patterns when using Sentry, and how to avoid them.

## SDK Initialization Pitfalls

### Pitfall 1: Late Initialization
```typescript
// ❌ BAD: Errors before init() are lost
app.use(errorHandler);
Sentry.init({ dsn: process.env.SENTRY_DSN });

// ✅ GOOD: Initialize first
Sentry.init({ dsn: process.env.SENTRY_DSN });
app.use(errorHandler);
```

### Pitfall 2: Multiple Initializations
```typescript
// ❌ BAD: Multiple init() calls cause issues
// file1.ts
Sentry.init({ dsn: 'dsn1' });

// file2.ts
Sentry.init({ dsn: 'dsn2' }); // Overwrites first!

// ✅ GOOD: Single initialization point
// sentry.ts
export function initSentry() {
  if (!Sentry.getCurrentHub().getClient()) {
    Sentry.init({ dsn: process.env.SENTRY_DSN });
  }
}
```

### Pitfall 3: Wrong SDK for Framework
```typescript
// ❌ BAD: Generic SDK for framework
import * as Sentry from '@sentry/node'; // In Next.js app

// ✅ GOOD: Framework-specific SDK
import * as Sentry from '@sentry/nextjs'; // Next.js
import * as Sentry from '@sentry/react'; // React
import * as Sentry from '@sentry/vue'; // Vue
```

## Error Capture Pitfalls

### Pitfall 4: Swallowing Errors
```typescript
// ❌ BAD: Error captured but swallowed
try {
  await riskyOperation();
} catch (error) {
  Sentry.captureException(error);
  // Error swallowed - app continues incorrectly
}

// ✅ GOOD: Capture and handle appropriately
try {
  await riskyOperation();
} catch (error) {
  Sentry.captureException(error);
  throw error; // Or handle properly
}
```

### Pitfall 5: Capturing Non-Errors
```typescript
// ❌ BAD: Capturing strings instead of errors
Sentry.captureException('Something went wrong'); // No stack trace!

// ✅ GOOD: Capture actual Error objects
Sentry.captureException(new Error('Something went wrong'));

// Or use captureMessage for non-errors
Sentry.captureMessage('Something happened', 'info');
```

### Pitfall 6: Double Capture
```typescript
// ❌ BAD: Capturing same error multiple times
app.use((err, req, res, next) => {
  Sentry.captureException(err);
  next(err);
});
app.use(Sentry.Handlers.errorHandler()); // Captures again!

// ✅ GOOD: Single capture point
app.use(Sentry.Handlers.errorHandler()); // Only this
```

## Configuration Pitfalls

### Pitfall 7: Hardcoded DSN
```typescript
// ❌ BAD: DSN in code
Sentry.init({
  dsn: 'https://abc123@sentry.io/123', // Exposed!
});

// ✅ GOOD: Environment variable
Sentry.init({
  dsn: process.env.SENTRY_DSN,
});
```

### Pitfall 8: 100% Sampling in Production
```typescript
// ❌ BAD: Full sampling = huge bills
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0, // 100% of all requests!
});

// ✅ GOOD: Production-appropriate rates
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
});
```

### Pitfall 9: Ignoring beforeSend Return
```typescript
// ❌ BAD: Not returning event
Sentry.init({
  beforeSend(event) {
    console.log('Event:', event);
    // Forgot to return! Event is dropped.
  },
});

// ✅ GOOD: Always return event (or null to drop)
Sentry.init({
  beforeSend(event) {
    console.log('Event:', event);
    return event; // Don't forget!
  },
});
```

## Performance Pitfalls

### Pitfall 10: Not Finishing Transactions
```typescript
// ❌ BAD: Transaction never finished
const transaction = Sentry.startTransaction({ name: 'operation' });
await doWork();
// Forgot transaction.finish()!

// ✅ GOOD: Always finish with try/finally
const transaction = Sentry.startTransaction({ name: 'operation' });
try {
  await doWork();
} finally {
  transaction.finish();
}
```

### Pitfall 11: Orphan Spans
```typescript
// ❌ BAD: Spans without transaction context
const span = Sentry.startSpan({ name: 'work' }); // No parent!

// ✅ GOOD: Spans within transaction
const transaction = Sentry.startTransaction({ name: 'operation' });
Sentry.getCurrentHub().configureScope((scope) => scope.setSpan(transaction));

const span = transaction.startChild({ op: 'work' });
// Now properly linked
```

## Source Maps Pitfalls

### Pitfall 12: Wrong URL Prefix
```bash
# ❌ BAD: Prefix doesn't match actual URLs
sentry-cli releases files $VERSION upload-sourcemaps ./dist
# Files uploaded as ~/dist/main.js
# But browser loads from /static/js/main.js

# ✅ GOOD: Match actual URL structure
sentry-cli releases files $VERSION upload-sourcemaps ./dist \
  --url-prefix "~/static/js"
```

### Pitfall 13: Release Version Mismatch
```typescript
// ❌ BAD: SDK and CLI use different versions
// SDK: release: 'v1.0.0'
// CLI: sentry-cli releases new '1.0.0' (no 'v' prefix)

// ✅ GOOD: Consistent versioning
const VERSION = process.env.GIT_SHA;
Sentry.init({ release: VERSION });
// CLI: sentry-cli releases new $GIT_SHA
```

## Integration Pitfalls

### Pitfall 14: Missing Request Handler
```typescript
// ❌ BAD: Error handler without request handler
app.use(Sentry.Handlers.errorHandler());
// Missing request context!

// ✅ GOOD: Both handlers in correct order
app.use(Sentry.Handlers.requestHandler());
// ... routes ...
app.use(Sentry.Handlers.errorHandler());
```

### Pitfall 15: Blocking Event Sending
```typescript
// ❌ BAD: Awaiting Sentry in request path
app.post('/api/data', async (req, res) => {
  try {
    const result = await processData(req.body);
    res.json(result);
  } catch (error) {
    await Sentry.captureException(error); // Blocks response!
    await Sentry.flush(5000); // Even more blocking!
    res.status(500).json({ error: 'Failed' });
  }
});

// ✅ GOOD: Non-blocking capture
app.post('/api/data', async (req, res) => {
  try {
    const result = await processData(req.body);
    res.json(result);
  } catch (error) {
    Sentry.captureException(error); // Fire and forget
    res.status(500).json({ error: 'Failed' });
  }
});
```

## Monitoring Pitfalls

### Pitfall 16: Alert Fatigue
```yaml
# ❌ BAD: Alert on every error
alert_rules:
  - condition: any_error
    action: email_team  # Hundreds of emails!

# ✅ GOOD: Threshold-based alerts
alert_rules:
  - condition: error_rate > 5%
    action: slack_warning
  - condition: error_rate > 20%
    action: pagerduty_critical
```

### Pitfall 17: Ignoring Release Health
```typescript
// ❌ BAD: No release tracking
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  // No release specified
});

// ✅ GOOD: Track releases
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  release: `myapp@${process.env.GIT_SHA}`,
  autoSessionTracking: true,
});
```

## Checklist: Avoid These Pitfalls

```markdown
## SDK Setup
- [ ] Initialize Sentry before app starts
- [ ] Use framework-specific SDK
- [ ] Single initialization point
- [ ] DSN in environment variable

## Error Handling
- [ ] Capture Error objects, not strings
- [ ] Single capture point (no duplicates)
- [ ] Re-throw or handle after capture
- [ ] Return event from beforeSend

## Performance
- [ ] Production-appropriate sample rates
- [ ] Finish all transactions
- [ ] Non-blocking captures
- [ ] Spans attached to transactions

## Source Maps
- [ ] Correct URL prefix
- [ ] Matching release versions
- [ ] Upload in CI/CD

## Monitoring
- [ ] Threshold-based alerts
- [ ] Release tracking enabled
- [ ] Environment tags
```

## Resources
- [Sentry Best Practices](https://docs.sentry.io/product/issues/best-practices/)
- [Troubleshooting Guide](https://docs.sentry.io/platforms/javascript/troubleshooting/)
