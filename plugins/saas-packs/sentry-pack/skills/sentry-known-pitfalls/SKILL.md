---
name: sentry-known-pitfalls
description: |
  Common Sentry pitfalls and how to avoid them.
  Use when troubleshooting Sentry issues, reviewing configurations,
  or preventing common mistakes.
  Trigger with phrases like "sentry mistakes", "sentry pitfalls",
  "sentry common issues", "sentry anti-patterns".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, anti-patterns, troubleshooting, best-practices]

---
# Sentry Known Pitfalls

## Prerequisites
- Existing Sentry implementation to review
- Access to SDK configuration code
- Understanding of current error patterns
- Codebase access for applying fixes

## Instructions

### Pitfall 1: Late Initialization

The most common issue. SDK must initialize BEFORE importing any module you want instrumented.

```typescript
// WRONG — Express imported before Sentry
import express from 'express';
import * as Sentry from '@sentry/node';
Sentry.init({ dsn: process.env.SENTRY_DSN });
// Result: Express is NOT instrumented

// RIGHT — Sentry initialized in separate file, loaded first
// instrument.mjs
import * as Sentry from '@sentry/node';
Sentry.init({ dsn: process.env.SENTRY_DSN });

// app.mjs (loaded after instrument.mjs)
import express from 'express';

// Run with: node --import ./instrument.mjs app.mjs
```

### Pitfall 2: Capturing Strings Instead of Errors

```typescript
// WRONG — no stack trace
Sentry.captureException('something went wrong');
// WRONG — no stack trace
Promise.reject('auth failed');
// WRONG — no stack trace
throw 'bad request';

// RIGHT — full stack trace preserved
Sentry.captureException(new Error('something went wrong'));
Promise.reject(new Error('auth failed'));
throw new Error('bad request');

// For third-party code that throws non-Error values:
try {
  thirdPartyLib.call();
} catch (error) {
  Sentry.captureException(
    error instanceof Error ? error : new Error(String(error))
  );
}
```

### Pitfall 3: beforeSend Returns Undefined

```typescript
// WRONG — function implicitly returns undefined, dropping ALL events
Sentry.init({
  beforeSend(event) {
    if (event.level === 'error') {
      return event; // Only returns for errors
    }
    // Falls through — returns undefined — ALL non-error events dropped!
  },
});

// RIGHT — always return event or null
Sentry.init({
  beforeSend(event) {
    if (shouldDrop(event)) {
      return null; // Explicitly drop
    }
    return event; // Always return the event
  },
});
```

### Pitfall 4: Multiple Sentry.init() Calls

```typescript
// WRONG — calling init() more than once
// File A:
Sentry.init({ dsn: DSN_A, environment: 'production' });
// File B (loaded later):
Sentry.init({ dsn: DSN_B, environment: 'staging' }); // Overwrites A!

// RIGHT — single init in dedicated file
// instrument.mjs — THE ONLY file that calls Sentry.init()
Sentry.init({ dsn: process.env.SENTRY_DSN });

// Diagnosis: search for multiple inits
// grep -r "Sentry.init" --include="*.ts" --include="*.js" src/
```

### Pitfall 5: Hardcoded DSN

```typescript
// WRONG — DSN in source code
Sentry.init({
  dsn: 'https://abc123@o0.ingest.sentry.io/12345', // NEVER do this
});

// RIGHT — from environment variable
Sentry.init({
  dsn: process.env.SENTRY_DSN,
});

// Prevent in CI:
// grep -r "ingest.sentry.io" --include="*.ts" --include="*.js" src/
```

### Pitfall 6: Scope Pollution in Async Context

```typescript
// WRONG — global scope mutations leak between requests
app.get('/api/user/:id', async (req, res) => {
  Sentry.setUser({ id: req.params.id });     // Leaks to other requests!
  Sentry.setTag('route', '/api/user/:id');     // Leaks!
  // ... handle request
});

// RIGHT — use withScope for per-request context
app.get('/api/user/:id', async (req, res) => {
  Sentry.withScope((scope) => {
    scope.setUser({ id: req.params.id });     // Scoped to this request
    scope.setTag('route', '/api/user/:id');
    // ... handle request
  });
});

// Or use Sentry's Express middleware which handles this automatically
```

### Pitfall 7: High-Cardinality Transaction Names

