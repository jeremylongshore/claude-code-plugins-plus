---
name: sentry-advanced-troubleshooting
description: |
  Advanced Sentry troubleshooting techniques.
  Use when debugging complex SDK issues, missing events,
  source map problems, or performance anomalies.
  Trigger with phrases like "sentry not working", "debug sentry",
  "sentry events missing", "fix sentry issues".
allowed-tools: Read, Write, Edit, Grep, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Advanced Troubleshooting

## Overview
Diagnose and resolve complex Sentry SDK and configuration issues.

## Events Not Appearing

### Check 1: SDK Initialization
```typescript
// Verify SDK is initialized
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: true, // Enable debug logging
});

// Check if client exists
const client = Sentry.getCurrentHub().getClient();
console.log('Sentry client initialized:', !!client);
console.log('DSN:', client?.getDsn()?.toString());
```

### Check 2: Network Issues
```typescript
// Test network connectivity
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Add transport debugging
  beforeSend(event) {
    console.log('Sending event:', event.event_id);
    return event;
  },

  // Capture transport errors
  transport: (options) => {
    const transport = Sentry.makeNodeTransport(options);
    return {
      ...transport,
      send: async (request) => {
        try {
          const result = await transport.send(request);
          console.log('Transport success');
          return result;
        } catch (error) {
          console.error('Transport error:', error);
          throw error;
        }
      },
    };
  },
});
```

### Check 3: Sampling Configuration
```typescript
// Verify sample rates
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Check these aren't too low
  sampleRate: 1.0, // 100% of errors (for debugging)
  tracesSampleRate: 1.0, // 100% of transactions

  // Check sampler isn't dropping events
  tracesSampler: (ctx) => {
    console.log('Sampling context:', ctx);
    return 1.0; // Force sampling for debug
  },
});
```

### Check 4: beforeSend Filtering
```typescript
// Temporarily disable filtering
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  beforeSend(event, hint) {
    console.log('beforeSend called:', event.message);
    // Return event always (don't filter during debug)
    return event;
  },
});
```

## Source Maps Not Working

### Verify Upload
```bash
# Check if source maps are uploaded
sentry-cli releases files $VERSION list

# Expected output:
# ~/static/js/main.js
# ~/static/js/main.js.map
```

### Check URL Prefix
```typescript
// Browser URL: https://example.com/static/js/main.js
// Source map should be: ~/static/js/main.js.map

// Upload with correct prefix
sentry-cli releases files $VERSION upload-sourcemaps ./dist \
  --url-prefix "~/static/js"
```

### Debug Source Map Resolution
```bash
# Validate source map
sentry-cli sourcemaps explain $EVENT_ID

# This shows:
# - What URL Sentry is looking for
# - What files are uploaded
# - Why mapping failed
```

### Common Source Map Issues
```yaml
Issue: Minified stack traces
Fix: Verify source maps uploaded with correct release

Issue: "Could not find source map"
Fix: Check url-prefix matches actual URLs

Issue: Wrong line numbers
Fix: Ensure source maps are from same build

Issue: "Source code not found"
Fix: Upload source files along with maps
```

## Performance Data Missing

### Check Transaction Creation
```typescript
// Verify transactions are being created
const transaction = Sentry.startTransaction({
  name: 'test-transaction',
  op: 'test',
});

console.log('Transaction created:', transaction.traceId);

// Don't forget to finish!
transaction.finish();
console.log('Transaction finished');
```

### Check Trace Sampling
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Ensure traces are sampled
  tracesSampleRate: 1.0,

  // Or debug sampler
  tracesSampler: (ctx) => {
    console.log('Trace sampler called:', ctx.transactionContext);
    return 1.0;
  },
});
```

### Verify Integration Setup
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0,

  integrations: [
    // HTTP tracing
    new Sentry.Integrations.Http({ tracing: true }),

    // Express tracing
    new Sentry.Integrations.Express({ app }),
  ],
});

// Verify integrations loaded
const client = Sentry.getCurrentHub().getClient();
console.log('Integrations:', client?.getIntegration);
```

## Breadcrumbs Issues

### Debug Breadcrumb Capture
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Increase breadcrumb limit for debugging
  maxBreadcrumbs: 100,

  beforeBreadcrumb(breadcrumb, hint) {
    console.log('Breadcrumb:', breadcrumb.category, breadcrumb.message);
    return breadcrumb;
  },
});
```

### Manual Breadcrumb Test
```typescript
// Add test breadcrumb
Sentry.addBreadcrumb({
  category: 'test',
  message: 'Test breadcrumb',
  level: 'info',
});

// Capture error to see breadcrumbs
Sentry.captureMessage('Test message');

// Check Sentry dashboard for breadcrumbs
```

## SDK Conflicts

### Multiple SDK Instances
```typescript
// Problem: Multiple init() calls
// Solution: Check for existing client
if (!Sentry.getCurrentHub().getClient()) {
  Sentry.init({ dsn: process.env.SENTRY_DSN });
}
```

### Version Mismatches
```bash
# Check all Sentry package versions
npm list | grep sentry

# All packages should be same major version
# @sentry/node@7.x.x
# @sentry/tracing@7.x.x  # Same major version
```

### Framework Integration Conflicts
```typescript
// Example: Next.js conflicts
// Use framework-specific SDK
import * as Sentry from '@sentry/nextjs'; // Not @sentry/node

// Configure in next.config.js
const { withSentryConfig } = require('@sentry/nextjs');
module.exports = withSentryConfig(nextConfig);
```

## Rate Limiting Diagnosis

### Check Quota Status
```bash
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$ORG/stats/v2/?field=sum(quantity)&category=error"
```

### Detect Client-Side Rate Limiting
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Monitor for rate limit responses
  transport: (options) => {
    const transport = Sentry.makeNodeTransport(options);
    return {
      ...transport,
      send: async (request) => {
        const result = await transport.send(request);
        if (result.statusCode === 429) {
          console.error('Rate limited by Sentry!');
        }
        return result;
      },
    };
  },
});
```

## Diagnostic Script

```typescript
// diagnostic.ts - Run to check Sentry health
import * as Sentry from '@sentry/node';

async function runDiagnostics() {
  console.log('=== Sentry Diagnostics ===\n');

  // Check 1: Environment
  console.log('1. Environment');
  console.log('   DSN set:', !!process.env.SENTRY_DSN);
  console.log('   Environment:', process.env.NODE_ENV);

  // Check 2: Client
  const client = Sentry.getCurrentHub().getClient();
  console.log('\n2. Client');
  console.log('   Initialized:', !!client);
  console.log('   DSN:', client?.getDsn()?.toString() || 'N/A');

  // Check 3: Test capture
  console.log('\n3. Test Capture');
  const eventId = Sentry.captureMessage('Diagnostic test');
  console.log('   Event ID:', eventId);

  // Check 4: Flush
  console.log('\n4. Flushing...');
  const flushed = await Sentry.flush(5000);
  console.log('   Flushed:', flushed);

  console.log('\n=== Complete ===');
}

runDiagnostics();
```

## Resources
- [Sentry Troubleshooting](https://docs.sentry.io/platforms/javascript/troubleshooting/)
- [Source Maps Troubleshooting](https://docs.sentry.io/platforms/javascript/sourcemaps/troubleshooting/)
