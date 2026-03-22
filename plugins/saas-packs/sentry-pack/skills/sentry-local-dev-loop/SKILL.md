---
name: sentry-local-dev-loop
description: |
  Set up local development workflow with Sentry.
  Use when configuring Sentry for development environments,
  setting up debug mode, or testing error capture locally.
  Trigger with phrases like "sentry local dev", "sentry development",
  "debug sentry", "sentry dev environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, testing, debugging, workflow, development]

---
# Sentry Local Dev Loop

## Prerequisites
- Sentry SDK installed
- Separate Sentry project for development (recommended)
- `.env` file with development DSN

## Instructions

### 1. Development-Optimized Sentry.init

```typescript
// instrument.dev.mjs — development configuration
import * as Sentry from '@sentry/node';

const isDev = process.env.NODE_ENV !== 'production';

Sentry.init({
  dsn: isDev ? process.env.SENTRY_DSN_DEV : process.env.SENTRY_DSN,

  environment: 'development',
  release: 'dev-local',

  // Capture everything in development
  tracesSampleRate: 1.0,
  sampleRate: 1.0,

  // Enable verbose logging to console
  debug: true,

  // Include default PII in dev for easier debugging
  sendDefaultPii: true,

  // Optional: disable sending to Sentry entirely for offline work
  // dsn: '', // Empty DSN = SDK initialized but no events sent

  beforeSend(event) {
    // In dev, also log to console for immediate feedback
    console.log('[Sentry Event]', event.exception?.values?.[0]?.value || event.message);
    return event;
  },
});
```

### 2. Environment Variable Setup

```bash
# .env.development
SENTRY_DSN_DEV=https://dev-key@o0.ingest.sentry.io/dev-project
SENTRY_ENVIRONMENT=development
SENTRY_RELEASE=dev-local
NODE_ENV=development

# .env.production
SENTRY_DSN=https://prod-key@o0.ingest.sentry.io/prod-project
SENTRY_ENVIRONMENT=production
NODE_ENV=production
```

### 3. Conditional Initialization Pattern

```typescript
// lib/sentry.ts — environment-aware initialization
import * as Sentry from '@sentry/node';

export function initSentry() {
  const env = process.env.NODE_ENV || 'development';

  // Option A: Skip Sentry entirely in dev
  if (env === 'development' && !process.env.SENTRY_DSN_DEV) {
    console.log('[Sentry] Skipped — no dev DSN configured');
    return;
  }

  // Option B: Initialize with dev-specific settings
  Sentry.init({
    dsn: env === 'development'
      ? process.env.SENTRY_DSN_DEV
      : process.env.SENTRY_DSN,
    environment: env,
    debug: env === 'development',
    tracesSampleRate: env === 'development' ? 1.0 : 0.1,
    sendDefaultPii: env === 'development',

    // In dev, also log events to console
    beforeSend(event) {
      if (env === 'development') {
        const errorType = event.exception?.values?.[0]?.type;
        const errorMsg = event.exception?.values?.[0]?.value;
        console.log(`[Sentry] ${errorType}: ${errorMsg}`);
      }
      return event;
    },
  });
}
```

### 4. Local Verification Script

```typescript
// scripts/verify-sentry.mjs
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN_DEV || process.env.SENTRY_DSN,
  debug: true,
  environment: 'verification',
});

async function verify() {
  console.log('1. Testing captureMessage...');
  Sentry.captureMessage('Dev verification test', 'info');

  console.log('2. Testing captureException...');
  try {
    throw new Error('Dev loop verification error');
  } catch (e) {
    Sentry.captureException(e);
  }

  console.log('3. Testing performance span...');
  await Sentry.startSpan(
    { name: 'dev.verification', op: 'test' },
    async () => {
      await new Promise((r) => setTimeout(r, 100));
    }
  );

  console.log('4. Flushing events...');
  const flushed = await Sentry.flush(5000);
  console.log(flushed ? 'All events sent' : 'Flush timed out — check DSN');
}

verify();
```

### 5. Sentry Spotlight for Local Debugging

Sentry Spotlight is a dev tool that shows Sentry events in your browser without sending to sentry.io:

```bash
# Install Spotlight sidecar
npx @spotlightjs/spotlight
```

```typescript
// instrument.dev.mjs — with Spotlight
import * as Sentry from '@sentry/node';
import { setupSidecar } from '@spotlightjs/sidecar';

Sentry.init({
  dsn: process.env.SENTRY_DSN_DEV,
  debug: true,
  spotlight: process.env.NODE_ENV === 'development',
  // Spotlight intercepts events and shows them in a local UI
  // at http://localhost:8969/stream
});
```

### 6. Git Hook for Pre-Push Verification

```bash
#!/bin/bash
# .git/hooks/pre-push — verify Sentry doesn't have hardcoded DSNs
if grep -r "ingest.sentry.io" --include="*.ts" --include="*.js" \
   --exclude-dir=node_modules --exclude-dir=dist src/; then
  echo "ERROR: Hardcoded Sentry DSN found. Use environment variables."
  exit 1
fi
```

### 7. Testing Without Network

```typescript
// For offline development or CI without Sentry access:
Sentry.init({
  dsn: '', // Empty DSN = SDK loads but sends nothing
  debug: false,
});

// All Sentry.captureException() calls become no-ops
// Your app code continues working without modification
```

## Output
- Environment-aware Sentry configuration switching dev/prod
- Debug logging enabled showing events in console during dev
- Verification script confirming SDK works end-to-end
- Spotlight integration for local event inspection
- DSN security check preventing hardcoded secrets in commits

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Events going to prod project | Wrong DSN loaded | Use separate `SENTRY_DSN_DEV` and verify `NODE_ENV` |
| Debug output too verbose | `debug: true` in production | Gate debug mode behind environment check |
| Events not appearing locally | Firewall blocking sentry.io | Use Spotlight for local dev, or set `dsn: ''` for offline |
| Rate-limited during dev | `tracesSampleRate: 1.0` sending too many events | Use separate dev project with its own quota |
| `Sentry.flush()` times out | No network or invalid DSN | Check DSN, verify network with `curl https://sentry.io/api/0/` |

## Resources
- [Configuration Options](https://docs.sentry.io/platforms/javascript/configuration/options/)
- [Environments](https://docs.sentry.io/platforms/javascript/configuration/environments/)
- [Sentry Spotlight](https://spotlightjs.com/)
- [Debug Mode](https://docs.sentry.io/platforms/javascript/configuration/options/#debug)
