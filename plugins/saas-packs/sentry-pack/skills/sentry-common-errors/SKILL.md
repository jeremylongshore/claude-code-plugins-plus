---
name: sentry-common-errors
description: |
  Troubleshoot common Sentry integration issues and fixes.
  Use when encountering Sentry errors, missing events,
  or configuration problems.
  Trigger with phrases like "sentry not working", "sentry errors missing",
  "fix sentry", "sentry troubleshoot".
allowed-tools: Read, Grep, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Common Errors

## Overview
Quick fixes for the most common Sentry integration issues.

## Common Issues and Solutions

### Issue 1: Events Not Appearing in Dashboard
**Symptoms:** Errors captured but not visible in Sentry

**Causes & Solutions:**
```typescript
// 1. DSN not configured
Sentry.init({
  dsn: process.env.SENTRY_DSN, // Ensure this is set
});

// 2. SDK not enabled
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  enabled: true, // Default is true, but check this
});

// 3. Events filtered by beforeSend
beforeSend(event) {
  console.log('Event:', event); // Debug to see if events reach here
  return event; // Ensure you return the event
}

// 4. Rate limited - check dashboard quota
// Visit: https://sentry.io/settings/organization/rate-limits/
```

### Issue 2: Source Maps Not Working
**Symptoms:** Stack traces show minified code

**Solutions:**
```bash
# Install Sentry CLI
npm install @sentry/cli --save-dev

# Upload source maps during build
sentry-cli releases new $RELEASE
sentry-cli releases files $RELEASE upload-sourcemaps ./dist
sentry-cli releases finalize $RELEASE
```

```typescript
// Ensure release matches
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  release: process.env.SENTRY_RELEASE, // Must match uploaded release
});
```

### Issue 3: Missing User Context
**Symptoms:** Events show "Unknown User"

**Solution:**
```typescript
// Set user context after authentication
Sentry.setUser({
  id: user.id,
  email: user.email,
  username: user.username,
});

// Clear on logout
Sentry.setUser(null);
```

### Issue 4: Too Many Events (Rate Limited)
**Symptoms:** 429 errors, events dropped

**Solutions:**
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Sample errors
  sampleRate: 0.5, // Only send 50% of errors

  // Ignore specific errors
  ignoreErrors: [
    'ResizeObserver loop limit exceeded',
    'Network request failed',
  ],

  // Filter events
  beforeSend(event) {
    if (event.exception?.values?.[0]?.type === 'ChunkLoadError') {
      return null; // Don't send
    }
    return event;
  },
});
```

### Issue 5: Missing Breadcrumbs
**Symptoms:** No context trail in error events

**Solution:**
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  integrations: [
    new Sentry.Integrations.Breadcrumbs({
      console: true,
      dom: true,
      fetch: true,
      xhr: true,
    }),
  ],
  maxBreadcrumbs: 50, // Increase if needed
});
```

### Issue 6: Performance Data Missing
**Symptoms:** No transactions in Performance tab

**Solution:**
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1, // Must be > 0 for performance
  integrations: [
    new Sentry.Integrations.Http({ tracing: true }),
  ],
});
```

## Diagnostic Commands

```bash
# Check Sentry connectivity
curl -I https://sentry.io

# Verify DSN format
echo $SENTRY_DSN | grep -E "https://[a-f0-9]+@[a-z]+\.ingest\.sentry\.io/[0-9]+"

# Check SDK version
npm list @sentry/node

# Test error capture
node -e "require('@sentry/node').captureMessage('Test')"
```

## Debug Mode

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: true, // Enable verbose logging
});
```

## Resources
- [Sentry Troubleshooting](https://docs.sentry.io/platforms/javascript/troubleshooting/)
- [Sentry Status](https://status.sentry.io)
