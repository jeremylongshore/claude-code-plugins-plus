---
name: sentry-deploy-integration
description: |
  Track deployments and releases in Sentry.
  Use when configuring deployment tracking, release health,
  or connecting deployments to error data.
  Trigger with phrases like "sentry deploy tracking", "sentry release health",
  "track deployments sentry", "sentry deployment notification".
allowed-tools: Read, Write, Edit, Bash(sentry-cli:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Deploy Integration

## Overview
Track deployments and monitor release health with Sentry.

## Deployment Tracking

### Create Release and Deploy
```bash
#!/bin/bash
# deploy.sh

VERSION=$(git rev-parse --short HEAD)
ENVIRONMENT=${1:-production}

# Create release
sentry-cli releases new $VERSION

# Upload source maps
sentry-cli releases files $VERSION upload-sourcemaps ./dist

# Associate commits
sentry-cli releases set-commits $VERSION --auto

# Finalize release
sentry-cli releases finalize $VERSION

# Deploy application
npm run deploy:$ENVIRONMENT

# Notify Sentry of deployment
sentry-cli releases deploys $VERSION new \
  --env $ENVIRONMENT \
  --started $(date +%s) \
  --finished $(date +%s)

echo "Deployed $VERSION to $ENVIRONMENT"
```

### Application Configuration
```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.SENTRY_RELEASE || process.env.GIT_SHA,
});
```

## Release Health

### Enable Session Tracking
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  release: process.env.SENTRY_RELEASE,

  // Enable release health
  autoSessionTracking: true,

  // Or manual session management
});

// Manual session
Sentry.startSession();
// ... app runs ...
Sentry.endSession();
```

### Health Metrics
Sentry tracks automatically:
- **Crash-free sessions** - Sessions without fatal errors
- **Crash-free users** - Users without fatal errors
- **Adoption rate** - Users on this release vs total
- **Session duration** - Time spent in app

## Multi-Environment Deploys

```bash
# Deploy to staging
./deploy.sh staging

# Deploy to production
./deploy.sh production

# Deploy to canary
./deploy.sh canary
```

```typescript
// Environment-specific config
const environments = {
  production: { sampleRate: 0.1 },
  staging: { sampleRate: 1.0 },
  canary: { sampleRate: 1.0 },
};

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.DEPLOY_ENV,
  ...environments[process.env.DEPLOY_ENV],
});
```

## Vercel Integration

```bash
# Install Sentry Vercel integration
# Vercel Dashboard > Integrations > Sentry

# vercel.json
{
  "build": {
    "env": {
      "SENTRY_RELEASE": "@sentry-release"
    }
  }
}
```

```typescript
// next.config.js with Sentry
const { withSentryConfig } = require('@sentry/nextjs');

module.exports = withSentryConfig({
  // Next.js config
}, {
  silent: true,
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
});
```

## Kubernetes Deploys

```yaml
# k8s deployment with Sentry
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    spec:
      containers:
        - name: app
          env:
            - name: SENTRY_DSN
              valueFrom:
                secretKeyRef:
                  name: sentry
                  key: dsn
            - name: SENTRY_RELEASE
              value: "${GIT_SHA}"
            - name: SENTRY_ENVIRONMENT
              value: "production"
```

```bash
# Post-deploy hook
kubectl rollout status deployment/app
sentry-cli releases deploys $VERSION new --env production
```

## Rollback Tracking

```bash
# When rolling back
OLD_VERSION=$(git rev-parse HEAD~1 --short)

# Deploy old version
kubectl set image deployment/app app=myapp:$OLD_VERSION

# Notify Sentry
sentry-cli releases deploys $OLD_VERSION new \
  --env production \
  --name "Rollback from $CURRENT_VERSION"
```

## Release Comparison

View in Sentry Dashboard:
1. Releases > Compare
2. Select two releases
3. View:
   - New issues introduced
   - Issues resolved
   - Crash rate changes
   - Performance differences

## Resources
- [Sentry Releases](https://docs.sentry.io/product/releases/)
- [Release Health](https://docs.sentry.io/product/releases/health/)