```typescript
// WRONG — unique transaction name per request (cardinality explosion)
Sentry.startSpan({ name: `GET /api/users/${userId}` }, () => {});
// Creates thousands of unique transactions: GET /api/users/1, GET /api/users/2, ...

// RIGHT — parameterized names (Sentry auto-does this for Express routes)
Sentry.startSpan({
  name: 'GET /api/users/:id',
  attributes: { 'user.id': userId }, // Put dynamic values in attributes
}, () => {});
```

### Pitfall 8: Not Flushing Before Process Exit

```typescript
// WRONG — events may be lost
process.on('uncaughtException', (error) => {
  Sentry.captureException(error);
  process.exit(1); // Events may not have been sent yet!
});

// RIGHT — flush before exit
process.on('uncaughtException', async (error) => {
  Sentry.captureException(error);
  await Sentry.close(2000); // Wait up to 2s for events to send
  process.exit(1);
});
```

### Pitfall 9: Source Map URL Prefix Mismatch

```bash
# Your JS is served at: https://example.com/static/js/main.abc123.js
# You uploaded with:    --url-prefix="~/js"
# Sentry looks for:     ~/js/main.abc123.js
# Actual URL:           ~/static/js/main.abc123.js
# Result: Source maps don't resolve!

# Fix: match the URL path exactly
sentry-cli sourcemaps upload \
  --url-prefix="~/static/js" \  # Must match the URL path
  ./dist

# Diagnosis: check what URL your JS loads from
# Browser DevTools > Network tab > look at JS file URLs
```

### Pitfall 10: sendDefaultPii in Production

```typescript
// WRONG — sends IP addresses, cookies, request bodies
Sentry.init({
  sendDefaultPii: true, // Fine for dev, DANGEROUS for production
});

// RIGHT — environment-aware PII setting
Sentry.init({
  sendDefaultPii: process.env.NODE_ENV !== 'production',
});
```

### Pitfall 11: Alert Fatigue

```
// WRONG: Alert on EVERY event
// Result: 1000 alerts/day -> team ignores all of them

// RIGHT: Alert on meaningful thresholds
// Issue Alert: "New issue is created" (not "event occurs")
// Metric Alert: "Error rate > 50/min" (not "> 1/min")
// Use: "First seen" not "Every event" for issue alerts
```

### Pitfall 12: Release Version Mismatch

```typescript
// WRONG — SDK release doesn't match CLI release
// CLI: sentry-cli releases new "1.0.0"
// SDK: Sentry.init({ release: process.env.npm_package_version })
// If npm_package_version is "1.0.0-beta", source maps won't resolve

// RIGHT — use the same version source
const VERSION = process.env.SENTRY_RELEASE || process.env.npm_package_version;

// In SDK:
Sentry.init({ release: VERSION });

// In CLI:
// sentry-cli releases new "$VERSION"
```

### Quick Audit Checklist

Run through this for any existing Sentry setup:

```bash
# 1. Single init point?
grep -r "Sentry.init" --include="*.ts" --include="*.js" src/ | wc -l
# Expected: 1

# 2. No hardcoded DSN?
grep -r "ingest.sentry.io" --include="*.ts" --include="*.js" src/
# Expected: 0 results

# 3. sendDefaultPii not true in production?
grep -r "sendDefaultPii.*true" --include="*.ts" --include="*.js" src/
# Expected: 0 results or gated behind env check

# 4. beforeSend always returns?
# Manual review: every code path in beforeSend returns event or null

# 5. Error objects (not strings)?
grep -r "captureException\s*(" --include="*.ts" --include="*.js" src/
# Review: should always pass Error objects
```

## Output
- All 12 pitfalls identified and resolved
- Single initialization point confirmed
- Proper Error objects in all capture calls
- beforeSend returning event or null on all paths
- Source map URL prefix matching production URLs
- Audit checklist completed for existing setup

## Error Handling

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Late init | "Express is not instrumented" | Use `--import ./instrument.mjs` |
| String capture | Missing stack traces | Always use `new Error()` |
| beforeSend void | Events silently dropped | Always `return event` or `return null` |
| Multiple init | Inconsistent behavior | Consolidate to single instrument file |
| Scope pollution | Wrong user/tags on events | Use `withScope()` per request |
| No flush | Lost events on exit | Add `Sentry.close()` to shutdown handlers |

## Resources
- [Troubleshooting](https://docs.sentry.io/platforms/javascript/troubleshooting/)
- [Best Practices](https://docs.sentry.io/product/issues/best-practices/)
- [Configuration Options](https://docs.sentry.io/platforms/javascript/configuration/options/)
- [Source Maps](https://docs.sentry.io/platforms/javascript/sourcemaps/)
