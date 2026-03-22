---
name: sentry-install-auth
description: |
  Install and configure Sentry SDK with DSN authentication.
  Use when setting up a new Sentry integration, configuring DSN,
  or initializing Sentry in your project.
  Trigger with phrases like "install sentry", "setup sentry",
  "sentry auth", "configure sentry DSN".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(pip:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, authentication, sdk, setup]

---
# Sentry Install & Auth

## Prerequisites
- Node.js 18.19+ or 20.6+ (required for ESM support in SDK v8)
- Package manager (npm, pnpm, or pip)
- Sentry account with project created at https://sentry.io
- DSN from Project Settings > Client Keys (DSN)

## Instructions

### 1. Install the SDK

**Node.js / TypeScript:**
```bash
npm install @sentry/node
# For profiling support:
npm install @sentry/profiling-node
```

**Browser / React:**
```bash
npm install @sentry/browser
# Or framework-specific:
npm install @sentry/react
npm install @sentry/nextjs
npm install @sentry/vue
```

**Python:**
```bash
pip install sentry-sdk
```

### 2. Store the DSN Securely

Never hardcode the DSN. Store it in environment variables:
```bash
# .env (add to .gitignore)
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
SENTRY_ENVIRONMENT=development
SENTRY_RELEASE=1.0.0
```

### 3. Initialize the SDK (Node.js v8)

Create `instrument.mjs` (or `instrument.js` for CJS) at your project root. This file MUST be imported before any other modules:

```typescript
// instrument.mjs — import this BEFORE your app code
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.SENTRY_ENVIRONMENT || 'development',
  release: process.env.SENTRY_RELEASE,

  // Performance: capture 100% in dev, 10-20% in production
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

  // Session replay (browser only — not applicable to Node)
  // replaysSessionSampleRate: 0.1,
  // replaysOnErrorSampleRate: 1.0,

  // Disable debug in production
  debug: process.env.NODE_ENV !== 'production',

  // Never send PII by default
  sendDefaultPii: false,

  integrations: [
    // Built-in: httpIntegration, expressIntegration auto-detected
  ],
});
```

**Import before your app starts:**
```typescript
// ESM: node --import ./instrument.mjs app.mjs
// CJS: require('./instrument.js'); at top of entry file
// Or in package.json:
// "scripts": { "start": "node --import ./instrument.mjs app.mjs" }
```

### 4. Initialize the SDK (Browser)

```typescript
import * as Sentry from '@sentry/browser';

Sentry.init({
  dsn: process.env.SENTRY_DSN, // injected at build time
  environment: process.env.NODE_ENV,
  release: process.env.SENTRY_RELEASE,
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
});
```

### 5. Initialize the SDK (Python)

```python
import sentry_sdk
import os

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
    release=os.environ.get("SENTRY_RELEASE"),
    traces_sample_rate=0.1,
    send_default_pii=False,
)
```

### 6. Verify Installation

```typescript
// Quick verification — send a test event
Sentry.captureMessage('Sentry SDK installed successfully', 'info');
```

Check the Sentry dashboard Issues tab within 30 seconds. If the event appears, authentication is working.

### 7. Auth Token for CLI & CI

Generate an auth token at https://sentry.io/settings/auth-tokens/ with scopes: `project:releases`, `org:read`. Store as `SENTRY_AUTH_TOKEN` in CI secrets.

```bash
# Install Sentry CLI
npm install -g @sentry/cli

# Verify auth
sentry-cli info
```

## Critical Initialization Order

The SDK MUST be initialized before importing any modules you want instrumented. If you initialize late, auto-instrumentation for HTTP, database, and framework middleware will not work. The `--import` flag for Node.js ESM ensures this ordering.

## Output
- SDK package installed in node_modules or site-packages
- DSN stored in environment variables (never committed to git)
- `instrument.mjs` created and loaded before app entry point
- Sentry initialized with environment, release, and sample rates configured
- Test event visible in Sentry dashboard confirming auth works

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Sentry Logger [error]: Error: Invalid Sentry Dsn` | Malformed DSN string | Copy DSN exactly from Project Settings > Client Keys |
| Events not appearing | DSN env var not loaded | Verify with `console.log(process.env.SENTRY_DSN)` before init |
| `[Sentry] Express is not instrumented` | SDK initialized after express import | Move `import './instrument.mjs'` to first line or use `--import` flag |
| ESM compatibility error | Node.js < 18.19 or < 20.6 | Upgrade Node.js; SDK v8 requires these minimum versions |
| `Sentry Logger [warn]: Too many requests` | Rate-limited by Sentry | Lower `tracesSampleRate`, check quota at sentry.io |

## Resources
- [Node.js Setup](https://docs.sentry.io/platforms/javascript/guides/node/)
- [Browser Setup](https://docs.sentry.io/platforms/javascript/)
- [Python Setup](https://docs.sentry.io/platforms/python/)
- [Configuration Options](https://docs.sentry.io/platforms/javascript/configuration/options/)
- [SDK Migration v7 to v8](https://docs.sentry.io/platforms/javascript/migration/v7-to-v8/)
