---
name: sentry-common-errors
description: |
  Troubleshoot common Sentry integration issues and fixes.
  Use when encountering Sentry errors, missing events,
  or configuration problems.
  Trigger with phrases like "sentry not working", "sentry errors missing",
  "fix sentry", "sentry troubleshoot".
allowed-tools: Read, Grep, Bash(npm:*), Bash(node:*), Bash(curl:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, troubleshooting, debugging]

---
# Sentry Common Errors

## Prerequisites
- Sentry SDK installed
- Access to Sentry dashboard
- Application logs available for inspection

## Instructions

### Problem 1: Events Not Appearing in Dashboard

**Diagnostic steps:**
```typescript
// 1. Enable debug mode
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: true, // Prints SDK activity to console
});

// 2. Verify DSN is loaded
console.log('DSN:', process.env.SENTRY_DSN ? 'SET' : 'MISSING');

// 3. Verify client is initialized
const client = Sentry.getClient();
console.log('Client:', client ? 'ACTIVE' : 'NOT INITIALIZED');

// 4. Test network connectivity
// Run: curl -v https://sentry.io/api/0/

// 5. Send a test event and check the return
const eventId = Sentry.captureMessage('Debug test', 'info');
console.log('Event ID:', eventId); // Should be a UUID, not undefined

// 6. Force flush to ensure events are sent
await Sentry.flush(5000);
```

**Common causes:**
- DSN environment variable not loaded (check dotenv config)
- `beforeSend` returning `undefined` instead of `event` or `null`
- `sampleRate: 0` or `tracesSampleRate: 0` dropping everything
- Network proxy blocking `*.ingest.sentry.io`
- SDK initialized after error occurs

### Problem 2: `beforeSend` Silently Dropping Events

```typescript
// WRONG — returns undefined when condition is false, dropping all events
beforeSend(event) {
  if (event.exception) {
    event.tags = { ...event.tags, has_exception: 'true' };
    return event;
  }
  // Missing return! Returns undefined = event dropped
}

// CORRECT — always return event or null
beforeSend(event) {
  if (event.exception) {
    event.tags = { ...event.tags, has_exception: 'true' };
  }
  return event; // Always return the event
}
```

### Problem 3: Source Maps Not Resolving

```bash
# Verify source maps are uploaded for the release
sentry-cli releases files "$VERSION" list

# Use the explain command for a specific event
sentry-cli sourcemaps explain --org $SENTRY_ORG --project $SENTRY_PROJECT EVENT_ID

# Common fixes:
# 1. URL prefix mismatch — check what URL the browser loads your JS from
# 2. Release version mismatch — SDK release must match CLI release
# 3. Source maps uploaded AFTER error occurred — Sentry won't retroactively apply
```

### Problem 4: Express Not Instrumented

```
[Sentry] Express is not instrumented. This is likely because you
required/imported express before calling Sentry.init()
```

**Fix:** Initialize Sentry BEFORE importing express:
```typescript
// CORRECT order
import './instrument.mjs'; // Sentry.init() happens here
import express from 'express';

// Or use Node.js --import flag:
// node --import ./instrument.mjs app.mjs
```

### Problem 5: Duplicate Events

```typescript
// Cause: Error caught at multiple levels
// Fix: Capture at ONE level only

// Option A: Let middleware handle it
app.get('/api', async (req, res, next) => {
  try {
    const data = await getData();
    res.json(data);
  } catch (error) {
    next(error); // Don't captureException here
  }
});

// Sentry.setupExpressErrorHandler(app) captures it once

// Option B: Catch and capture, but don't re-throw
app.get('/api', async (req, res) => {
  try {
    const data = await getData();
    res.json(data);
  } catch (error) {
    Sentry.captureException(error);
    res.status(500).json({ error: 'Internal error' });
    // Don't re-throw — event already captured
  }
});
```

### Problem 6: Missing Stack Traces

```typescript
// WRONG — string has no stack trace
Sentry.captureException('something broke');

// WRONG — rejecting with a string
Promise.reject('auth failed');

// CORRECT — always use Error objects
Sentry.captureException(new Error('something broke'));
Promise.reject(new Error('auth failed'));

// For non-Error values from third-party code:
try {
  thirdPartyLib.call();
} catch (error) {
  if (error instanceof Error) {
    Sentry.captureException(error);
  } else {
    Sentry.captureException(new Error(String(error)));
  }
}
```

### Problem 7: ESM Compatibility Issues

SDK v8 requires Node.js 18.19+ or 20.6+ for ESM:

```bash
# Check Node version
node --version

# If using ESM, must use --import flag
node --import ./instrument.mjs app.mjs

# For CJS, require at top of entry file
# require('./instrument.js');
```

### Problem 8: Rate Limited (429 Errors)

```typescript
// Reduce event volume
Sentry.init({
  sampleRate: 0.5,           // 50% of errors
  tracesSampleRate: 0.01,    // 1% of transactions
  maxBreadcrumbs: 20,        // Default is 100
  ignoreErrors: [
    'ResizeObserver loop',
    'Non-Error promise rejection',
    /Loading chunk \d+ failed/,
  ],
});
```

### Diagnostic Checklist

Run through this when Sentry is not working:

```bash
# 1. Verify SDK version
npm list @sentry/node @sentry/browser 2>/dev/null

# 2. Verify CLI auth
sentry-cli info

# 3. Test network
curl -s https://sentry.io/api/0/ | head -c 100

# 4. Check project rate limits
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$SENTRY_ORG/$SENTRY_PROJECT/stats/"

# 5. List uploaded artifacts for current release
sentry-cli releases files "$VERSION" list 2>/dev/null || echo "No release found"
```

## Output
- Root cause identified from diagnostic checklist
- Configuration fix applied and verified
- Error capture confirmed working with test event
- Debug mode disabled after issue resolution

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid Sentry Dsn` | Malformed DSN string | Re-copy from Project Settings > Client Keys |
| No events in dashboard | `beforeSend` returns undefined | Add explicit `return event` at end of function |
| Minified stack traces | Source maps not uploaded or URL prefix wrong | Run `sentry-cli sourcemaps explain EVENT_ID` |
| 429 Too Many Requests | Quota exceeded | Lower sample rates, add `ignoreErrors`, set project rate limits |
| Express not instrumented | Wrong import order | Initialize Sentry before importing Express |
| ESM errors on startup | Node.js version too old | Upgrade to Node.js 18.19+ or 20.6+ |

## Resources
- [Troubleshooting](https://docs.sentry.io/platforms/javascript/troubleshooting/)
- [Source Maps Troubleshooting](https://docs.sentry.io/platforms/javascript/sourcemaps/troubleshooting_js/)
- [Sentry Status](https://status.sentry.io)
- [Filtering Events](https://docs.sentry.io/platforms/javascript/configuration/filtering/)
