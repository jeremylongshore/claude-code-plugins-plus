---
name: sentry-migration-deep-dive
description: |
  Migrate to Sentry from other error tracking tools.
  Use when migrating from Rollbar, Bugsnag, Raygun,
  or other error tracking solutions.
  Trigger with phrases like "migrate to sentry", "sentry migration",
  "switch from rollbar to sentry", "replace bugsnag with sentry".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, migration, rollbar, bugsnag]

---
# Sentry Migration Deep Dive

## Current State
!`npm list 2>/dev/null | grep -iE "sentry|rollbar|bugsnag|raygun|airbrake|honeybadger" || echo 'No error tracking packages found'`

## Prerequisites
- Current error tracking tool access and API credentials
- Sentry project created with DSN
- Parallel run timeline established (2-4 weeks recommended)
- Feature mapping document prepared

## Instructions

### 1. Feature Mapping: Old Tool to Sentry

| Feature | Rollbar | Bugsnag | Sentry Equivalent |
|---------|---------|---------|-------------------|
| Error capture | `Rollbar.error()` | `Bugsnag.notify()` | `Sentry.captureException()` |
| Message | `Rollbar.info()` | `Bugsnag.notify(msg)` | `Sentry.captureMessage()` |
| User context | `Rollbar.configure({person})` | `Bugsnag.setUser()` | `Sentry.setUser()` |
| Tags/metadata | `Rollbar.configure({custom})` | `bugsnag.addMetadata()` | `Sentry.setTag()` / `setContext()` |
| Breadcrumbs | `Rollbar.log()` | `Bugsnag.leaveBreadcrumb()` | `Sentry.addBreadcrumb()` |
| Release | `Rollbar.configure({code_version})` | `Bugsnag.start({appVersion})` | `Sentry.init({release})` |
| Environment | `Rollbar.configure({environment})` | `Bugsnag.start({releaseStage})` | `Sentry.init({environment})` |
| Filtering | `checkIgnore` callback | `onError` callback | `beforeSend` callback |
| Performance | N/A | `@bugsnag/plugin-*` | Built-in `tracesSampleRate` |

### 2. Phase 1 — Parallel Installation

Install Sentry alongside existing tool:

```typescript
// instrument.mjs — Sentry initialization
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.APP_VERSION,
  tracesSampleRate: 0.1,
  sendDefaultPii: false,
});
```

```typescript
// error-handler.ts — dual reporting during migration
import * as Sentry from '@sentry/node';
import Rollbar from 'rollbar'; // or bugsnag, etc.

const rollbar = new Rollbar({ accessToken: process.env.ROLLBAR_TOKEN });

export function captureError(error: Error, context?: Record<string, unknown>) {
  // Report to BOTH during parallel run
  Sentry.withScope((scope) => {
    if (context) scope.setContext('app', context);
    Sentry.captureException(error);
  });

  // Keep old tool running
  rollbar.error(error, context);
}
```

### 3. Phase 2 — Migrate API Calls

**From Rollbar:**
```typescript
// BEFORE: Rollbar
import Rollbar from 'rollbar';
const rollbar = new Rollbar({
  accessToken: process.env.ROLLBAR_TOKEN,
  environment: process.env.NODE_ENV,
  codeVersion: process.env.APP_VERSION,
});
rollbar.error('Payment failed', { orderId: '123' });
rollbar.configure({ person: { id: user.id, email: user.email } });

// AFTER: Sentry
import * as Sentry from '@sentry/node';
Sentry.captureException(new Error('Payment failed'));
Sentry.setContext('order', { orderId: '123' });
Sentry.setUser({ id: user.id });
```

**From Bugsnag:**
```typescript
// BEFORE: Bugsnag
import Bugsnag from '@bugsnag/node';
Bugsnag.start({
  apiKey: process.env.BUGSNAG_KEY,
  releaseStage: process.env.NODE_ENV,
  appVersion: process.env.APP_VERSION,
});
Bugsnag.notify(error, (event) => {
  event.addMetadata('order', { id: orderId });
  event.setUser(user.id, user.email, user.name);
});
Bugsnag.leaveBreadcrumb('User clicked checkout');

// AFTER: Sentry
import * as Sentry from '@sentry/node';
Sentry.withScope((scope) => {
  scope.setContext('order', { id: orderId });
  scope.setUser({ id: user.id });
  Sentry.captureException(error);
});
Sentry.addBreadcrumb({ category: 'ui', message: 'User clicked checkout' });
```

