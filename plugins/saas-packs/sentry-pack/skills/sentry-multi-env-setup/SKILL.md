---
name: sentry-multi-env-setup
description: |
  Configure Sentry across multiple environments.
  Use when setting up Sentry for dev/staging/production,
  managing environment-specific configurations, or isolating data.
  Trigger with phrases like "sentry environments", "sentry staging setup",
  "multi-environment sentry", "sentry dev vs prod".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, environments, configuration, multi-env]

---
# Sentry Multi-Environment Setup

## Prerequisites
- Environment naming convention defined (development, staging, production)
- DSN management strategy decided (single project vs. separate projects)
- Sample rate requirements per environment documented
- Alert routing per environment planned

## Instructions

### 1. Environment-Aware SDK Configuration

```typescript
// config/sentry.ts
import * as Sentry from '@sentry/node';

type Environment = 'development' | 'staging' | 'production';

const ENV_CONFIG: Record<Environment, Partial<Sentry.NodeOptions>> = {
  development: {
    tracesSampleRate: 1.0,        // Capture everything
    sampleRate: 1.0,
    debug: true,                   // Verbose console output
    sendDefaultPii: true,          // Include PII for debugging
    maxBreadcrumbs: 100,
  },
  staging: {
    tracesSampleRate: 0.5,        // 50% of transactions
    sampleRate: 1.0,              // All errors
    debug: false,
    sendDefaultPii: false,
    maxBreadcrumbs: 50,
  },
  production: {
    tracesSampleRate: 0.1,        // 10% of transactions
    sampleRate: 1.0,              // All errors
    debug: false,
    sendDefaultPii: false,
    maxBreadcrumbs: 50,
  },
};

export function initSentry(env?: Environment) {
  const environment = env || (process.env.NODE_ENV as Environment) || 'development';
  const config = ENV_CONFIG[environment] || ENV_CONFIG.development;

  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment,
    release: process.env.SENTRY_RELEASE,
    ...config,
  });
}
```

### 2. Project Structure Decision

**Option A: Single project with environments (simpler, recommended for small teams)**
```
Project: my-app
├── Environment: development  (DSN: same)
├── Environment: staging      (DSN: same)
└── Environment: production   (DSN: same)
```

Pros: Unified issue view, easy to track regressions across environments.

**Option B: Separate projects per environment (enterprise)**
```
Project: my-app-dev        (DSN: dev-dsn)
Project: my-app-staging    (DSN: staging-dsn)
Project: my-app-production (DSN: prod-dsn)
```

Pros: Independent quotas, stricter access control, no dev noise in prod.

### 3. Separate DSN per Environment

```bash
# .env.development
SENTRY_DSN=https://dev-key@o0.ingest.sentry.io/111
SENTRY_ENVIRONMENT=development

# .env.staging
SENTRY_DSN=https://staging-key@o0.ingest.sentry.io/222
SENTRY_ENVIRONMENT=staging

# .env.production
SENTRY_DSN=https://prod-key@o0.ingest.sentry.io/333
SENTRY_ENVIRONMENT=production
```

```typescript
// Conditional DSN loading
Sentry.init({
  // Use environment-specific DSN, or disable in development
  dsn: process.env.NODE_ENV === 'development'
    ? (process.env.SENTRY_DSN_DEV || '') // Empty string = disabled
    : process.env.SENTRY_DSN,
  environment: process.env.SENTRY_ENVIRONMENT || process.env.NODE_ENV,
});
```

### 4. Environment-Specific Filtering

```typescript
Sentry.init({
  beforeSend(event) {
    const env = process.env.NODE_ENV;

    // In development: filter nothing, capture everything
    if (env === 'development') return event;

    // In staging: drop debug-level events
    if (env === 'staging' && event.level === 'debug') return null;

    // In production: aggressive filtering
    if (env === 'production') {
      // Drop known non-actionable errors
      if (event.exception?.values?.some(e =>
        e.value?.match(/ResizeObserver|Loading chunk/)
      )) return null;

      // Scrub PII
      if (event.request?.headers) {
        delete event.request.headers['Authorization'];
        delete event.request.headers['Cookie'];
      }
    }

    return event;
  },
});
```

### 5. Environment-Specific Alert Rules

Configure in Sentry dashboard per environment:

**Production alerts:**
- Issue alert: "New issue" with environment filter `production` -> PagerDuty
- Metric alert: "Error rate > 50/min" with environment `production` -> Slack #alerts-critical

**Staging alerts:**
- Issue alert: "New issue" with environment filter `staging` -> Slack #alerts-staging
- No PagerDuty for staging

**Development alerts:**
- No alerts configured (developers check dashboard manually)

### 6. Environment Tags for Filtering

```typescript
// Add environment context to every event
Sentry.init({
  initialScope: {
    tags: {
      environment: process.env.NODE_ENV,
      region: process.env.AWS_REGION || 'us-east-1',
      cluster: process.env.K8S_CLUSTER || 'default',
    },
  },
});

// Filter by environment in Sentry dashboard:
// Issues > Search: environment:production is:unresolved
// Performance > Filter: environment:staging
```

### 7. CI/CD Environment-Aware Releases

```bash
#!/bin/bash
# scripts/sentry-release.sh
VERSION=$(git rev-parse --short HEAD)
ENVIRONMENT="${1:-staging}"

sentry-cli releases new "$VERSION"
sentry-cli releases set-commits "$VERSION" --auto
sentry-cli sourcemaps upload --release="$VERSION" ./dist
sentry-cli releases finalize "$VERSION"

# Record deployment to specific environment
sentry-cli releases deploys "$VERSION" new --env "$ENVIRONMENT"

# Usage:
# ./scripts/sentry-release.sh staging
# ./scripts/sentry-release.sh production
```

### 8. Disable Sentry in Test/CI Environments

```typescript
// Skip Sentry entirely in test environments
if (process.env.NODE_ENV === 'test' || process.env.CI) {
  // Don't initialize Sentry in unit tests
  // All Sentry.captureException() calls become no-ops
} else {
  Sentry.init({ dsn: process.env.SENTRY_DSN, /* ... */ });
}

// Or initialize with empty DSN (SDK loads but sends nothing)
Sentry.init({
  dsn: process.env.NODE_ENV === 'test' ? '' : process.env.SENTRY_DSN,
});
```

## Output
- Environment-specific SDK configuration with appropriate sample rates
- DSN management strategy implemented (single or separate projects)
- Environment-specific alert rules with appropriate routing
- Production-only PII scrubbing and filtering
- CI/CD releases tagged to correct environment
- Test environments properly excluded

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Dev events in production project | Wrong DSN loaded | Use separate env vars: `SENTRY_DSN_DEV`, `SENTRY_DSN_PROD` |
| Staging alerts going to PagerDuty | Alert rules not filtered by environment | Add `environment:production` filter to critical alerts |
| `environment: undefined` in events | `NODE_ENV` not set | Explicitly set `environment` in Sentry.init() |
| Quota exhausted by dev events | All environments sharing one quota | Use separate projects per environment for independent quotas |

## Resources
- [Environments](https://docs.sentry.io/product/sentry-basics/environments/)
- [Filtering Events](https://docs.sentry.io/platforms/javascript/configuration/filtering/)
- [Alert Configuration](https://docs.sentry.io/product/alerts/create-alerts/)
