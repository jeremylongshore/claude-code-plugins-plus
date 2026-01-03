---
name: sentry-prod-checklist
description: |
  Production deployment checklist for Sentry integration.
  Use when preparing for production deployment, reviewing
  Sentry configuration, or verifying production readiness.
  Trigger with phrases like "sentry production", "deploy sentry",
  "sentry checklist", "sentry go-live".
allowed-tools: Read, Grep, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Production Checklist

## Overview
Ensure your Sentry integration is production-ready.

## Pre-Deployment Checklist

### 1. Configuration
- [ ] Production DSN configured (separate from dev/staging)
- [ ] Environment set to "production"
- [ ] Release version configured
- [ ] Sample rates tuned for production volume

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: 'production',
  release: `${APP_NAME}@${APP_VERSION}`,
  tracesSampleRate: 0.1, // 10% in production
  sampleRate: 1.0, // Capture all errors
});
```

### 2. Source Maps
- [ ] Source maps generated during build
- [ ] Source maps uploaded to Sentry
- [ ] Release created and finalized

```bash
# Build process
npm run build

# Upload source maps
export SENTRY_ORG=your-org
export SENTRY_PROJECT=your-project
export SENTRY_AUTH_TOKEN=your-token
export VERSION=$(git rev-parse --short HEAD)

sentry-cli releases new $VERSION
sentry-cli releases files $VERSION upload-sourcemaps ./dist
sentry-cli releases finalize $VERSION
```

### 3. Security
- [ ] DSN in environment variables (not hardcoded)
- [ ] `sendDefaultPii: false` in production
- [ ] Data scrubbing configured
- [ ] Debug mode disabled

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: false, // MUST be false in production
  sendDefaultPii: false,
});
```

### 4. Performance
- [ ] Performance monitoring enabled
- [ ] Appropriate sample rates set
- [ ] Key transactions identified

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
  tracesSampler: (ctx) => {
    // Always trace critical transactions
    if (ctx.transactionContext.name.includes('checkout')) return 1.0;
    if (ctx.transactionContext.name.includes('payment')) return 1.0;
    return 0.1;
  },
});
```

### 5. Alerting
- [ ] Alert rules configured
- [ ] Team notifications set up
- [ ] On-call integration (PagerDuty/Slack)
- [ ] Issue assignment rules defined

### 6. Integrations
- [ ] Source control (GitHub/GitLab) connected
- [ ] CI/CD integration configured
- [ ] Slack/Teams notifications
- [ ] Issue tracker (Jira/Linear) linked

## Verification Steps

### Test Error Capture
```typescript
// Test script to verify production setup
async function verifySentry() {
  const eventId = Sentry.captureMessage('Production verification test', {
    level: 'info',
    tags: { test: 'production-verify' },
  });

  console.log(`Test event sent: ${eventId}`);
  console.log('Check Sentry dashboard for this event');
}
```

### Verify Source Maps
```bash
# After deploying, verify source maps work
sentry-cli releases list
sentry-cli releases files $VERSION list

# Test with a real error
# Stack trace should show original source, not minified
```

### Check Connectivity
```bash
# Verify Sentry is reachable from production
curl -I https://sentry.io/api/0/

# Check DSN endpoint
curl -I "https://o123456.ingest.sentry.io/api/123456/envelope/"
```

## Production Configuration Template

```typescript
// sentry.config.ts
import * as Sentry from '@sentry/node';

const isProduction = process.env.NODE_ENV === 'production';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.SENTRY_RELEASE || process.env.npm_package_version,

  // Production settings
  debug: !isProduction,
  sendDefaultPii: false,
  attachStacktrace: true,

  // Sampling
  sampleRate: 1.0,
  tracesSampleRate: isProduction ? 0.1 : 1.0,

  // Filtering
  ignoreErrors: [
    'ResizeObserver loop',
    'Network request failed',
  ],

  // Performance
  integrations: [
    new Sentry.Integrations.Http({ tracing: true }),
  ],
});

export default Sentry;
```

## Rollback Plan

If issues occur after deployment:

1. **Disable Sentry temporarily:**
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  enabled: false, // Quick disable
});
```

2. **Reduce sample rate:**
```typescript
sampleRate: 0.1, // Reduce load
tracesSampleRate: 0.01,
```

3. **Check Sentry status:**
```bash
curl https://status.sentry.io/api/v2/status.json
```

## Resources
- [Sentry Production Checklist](https://docs.sentry.io/product/releases/setup/)
- [Sentry Release Health](https://docs.sentry.io/product/releases/health/)
