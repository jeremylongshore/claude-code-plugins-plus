---
name: sentry-upgrade-migration
description: |
  Upgrade Sentry SDK and migrate between versions.
  Use when upgrading Sentry SDK, handling breaking changes,
  or migrating from legacy versions.
  Trigger with phrases like "upgrade sentry", "sentry migration",
  "update sentry sdk", "sentry breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, migration, upgrade, sdk]

---
# Sentry Upgrade Migration

## Current State
!`npm list 2>/dev/null | grep @sentry || echo 'No Sentry packages found'`
!`node --version 2>/dev/null || echo 'N/A'`

## Prerequisites
- Current Sentry SDK version identified
- Target version changelog reviewed
- Non-production environment for testing
- Test suite for error capture and performance monitoring

## Instructions

### 1. Identify Current Version

```bash
# Check installed Sentry packages
npm list | grep @sentry

# Verify all packages are the same version (critical!)
npm list 2>/dev/null | grep "@sentry/" | sort
```

### 2. v7 to v8 Migration (Major Breaking Changes)

This is the most common migration. Key changes:

**Run the automated migration tool first:**
```bash
# Step 1: Upgrade to latest v7 first
npm install @sentry/node@7

# Step 2: Run the migration codemod
npx @sentry/migr8@latest
# This automatically updates deprecated APIs in your code

# Step 3: Upgrade to v8
npm install @sentry/node@8
```

**Breaking Change 1: Integrations are functions, not classes**
```typescript
// v7 (OLD)
import * as Sentry from '@sentry/node';
Sentry.init({
  integrations: [new Sentry.Integrations.Http({ tracing: true })],
});

// v8 (NEW) — integrations are now functions
Sentry.init({
  integrations: [
    // Most integrations are auto-enabled, no need to list them
    // Only add if you need to configure:
    Sentry.httpIntegration({ tracing: true }),
  ],
});
```

**Breaking Change 2: Hub is replaced by Scope API**
```typescript
// v7 (OLD)
const hub = Sentry.getCurrentHub();
hub.configureScope((scope) => {
  scope.setTag('key', 'value');
});
const transaction = hub.startTransaction({ name: 'my-tx' });

// v8 (NEW)
Sentry.withScope((scope) => {
  scope.setTag('key', 'value');
});
// Use startSpan instead of startTransaction
Sentry.startSpan({ name: 'my-tx', op: 'custom' }, (span) => {
  // ... your code
});
```

**Breaking Change 3: Transaction/Span API replaced**
```typescript
// v7 (OLD)
const transaction = Sentry.startTransaction({ name: 'process', op: 'task' });
const span = transaction.startChild({ op: 'db.query', description: 'SELECT' });
span.finish();
transaction.finish();

// v8 (NEW)
await Sentry.startSpan({ name: 'process', op: 'task' }, async () => {
  await Sentry.startSpan({ name: 'SELECT', op: 'db.query' }, async () => {
    // ... query
  }); // auto-finishes
}); // auto-finishes
```

**Breaking Change 4: ESM initialization**
```typescript
// v7 (OLD) — import at top of file
import * as Sentry from '@sentry/node';
Sentry.init({ dsn: '...' });

// v8 (NEW) — must be in separate file, loaded first
// instrument.mjs (separate file)
import * as Sentry from '@sentry/node';
Sentry.init({ dsn: '...' });

// Run with: node --import ./instrument.mjs app.mjs
```

**Breaking Change 5: Transport interface**
```typescript
// v7 (OLD) — send could return void
makeRequest(request) {
  sendToBackend(request);
  // no return needed
}

// v8 (NEW) — must return TransportMakeRequestResponse
makeRequest(request) {
  sendToBackend(request);
  return { statusCode: 200 }; // Required
}
```

### 3. Verify All @sentry/* Packages Match

```bash
# All Sentry packages MUST be the same major version
# Mixed versions cause runtime errors

# Check for mismatches
npm ls @sentry/core @sentry/node @sentry/utils @sentry/types 2>/dev/null

# Fix: install all at same version
npm install @sentry/node@8 @sentry/profiling-node@8
```

### 4. Update Bundler Plugins

```bash
# Sentry bundler plugins must be v2.14.2+ for SDK v8 compatibility
npm install @sentry/webpack-plugin@latest
npm install @sentry/vite-plugin@latest
```

### 5. Node.js Version Requirements

SDK v8 requires:
- Node.js >= 18.19.0 (for 18.x line)
- Node.js >= 20.6.0 (for 20.x line)
- Earlier versions have no ESM support needed by SDK v8

```bash
# Check Node version
node --version

# If too old, upgrade Node.js first
nvm install 20
nvm use 20
```

### 6. Post-Migration Test Plan

```typescript
// test-migration.mjs
import * as Sentry from '@sentry/node';

async function testMigration() {
  // 1. Test error capture
  try {
    throw new Error('Migration test error');
  } catch (e) {
    const eventId = Sentry.captureException(e);
    console.log('Error captured:', eventId ? 'PASS' : 'FAIL');
  }

  // 2. Test message capture
  Sentry.captureMessage('Migration test message', 'info');
  console.log('Message captured: PASS');

  // 3. Test scoped context
  Sentry.withScope((scope) => {
    scope.setTag('test', 'migration');
    scope.setUser({ id: 'test-user' });
    Sentry.captureMessage('Scoped test');
  });
  console.log('Scoped context: PASS');

  // 4. Test performance span
  await Sentry.startSpan(
    { name: 'migration-test', op: 'test' },
    async (span) => {
      await new Promise((r) => setTimeout(r, 50));
      console.log('Span created:', span ? 'PASS' : 'FAIL');
    }
  );

  // 5. Flush and verify
  const flushed = await Sentry.flush(5000);
  console.log('Flush:', flushed ? 'PASS' : 'FAIL');
}

testMigration();
```

### 7. Gradual Rollout Strategy

1. Upgrade in development environment first
2. Run full test suite — look for Sentry-related failures
3. Deploy to staging, monitor for 1-2 days
4. Review Sentry dashboard for event quality changes
5. Deploy to production with rollback plan ready

## Output
- SDK upgraded to target version with all packages aligned
- Deprecated APIs updated using migr8 codemod
- Integration syntax migrated from classes to functions
- Hub API replaced with new Scope API
- ESM initialization pattern implemented
- Post-migration tests passing

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot find module '@sentry/hub'` | Package removed in v8 | Replace hub imports with `@sentry/node` scope APIs |
| `Sentry.startTransaction is not a function` | Removed in v8 | Use `Sentry.startSpan()` instead |
| `new Integrations.X is not a constructor` | Classes removed in v8 | Use functional form: `Sentry.xIntegration()` |
| Mixed version errors | Some @sentry packages at v7, others at v8 | Align all packages: `npm install @sentry/node@8 @sentry/browser@8` |
| ESM import errors | Node.js version too old for SDK v8 | Upgrade to Node.js 18.19+ or 20.6+ |

## Resources
- [v7 to v8 Migration Guide](https://docs.sentry.io/platforms/javascript/migration/v7-to-v8/)
- [Node.js v7 to v8](https://docs.sentry.io/platforms/javascript/guides/node/migration/v7-to-v8/)
- [Express v7 to v8](https://docs.sentry.io/platforms/javascript/guides/express/migration/v7-to-v8/)
- [@sentry/migr8 Tool](https://github.com/getsentry/sentry-migr8)
