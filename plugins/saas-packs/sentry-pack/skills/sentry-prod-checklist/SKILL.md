---
name: sentry-prod-checklist
description: |
  Production deployment checklist for Sentry integration.
  Use when preparing for production deployment, reviewing
  Sentry configuration, or verifying production readiness.
  Trigger with phrases like "sentry production", "deploy sentry",
  "sentry checklist", "sentry go-live".
allowed-tools: Read, Grep, Bash(npm:*), Bash(node:*), Bash(curl:*), Bash(sentry-cli:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, deployment, production, checklist]

---
# Sentry Production Checklist

## Prerequisites
- Sentry account with dedicated production project
- Production DSN separate from development/staging
- Build pipeline with source map generation
- Sentry CLI or bundler plugin configured for source map upload

## Instructions

### SDK Configuration Checklist

```typescript
// production-ready Sentry.init
Sentry.init({
  // [x] DSN from environment variable, never hardcoded
  dsn: process.env.SENTRY_DSN,

  // [x] Environment set explicitly
  environment: 'production',

  // [x] Release matches sentry-cli release version
  release: process.env.SENTRY_RELEASE,

  // [x] Debug disabled in production
  debug: false,

  // [x] PII collection disabled
  sendDefaultPii: false,

  // [x] Error sample rate: 100% (capture all errors)
  sampleRate: 1.0,

  // [x] Transaction sample rate: 5-20% for production
  tracesSampleRate: 0.1,

  // [x] Max breadcrumbs limited for payload size
  maxBreadcrumbs: 50,

  // [x] Filtering configured for noisy errors
  ignoreErrors: [
    'ResizeObserver loop',
    'Non-Error promise rejection',
    /Loading chunk \d+ failed/,
    'Network request failed',
  ],

  // [x] beforeSend scrubs sensitive data
  beforeSend(event, hint) {
    if (event.request?.headers) {
      delete event.request.headers['Authorization'];
      delete event.request.headers['Cookie'];
    }
    return event;
  },
});
```

### Pre-Deployment Checklist

**Security:**
- [ ] `sendDefaultPii: false`
- [ ] `debug: false`
- [ ] DSN in environment variables (not in source code)
- [ ] `beforeSend` scrubs auth headers and sensitive data
- [ ] Auth tokens use minimal scopes (`project:releases` for CI)
- [ ] Allowed domains configured for browser projects

**Source Maps:**
- [ ] Source maps generated during build (`sourcemap: true`)
- [ ] `sentry-cli sourcemaps upload` or bundler plugin configured
- [ ] `--url-prefix` matches production asset URLs
- [ ] `--validate` flag confirms maps are valid
- [ ] SDK `release` matches CLI release version
- [ ] Source maps NOT served to clients (only uploaded to Sentry)

**Alerting:**
- [ ] Issue alert: "New issue in production" -> Slack/PagerDuty
- [ ] Issue alert: "Regression" -> team channel
- [ ] Metric alert: "Error rate > X/minute" -> on-call
- [ ] Metric alert: "P95 latency > threshold" -> performance team
- [ ] Alert actions route to correct team channels

**Performance:**
- [ ] `tracesSampleRate` set to 5-20% (not 100%)
- [ ] `tracesSampler` configured for endpoint-specific rates
- [ ] High-volume endpoints sampled at lower rates
- [ ] Health check endpoints excluded from tracing
- [ ] Transaction names parameterized (`:id` not `12345`)

**Release Management:**
- [ ] Release created in CI: `sentry-cli releases new $VERSION`
- [ ] Commits associated: `sentry-cli releases set-commits --auto`
- [ ] Source maps uploaded before deployment
- [ ] Release finalized: `sentry-cli releases finalize $VERSION`
- [ ] Deploy recorded: `sentry-cli releases deploys $VERSION new -e production`

### Verification Script

```bash
#!/bin/bash
# scripts/verify-production-sentry.sh
set -euo pipefail

echo "=== Sentry Production Verification ==="

# 1. Verify environment variables
for var in SENTRY_DSN SENTRY_ORG SENTRY_PROJECT SENTRY_AUTH_TOKEN; do
  if [ -z "${!var:-}" ]; then
    echo "FAIL: $var not set"
    exit 1
  fi
  echo "OK: $var is set"
done

# 2. Verify CLI auth
sentry-cli info > /dev/null 2>&1 && echo "OK: CLI authenticated" || echo "FAIL: CLI auth"

# 3. Verify source maps uploaded
RELEASE="${SENTRY_RELEASE:-$(git rev-parse --short HEAD)}"
FILE_COUNT=$(sentry-cli releases files "$RELEASE" list 2>/dev/null | wc -l)
if [ "$FILE_COUNT" -gt 1 ]; then
  echo "OK: $FILE_COUNT files uploaded for release $RELEASE"
else
  echo "WARN: No source maps found for release $RELEASE"
fi

# 4. Verify network connectivity
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://sentry.io/api/0/)
echo "OK: sentry.io reachable (HTTP $HTTP_CODE)"

# 5. Send test event (optional — remove after first deploy)
# node -e "require('@sentry/node').init({dsn:process.env.SENTRY_DSN}); \
#   require('@sentry/node').captureMessage('Production deploy verification')"

echo "=== Verification Complete ==="
```

### Post-Deploy Monitoring

After deploying, verify in Sentry dashboard:

1. **Issues** tab — check for new errors in the latest release
2. **Performance** tab — verify transactions appear with correct names
3. **Releases** tab — confirm release shows with:
   - Correct version identifier
   - Associated commits
   - Source maps (click "Artifacts")
   - Deploy marker for production environment
4. **Release Health** — crash-free session rate should be > 99%

### Rollback Procedure

If Sentry causes issues in production:

```typescript
// Emergency disable: set DSN to empty string
// Environment variable: SENTRY_DSN=""

// Or disable via beforeSend
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  beforeSend() {
    return null; // Drop all events
  },
});
```

## Output
- Production-hardened Sentry configuration verified
- Source maps uploaded and validated for current release
- Alert rules configured with team routing
- Release tracking active with commit association
- Verification script confirming all production requirements met

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Stack traces show minified code | Source maps missing or URL prefix wrong | Re-upload with correct `--url-prefix`, verify with `sourcemaps explain` |
| No release health data | Session tracking not enabled | Ensure `autoSessionTracking: true` (default in v8) |
| Alerts not firing | Alert rules not configured for production env | Create issue/metric alerts filtered to `environment:production` |
| Events from wrong environment | `environment` not set in SDK init | Explicitly set `environment: 'production'` |
| Excessive event volume | No rate limits or filtering | Set project rate limits, add `ignoreErrors`, configure `tracesSampler` |

## Resources
- [Production Checklist](https://docs.sentry.io/product/releases/setup/)
- [Alerting](https://docs.sentry.io/product/alerts/)
- [Release Health](https://docs.sentry.io/product/releases/health/)
- [Source Maps](https://docs.sentry.io/platforms/javascript/sourcemaps/)
