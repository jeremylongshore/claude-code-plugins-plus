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
---

# Sentry Hello World

## Overview
Capture your first error and verify Sentry integration is working correctly.

## Prerequisites
- Sentry SDK installed and initialized
- Valid DSN configured
- Network access to Sentry servers

## Instructions

### Step 1: Capture Test Error
```typescript
import * as Sentry from '@sentry/node';

try {
  throw new Error('Hello Sentry! This is a test error.');
} catch (error) {
  Sentry.captureException(error);
  console.log('Error sent to Sentry');
}
```

### Step 2: Capture Test Message
```typescript
Sentry.captureMessage('Hello from Sentry SDK!', 'info');
```

### Step 3: Verify in Dashboard
1. Open https://sentry.io
2. Navigate to your project
3. Check Issues tab for the test error
4. Verify event details are correct

### Step 4: Add Context
```typescript
Sentry.setUser({ id: 'test-user', email: 'test@example.com' });
Sentry.setTag('test_run', 'hello-world');
Sentry.captureMessage('Test with context');
```

## Output
- Test error visible in Sentry dashboard
- Event contains stack trace and metadata
- User context and tags attached to event

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Event not appearing | DSN misconfigured | Verify DSN in project settings |
| Delayed events | Network latency | Wait 30-60 seconds, check again |
| Missing stack trace | Source maps not uploaded | Configure source map uploads |
| No user context | setUser not called | Add Sentry.setUser() before capture |

## Examples

### Full Test Script (TypeScript)
```typescript
import * as Sentry from '@sentry/node';

Sentry.init({ dsn: process.env.SENTRY_DSN });

// Set user context
Sentry.setUser({ id: '123', email: 'test@example.com' });

// Set tags
Sentry.setTag('environment', 'test');
Sentry.setTag('version', '1.0.0');

// Capture different event types
Sentry.captureMessage('Info message', 'info');
Sentry.captureMessage('Warning message', 'warning');

try {
  throw new Error('Test exception');
} catch (e) {
  Sentry.captureException(e);
}

console.log('Events sent - check Sentry dashboard');
```

### Python Test Script
```python
import sentry_sdk

sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))

sentry_sdk.set_user({'id': '123', 'email': 'test@example.com'})
sentry_sdk.set_tag('environment', 'test')

sentry_sdk.capture_message('Hello from Python!')

try:
    raise ValueError('Test exception from Python')
except Exception as e:
    sentry_sdk.capture_exception(e)
```

## Resources
- [Sentry Error Capture](https://docs.sentry.io/platforms/javascript/usage/)
- [Sentry Context](https://docs.sentry.io/platforms/javascript/enriching-events/context/)

## Next Steps
Proceed to `sentry-local-dev-loop` to set up your development workflow.
