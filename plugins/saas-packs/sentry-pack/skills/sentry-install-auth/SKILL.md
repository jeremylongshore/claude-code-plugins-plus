---
name: sentry-install-auth
description: |
  Install and configure Sentry SDK authentication.
  Use when setting up a new Sentry integration, configuring DSN,
  or initializing Sentry in your project.
  Trigger with phrases like "install sentry", "setup sentry",
  "sentry auth", "configure sentry DSN".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Install & Auth

## Overview
Set up Sentry SDK and configure authentication with your DSN.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Sentry account with project DSN
- DSN from Sentry project settings

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @sentry/node

# Browser/React
npm install @sentry/react

# Python
pip install sentry-sdk
```

### Step 2: Configure DSN
```bash
# Set environment variable
export SENTRY_DSN="https://key@org.ingest.sentry.io/project"

# Or create .env file
echo 'SENTRY_DSN=https://key@org.ingest.sentry.io/project' >> .env
```

### Step 3: Initialize Sentry
```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
});
```

### Step 4: Verify Connection
```typescript
Sentry.captureMessage('Sentry test message');
console.log('Check Sentry dashboard for test message');
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with DSN
- Sentry initialized and ready to capture errors

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid DSN | Incorrect or malformed DSN | Verify DSN format in Sentry project settings |
| Rate Limited | Exceeded quota | Check quota at https://sentry.io/settings |
| Network Error | Firewall blocking | Ensure outbound HTTPS to *.ingest.sentry.io |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV || 'development',
  release: process.env.npm_package_version,
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
});
```

### Python Setup
```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    environment=os.environ.get('ENVIRONMENT', 'development'),
    traces_sample_rate=1.0,
)
```

## Resources
- [Sentry Documentation](https://docs.sentry.io)
- [Sentry Dashboard](https://sentry.io)
- [Sentry Status](https://status.sentry.io)

## Next Steps
After successful auth, proceed to `sentry-hello-world` for your first error capture.
