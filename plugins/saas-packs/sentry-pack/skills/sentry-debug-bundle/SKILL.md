---
name: sentry-debug-bundle
description: |
  Collect debug information for Sentry support tickets.
  Use when preparing support requests, debugging complex issues,
  or gathering diagnostic information.
  Trigger with phrases like "sentry debug info", "sentry support ticket",
  "gather sentry diagnostics", "sentry debug bundle".
allowed-tools: Read, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Debug Bundle

## Overview
Collect comprehensive debug information for troubleshooting Sentry issues.

## Debug Information Checklist

### 1. SDK Version and Configuration
```bash
# Get SDK version
npm list @sentry/node @sentry/react @sentry/browser 2>/dev/null

# Or for Python
pip show sentry-sdk
```

### 2. Configuration Export
```typescript
// Create debug config export
const debugConfig = {
  sdkVersion: Sentry.SDK_VERSION,
  dsn: process.env.SENTRY_DSN?.replace(/\/\/(.+?)@/, '//**REDACTED**@'),
  environment: process.env.NODE_ENV,
  release: process.env.SENTRY_RELEASE,
  tracesSampleRate: 0.1,
  sampleRate: 1.0,
};

console.log('Sentry Config:', JSON.stringify(debugConfig, null, 2));
```

### 3. Network Connectivity Test
```bash
# Test Sentry ingest endpoint
curl -v https://sentry.io/api/0/ 2>&1 | head -20

# Test DSN endpoint (replace with your org)
curl -I https://o123456.ingest.sentry.io/api/123456/envelope/
```

### 4. Event Capture Test
```typescript
// Debug event capture
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: true,
  beforeSend(event, hint) {
    console.log('Event being sent:', JSON.stringify(event, null, 2));
    return event;
  },
});

const eventId = Sentry.captureMessage('Debug test message');
console.log('Event ID:', eventId);
```

### 5. Integration Status
```typescript
const client = Sentry.getCurrentHub().getClient();
const integrations = client?.getIntegrations?.() || [];

console.log('Active integrations:', integrations.map(i => i.name));
```

## Debug Script

```typescript
// debug-sentry.ts
import * as Sentry from '@sentry/node';

async function collectDebugInfo() {
  const info = {
    timestamp: new Date().toISOString(),
    nodeVersion: process.version,
    platform: process.platform,
    sdkVersion: Sentry.SDK_VERSION,
    env: {
      NODE_ENV: process.env.NODE_ENV,
      SENTRY_DSN: process.env.SENTRY_DSN ? 'SET' : 'NOT SET',
      SENTRY_RELEASE: process.env.SENTRY_RELEASE || 'NOT SET',
    },
    config: {
      debug: true,
      tracesSampleRate: 'configured',
    },
  };

  // Test capture
  try {
    const eventId = Sentry.captureMessage('Debug bundle test');
    info.testEventId = eventId;
    info.captureStatus = 'SUCCESS';
  } catch (error) {
    info.captureStatus = 'FAILED';
    info.captureError = error.message;
  }

  return info;
}

collectDebugInfo().then(info => {
  console.log('=== SENTRY DEBUG BUNDLE ===');
  console.log(JSON.stringify(info, null, 2));
});
```

## Output Format for Support

```markdown
## Sentry Debug Bundle

**Date:** 2025-01-15
**SDK:** @sentry/node@8.0.0
**Node:** v20.10.0
**Platform:** linux

### Configuration
- DSN: SET (verified format)
- Environment: production
- Release: v1.2.3
- Sample Rate: 1.0
- Traces Sample Rate: 0.1

### Test Results
- Connectivity: OK
- Event Capture: OK (event_id: abc123)
- Source Maps: Uploaded

### Issue Description
[Describe the issue here]

### Steps to Reproduce
1. Step one
2. Step two

### Expected vs Actual Behavior
Expected: ...
Actual: ...

### Relevant Logs
```
[Paste logs here]
```
```

## Common Debug Scenarios

### Events Not Appearing
```bash
# Check if events are being sent
DEBUG=sentry* node app.js

# Or set in code
process.env.DEBUG = 'sentry*';
```

### Source Map Issues
```bash
# List uploaded source maps
sentry-cli releases files $RELEASE list

# Validate source maps
sentry-cli sourcemaps explain $EVENT_ID
```

## Resources
- [Sentry Support](https://sentry.io/support/)
- [Sentry GitHub Issues](https://github.com/getsentry/sentry-javascript/issues)