### 4. Phase 3 — Migrate Alert Rules

Map existing alert rules to Sentry:

```
Old tool alerts:
  "New error in production" -> Slack #errors
  "Error rate > 100/min" -> PagerDuty

Sentry alert rules:
  Issue Alert: "A new issue is created"
    Filter: environment:production
    Action: Send Slack notification to #errors

  Metric Alert: "Error count > 100 in 1 minute"
    Filter: environment:production
    Action: Send PagerDuty notification
    Resolve: When < 10 for 5 minutes
```

### 5. Phase 4 — Validate Parity

Compare error capture between tools during parallel run:

```bash
# Compare error counts between old tool and Sentry
# Old tool API (Rollbar example):
curl -H "X-Rollbar-Access-Token: $ROLLBAR_TOKEN" \
  "https://api.rollbar.com/api/1/reports/top_recent_items"

# Sentry API:
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$SENTRY_ORG/$SENTRY_PROJECT/stats/"
```

**Parity checklist:**
- [ ] Error count within 10% between tools
- [ ] Stack traces resolve correctly (source maps)
- [ ] User context appears in Sentry events
- [ ] Breadcrumbs appear in event detail
- [ ] Alert rules fire correctly
- [ ] Release tracking shows deploy markers
- [ ] Performance data appears (if using tracing)

### 6. Phase 5 — Remove Old Tool

```bash
# Remove old SDK
npm uninstall rollbar          # or @bugsnag/node, raygun4js, etc.
npm uninstall @bugsnag/node
npm uninstall @bugsnag/plugin-express

# Remove old configuration
rm rollbar.js                   # or bugsnag.js
# Remove old env vars from .env, CI secrets

# Search for remaining references
grep -r "rollbar\|bugsnag\|raygun\|airbrake" \
  --include="*.ts" --include="*.js" --include="*.env*" \
  --exclude-dir=node_modules src/
```

### 7. Post-Migration Verification

```typescript
// Full verification after removing old tool
import * as Sentry from '@sentry/node';

async function verifyMigration() {
  // Error capture
  const errorId = Sentry.captureException(new Error('Migration verification'));
  console.log('Error captured:', errorId ? 'PASS' : 'FAIL');

  // Message capture
  Sentry.captureMessage('Migration complete', 'info');

  // Performance span
  await Sentry.startSpan({ name: 'migration.verify', op: 'test' }, async () => {
    await new Promise(r => setTimeout(r, 100));
  });

  // Flush
  const flushed = await Sentry.flush(5000);
  console.log('All events sent:', flushed ? 'PASS' : 'FAIL');
}

verifyMigration();
```

## Migration Timeline

```
Week 1:   Install Sentry alongside old tool, configure SDK
Week 2:   Migrate all captureException/notify calls to dual-report
Week 3:   Verify parity, migrate alert rules
Week 4:   Remove old tool, verify Sentry-only operation
Week 5:   Cancel old tool subscription, close migration
```

## Output
- Sentry SDK installed and configured as primary error tracker
- Feature mapping document translating old API to Sentry API
- Alert rules migrated and verified
- Parallel run validated error capture parity
- Old SDK removed and references cleaned up

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Error count mismatch | Different sampling rates | Align `sampleRate` with old tool's settings during comparison |
| Missing stack traces | Source maps not uploaded to Sentry | Set up `sentry-cli sourcemaps upload` in CI |
| Old tool references remain | Incomplete code cleanup | Run grep for old tool names across entire codebase |
| Alert rules not matching | Different alert logic | Re-test alert conditions with synthetic errors |

## Resources
- [SDK Documentation](https://docs.sentry.io/platforms/)
- [Migration Guide](https://docs.sentry.io/product/accounts/migration/)
- [Sentry vs Rollbar](https://sentry.io/vs/rollbar/)
- [Sentry vs Bugsnag](https://sentry.io/vs/bugsnag/)
