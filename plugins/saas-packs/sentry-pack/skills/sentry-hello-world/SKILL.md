---
name: sentry-hello-world
description: |
  Capture your first error with Sentry and verify it appears in the dashboard.
  Use when testing Sentry integration or verifying error capture works.
  Trigger with phrases like "test sentry", "sentry hello world",
  "verify sentry", "first sentry error".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(python:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, testing, dashboard, quickstart]

---
# Sentry Hello World

## Prerequisites
- Sentry SDK installed and initialized (see `sentry-install-auth`)
- Valid DSN configured in environment variables
- Network access to `*.ingest.sentry.io`

## Instructions

### 1. Verify SDK Is Initialized

Before sending test events, confirm the SDK loaded:

```typescript
import * as Sentry from '@sentry/node';

// Check SDK is active
const client = Sentry.getClient();
if (!client) {
  console.error('Sentry SDK not initialized — check instrument.mjs');
  process.exit(1);
}
console.log('Sentry SDK active, DSN configured');
```

### 2. Send a Test Exception

```typescript
try {
  throw new Error('Hello Sentry! This is a test error.');
} catch (error) {
  const eventId = Sentry.captureException(error);
  console.log(`Exception sent to Sentry — Event ID: ${eventId}`);
}
```

### 3. Send a Test Message

```typescript
Sentry.captureMessage('Hello from Sentry SDK!', 'info');
Sentry.captureMessage('Warning test message', 'warning');
```

### 4. Add User Context and Tags

```typescript
Sentry.setUser({
  id: 'test-user-001',
  email: 'dev@example.com',
  username: 'developer',
});

Sentry.setTag('test_run', 'hello-world');
Sentry.setTag('team', 'platform');

Sentry.setContext('test_metadata', {
  ran_at: new Date().toISOString(),
  node_version: process.version,
});

Sentry.captureMessage('Test with full context attached');
```

### 5. Add Breadcrumbs

```typescript
Sentry.addBreadcrumb({
  category: 'test',
  message: 'User clicked the submit button',
  level: 'info',
});

Sentry.addBreadcrumb({
  category: 'http',
  message: 'GET /api/users returned 200',
  level: 'info',
  data: { status_code: 200, url: '/api/users' },
});

// This error will include the breadcrumbs above
try {
  throw new Error('Error with breadcrumb trail');
} catch (error) {
  Sentry.captureException(error);
}
```

### 6. Flush and Verify

```typescript
// Ensure all events are sent before process exits
await Sentry.flush(5000);
console.log('All events flushed — check Sentry dashboard');
```

### 7. Verify in Dashboard

1. Open https://sentry.io and navigate to your project
2. Click the **Issues** tab — test errors appear as issues
3. Click an issue to see event details:
   - Stack trace pointing to correct file and line
   - User context (id, email, username)
   - Tags (test_run, team)
   - Breadcrumb trail showing events before the error
   - Custom context under "Additional Data"
4. Confirm environment tag matches your `SENTRY_ENVIRONMENT`
5. Confirm release matches your `SENTRY_RELEASE`

### Python Equivalent

```python
import sentry_sdk

sentry_sdk.set_user({"id": "test-001", "email": "dev@example.com"})
sentry_sdk.set_tag("test_run", "hello-world")

sentry_sdk.capture_message("Hello from Python SDK!")

try:
    raise ValueError("Test exception from Python")
except Exception as e:
    sentry_sdk.capture_exception(e)

sentry_sdk.flush()
```

## Complete Test Script

```typescript
// test-sentry.mjs — run with: node --import ./instrument.mjs test-sentry.mjs
import * as Sentry from '@sentry/node';

async function main() {
  Sentry.setUser({ id: 'test-001', email: 'dev@example.com' });
  Sentry.setTag('test_run', 'hello-world');
  Sentry.setTag('environment', process.env.SENTRY_ENVIRONMENT || 'test');

  // Capture message
  Sentry.captureMessage('Hello Sentry — SDK verification', 'info');

  // Capture exception with breadcrumbs
  Sentry.addBreadcrumb({ category: 'test', message: 'Starting verification' });

  try {
    throw new Error('Hello Sentry! Verification test error.');
  } catch (error) {
    const eventId = Sentry.captureException(error);
    console.log(`Event captured: ${eventId}`);
  }

  await Sentry.flush(5000);
  console.log('Verification complete — check Sentry dashboard');
}

main();
```

## Output
- Test error visible in Sentry dashboard within 30 seconds
- Event contains full stack trace pointing to correct source line
- User context, release tag, and environment label attached to event
- Breadcrumb trail visible in event detail view
- Event ID printed to console for cross-referencing

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Event not appearing | DSN misconfigured or env var not loaded | Log `process.env.SENTRY_DSN` to verify, re-copy from project settings |
| `getClient()` returns undefined | SDK not initialized before test code | Use `--import ./instrument.mjs` flag or import instrument first |
| Missing stack trace | Error captured as string, not Error object | Always pass `new Error()` to `captureException`, never a bare string |
| No user context | `setUser` called after `captureException` | Call `setUser` before capturing events |
| Events delayed > 60 seconds | Network or proxy blocking `ingest.sentry.io` | Check firewall rules; try `curl https://sentry.io/api/0/` |

## Resources
- [Capturing Errors](https://docs.sentry.io/platforms/javascript/usage/)
- [Enriching Events](https://docs.sentry.io/platforms/javascript/enriching-events/)
- [Breadcrumbs](https://docs.sentry.io/platforms/javascript/enriching-events/breadcrumbs/)
