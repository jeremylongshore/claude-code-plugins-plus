---
name: sentry-migration-deep-dive
description: |
  Migrate to Sentry from other error tracking tools.
  Use when migrating from Rollbar, Bugsnag, Raygun,
  or other error tracking solutions.
  Trigger with phrases like "migrate to sentry", "sentry migration",
  "switch from rollbar to sentry", "replace bugsnag with sentry".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Migration Deep Dive

## Overview
Comprehensive guide to migrating from other error tracking tools to Sentry.

## Migration Planning

### Phase 1: Assessment
```
□ Inventory current error tracking usage
□ List all projects/services using old tool
□ Document current alert configurations
□ Export historical data (if needed)
□ Identify team members and permissions
```

### Phase 2: Parallel Running
```
□ Set up Sentry projects
□ Install Sentry SDK alongside existing
□ Run both tools in parallel (2-4 weeks)
□ Compare error capture rates
□ Validate alert parity
```

### Phase 3: Cutover
```
□ Disable old tool SDK
□ Remove old tool dependencies
□ Update documentation
□ Train team on Sentry
□ Cancel old tool subscription
```

## Migration from Rollbar

### SDK Replacement
```typescript
// Before: Rollbar
import Rollbar from 'rollbar';
const rollbar = new Rollbar({
  accessToken: 'ROLLBAR_TOKEN',
  environment: process.env.NODE_ENV,
});
rollbar.error('Something went wrong', error);

// After: Sentry
import * as Sentry from '@sentry/node';
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
});
Sentry.captureException(error);
```

### Feature Mapping: Rollbar → Sentry
| Rollbar | Sentry |
|---------|--------|
| `rollbar.error()` | `Sentry.captureException()` |
| `rollbar.warning()` | `Sentry.captureMessage(..., 'warning')` |
| `rollbar.info()` | `Sentry.captureMessage(..., 'info')` |
| `rollbar.configure({ payload: {} })` | `Sentry.setContext()` |
| `rollbar.configure({ person: {} })` | `Sentry.setUser()` |
| Custom fingerprinting | `Sentry.withScope()` + fingerprint |

### Express Middleware Migration
```typescript
// Before: Rollbar
app.use(rollbar.errorHandler());

// After: Sentry
import * as Sentry from '@sentry/node';
Sentry.init({ dsn: process.env.SENTRY_DSN });
app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.errorHandler());
```

## Migration from Bugsnag

### SDK Replacement
```typescript
// Before: Bugsnag
import Bugsnag from '@bugsnag/js';
Bugsnag.start({ apiKey: 'BUGSNAG_KEY' });
Bugsnag.notify(error);

// After: Sentry
import * as Sentry from '@sentry/browser';
Sentry.init({ dsn: process.env.SENTRY_DSN });
Sentry.captureException(error);
```

### Feature Mapping: Bugsnag → Sentry
| Bugsnag | Sentry |
|---------|--------|
| `Bugsnag.notify()` | `Sentry.captureException()` |
| `Bugsnag.leaveBreadcrumb()` | `Sentry.addBreadcrumb()` |
| `Bugsnag.setUser()` | `Sentry.setUser()` |
| `Bugsnag.addMetadata()` | `Sentry.setContext()` |
| `onError` callback | `beforeSend` hook |

### React Integration Migration
```typescript
// Before: Bugsnag React
import Bugsnag from '@bugsnag/js';
import BugsnagPluginReact from '@bugsnag/plugin-react';
Bugsnag.start({ plugins: [new BugsnagPluginReact()] });
const ErrorBoundary = Bugsnag.getPlugin('react').createErrorBoundary(React);

// After: Sentry React
import * as Sentry from '@sentry/react';
Sentry.init({ dsn: process.env.SENTRY_DSN });
// Use Sentry.ErrorBoundary component
<Sentry.ErrorBoundary fallback={<ErrorFallback />}>
  <App />
</Sentry.ErrorBoundary>
```

## Migration from Raygun

### SDK Replacement
```typescript
// Before: Raygun
import raygun from 'raygun';
const client = new raygun.Client().init({ apiKey: 'RAYGUN_KEY' });
client.send(error);

// After: Sentry
import * as Sentry from '@sentry/node';
Sentry.init({ dsn: process.env.SENTRY_DSN });
Sentry.captureException(error);
```

### Feature Mapping: Raygun → Sentry
| Raygun | Sentry |
|--------|--------|
| `client.send()` | `Sentry.captureException()` |
| `client.setUser()` | `Sentry.setUser()` |
| `client.setVersion()` | `Sentry.init({ release })` |
| Custom data | `Sentry.setContext()` |
| Tags | `Sentry.setTag()` |

## Migration from NewRelic Errors

### SDK Addition (NewRelic → Sentry)
```typescript
// Keep NewRelic for APM, add Sentry for errors
import newrelic from 'newrelic';
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  beforeSend(event) {
    // Correlate with NewRelic
    event.tags = {
      ...event.tags,
      newrelic_transaction: newrelic.getTransaction()?.name,
    };
    return event;
  },
});

// Replace: newrelic.noticeError(error)
// With: Sentry.captureException(error)
```

## Data Migration

### Export Historical Data
Most tools don't support direct export. Options:
1. Keep read-only access to old tool
2. Export via API to archive
3. Screenshot/document important issues

### API Export Script
```typescript
// Export issues from Rollbar (example)
async function exportRollbarItems() {
  const response = await fetch(
    'https://api.rollbar.com/api/1/items',
    {
      headers: { 'X-Rollbar-Access-Token': ROLLBAR_TOKEN },
    }
  );
  const data = await response.json();

  // Save to file for reference
  fs.writeFileSync(
    'rollbar-export.json',
    JSON.stringify(data, null, 2)
  );
}
```

## Alert Migration

### Map Alert Rules
```yaml
# Old tool alert
name: "High Error Rate"
condition: error_rate > 10%
action: email oncall@company.com

# Sentry equivalent
- name: "High Error Rate"
  conditions:
    - type: event_frequency
      value: 100
      interval: 1h
  actions:
    - type: notify_email
      targetIdentifier: oncall@company.com
```

### Recreate Integrations
```
□ Slack integration
□ PagerDuty integration
□ Jira integration
□ GitHub integration
□ Custom webhooks
```

## Testing Migration

### Validation Checklist
```
□ Test error capture in all environments
□ Verify source maps work
□ Test user context capture
□ Verify breadcrumbs
□ Test alert triggering
□ Compare error grouping
□ Validate performance data (if used)
```

### Parallel Comparison Script
```typescript
// Capture in both during migration
function captureError(error: Error, context: object) {
  // Old tool
  rollbar.error(error, context);

  // New tool
  Sentry.withScope((scope) => {
    scope.setContext('migration', context);
    Sentry.captureException(error);
  });
}
```

## Cleanup

### Remove Old Dependencies
```bash
# Node.js
npm uninstall rollbar @bugsnag/js raygun

# Python
pip uninstall rollbar bugsnag raygun4py
```

### Remove Old Configuration
```bash
# Delete old config files
rm .rollbar.yml
rm bugsnag.config.js

# Remove environment variables
unset ROLLBAR_ACCESS_TOKEN
unset BUGSNAG_API_KEY
```

## Resources
- [Sentry Migration Guide](https://docs.sentry.io/product/accounts/migration/)
- [SDK Documentation](https://docs.sentry.io/platforms/)
