---
name: sentry-upgrade-migration
description: |
  Upgrade Sentry SDK and migrate between versions.
  Use when upgrading Sentry SDK, handling breaking changes,
  or migrating from legacy versions.
  Trigger with phrases like "upgrade sentry", "sentry migration",
  "update sentry sdk", "sentry breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Upgrade & Migration

## Overview
Guide for upgrading Sentry SDK and handling breaking changes.

## Check Current Version

```bash
# Node.js
npm list @sentry/node @sentry/react @sentry/browser

# Python
pip show sentry-sdk

# Check for available updates
npm outdated @sentry/node
```

## Upgrade Process

### Step 1: Review Changelog
```bash
# Check release notes
open https://github.com/getsentry/sentry-javascript/releases

# Or for Python
open https://github.com/getsentry/sentry-python/releases
```

### Step 2: Update Package
```bash
# Update to latest
npm update @sentry/node

# Or specific version
npm install @sentry/node@8.0.0

# Python
pip install --upgrade sentry-sdk
```

### Step 3: Handle Breaking Changes
Review and update code based on migration guide.

## Major Version Migrations

### v7 to v8 (JavaScript)

**Breaking Changes:**

1. **Init Options Renamed**
```typescript
// v7
Sentry.init({
  tracesSampleRate: 1.0,
  replaysOnErrorSampleRate: 1.0,
});

// v8
Sentry.init({
  tracesSampleRate: 1.0,
  replaysOnErrorSampleRate: 1.0, // Same, but check all options
});
```

2. **Removed Integrations**
```typescript
// v7 - Manual integration
import { BrowserTracing } from '@sentry/tracing';

// v8 - Built-in
Sentry.init({
  integrations: [
    Sentry.browserTracingIntegration(), // New API
  ],
});
```

3. **Hub Changes**
```typescript
// v7
const hub = Sentry.getCurrentHub();
hub.captureException(error);

// v8
Sentry.captureException(error);
// Or use scopes
Sentry.withScope((scope) => {
  scope.setTag('key', 'value');
  Sentry.captureException(error);
});
```

### v6 to v7 (JavaScript)

**Breaking Changes:**

1. **Package Structure**
```bash
# v6 - Single package
npm install @sentry/browser

# v7 - Modular packages
npm install @sentry/browser @sentry/tracing
```

2. **Performance API**
```typescript
// v6
Sentry.startTransaction({ name: 'test' });

// v7
const transaction = Sentry.startTransaction({
  name: 'test',
  op: 'task',
});
```

### Python SDK Migration

```python
# v1 to v2 changes
# Old
from sentry_sdk import capture_exception

# New (same, but check integrations)
import sentry_sdk
sentry_sdk.capture_exception(error)

# Integration changes
# Old
from sentry_sdk.integrations.flask import FlaskIntegration

# New (same API, updated internals)
from sentry_sdk.integrations.flask import FlaskIntegration
```

## Migration Checklist

- [ ] Back up current configuration
- [ ] Read release notes for target version
- [ ] Update package in non-production first
- [ ] Run tests to catch breaking changes
- [ ] Update deprecated APIs
- [ ] Verify error capture works
- [ ] Verify performance monitoring works
- [ ] Deploy to staging
- [ ] Monitor for issues
- [ ] Deploy to production

## Testing After Upgrade

```typescript
// test-upgrade.ts
import * as Sentry from '@sentry/node';

async function testUpgrade() {
  console.log('SDK Version:', Sentry.SDK_VERSION);

  // Test error capture
  try {
    throw new Error('Upgrade test error');
  } catch (e) {
    const eventId = Sentry.captureException(e);
    console.log('Error captured:', eventId);
  }

  // Test performance
  const transaction = Sentry.startTransaction({
    name: 'upgrade-test',
    op: 'test',
  });
  transaction.finish();
  console.log('Transaction created');

  // Test breadcrumbs
  Sentry.addBreadcrumb({
    category: 'test',
    message: 'Upgrade verification',
    level: 'info',
  });
  console.log('Breadcrumb added');

  console.log('Upgrade test complete!');
}

testUpgrade();
```

## Rollback Procedure

If upgrade causes issues:

```bash
# Rollback to previous version
npm install @sentry/node@7.x.x

# Or use package-lock.json
git checkout HEAD~1 -- package-lock.json
npm ci
```

## Resources
- [Sentry JavaScript Changelog](https://github.com/getsentry/sentry-javascript/blob/master/CHANGELOG.md)
- [Sentry Python Changelog](https://github.com/getsentry/sentry-python/blob/master/CHANGELOG.md)
- [Migration Guides](https://docs.sentry.io/platforms/javascript/migration/)
