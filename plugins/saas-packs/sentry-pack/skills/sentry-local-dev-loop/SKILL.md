---
name: sentry-local-dev-loop
description: |
  Set up local development workflow with Sentry.
  Use when configuring Sentry for development environments,
  setting up debug mode, or testing error capture locally.
  Trigger with phrases like "sentry local dev", "sentry development",
  "debug sentry", "sentry dev environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Local Dev Loop

## Overview
Configure Sentry for efficient local development with appropriate settings.

## Prerequisites
- Sentry SDK installed
- Development environment set up
- Separate Sentry project for development (recommended)

## Instructions

### Step 1: Environment-Based Configuration
```typescript
import * as Sentry from '@sentry/node';

const isDev = process.env.NODE_ENV === 'development';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: isDev ? 'development' : 'production',

  // Higher sample rates in dev for testing
  tracesSampleRate: isDev ? 1.0 : 0.1,

  // Enable debug mode in development
  debug: isDev,

  // Don't send errors in development (optional)
  enabled: !isDev || process.env.SENTRY_DEV_ENABLED === 'true',
});
```

### Step 2: Development-Only DSN
```bash
# .env.development
SENTRY_DSN=https://dev-key@org.ingest.sentry.io/dev-project

# .env.production
SENTRY_DSN=https://prod-key@org.ingest.sentry.io/prod-project
```

### Step 3: Debug Output
```typescript
// Enable verbose logging in development
if (isDev) {
  Sentry.addIntegration(new Sentry.Integrations.Debug({
    stringify: true,
  }));
}
```

### Step 4: Local Testing Script
```bash
# test-sentry.sh
#!/bin/bash
export NODE_ENV=development
export SENTRY_DEV_ENABLED=true
node -e "
const Sentry = require('@sentry/node');
Sentry.init({ dsn: process.env.SENTRY_DSN, debug: true });
Sentry.captureMessage('Local dev test');
console.log('Check Sentry dashboard');
"
```

## Output
- Environment-aware Sentry configuration
- Debug logging enabled for development
- Separate project/DSN for development events

## Best Practices

### Do
- Use separate Sentry projects for dev/staging/prod
- Enable debug mode during development
- Set higher sample rates for testing
- Use environment tags consistently

### Don't
- Send all development errors to production Sentry
- Leave debug mode on in production
- Use same DSN across all environments
- Ignore rate limits during testing

## Examples

### Next.js Configuration
```typescript
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_VERCEL_ENV || 'development',
  enabled: process.env.NODE_ENV === 'production',
  debug: process.env.NODE_ENV === 'development',
});
```

### Python Flask Configuration
```python
import sentry_sdk
from flask import Flask

app = Flask(__name__)

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    environment=os.environ.get('FLASK_ENV', 'development'),
    debug=os.environ.get('FLASK_ENV') == 'development',
    traces_sample_rate=1.0 if os.environ.get('FLASK_ENV') == 'development' else 0.1,
)
```

## Resources
- [Sentry Environment Config](https://docs.sentry.io/platforms/javascript/configuration/environments/)
- [Sentry Debug Mode](https://docs.sentry.io/platforms/javascript/configuration/options/#debug)

## Next Steps
Proceed to `sentry-sdk-patterns` for SDK best practices.
