---
name: sentry-debug-bundle
description: |
  Collect debug information for Sentry support tickets and diagnostics.
  Use when preparing support requests, debugging complex issues,
  or gathering diagnostic information.
  Trigger with phrases like "sentry debug info", "sentry support ticket",
  "gather sentry diagnostics", "sentry debug bundle".
allowed-tools: Read, Bash(npm:*), Bash(node:*), Bash(npx:*), Bash(curl:*), Bash(sentry-cli:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, debugging, support]

---
# Sentry Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`npm list @sentry/node @sentry/browser @sentry/cli 2>/dev/null | grep sentry || echo 'No Sentry packages found'`
!`sentry-cli --version 2>/dev/null || echo 'sentry-cli not installed'`

## Prerequisites
- Debug mode enabled in SDK (`debug: true`)
- Sentry CLI installed for source map diagnostics
- Access to environment variables
- Application logs available

## Instructions

### 1. Collect SDK Version and Configuration

```bash
# List all installed Sentry packages
npm list 2>/dev/null | grep -i sentry

# Check for version mismatches (all @sentry/* packages should be same version)
npm list 2>/dev/null | grep "@sentry/" | sort
```

### 2. Export Sanitized Configuration

```typescript
// scripts/sentry-debug.mjs
import * as Sentry from '@sentry/node';

const client = Sentry.getClient();
if (!client) {
  console.error('Sentry client not initialized');
  process.exit(1);
}

const options = client.getOptions();
const debugInfo = {
  sdk_version: Sentry.SDK_VERSION,
  dsn_configured: !!options.dsn,
  dsn_host: options.dsn ? new URL(options.dsn).hostname : 'N/A',
  environment: options.environment,
  release: options.release,
  sample_rate: options.sampleRate,
  traces_sample_rate: options.tracesSampleRate,
  send_default_pii: options.sendDefaultPii,
  debug: options.debug,
  max_breadcrumbs: options.maxBreadcrumbs,
  before_send: typeof options.beforeSend === 'function' ? 'configured' : 'none',
  before_send_transaction: typeof options.beforeSendTransaction === 'function' ? 'configured' : 'none',
  integrations: client.getOptions().integrations?.map(i => i.name) || [],
};

console.log(JSON.stringify(debugInfo, null, 2));
```

### 3. Test Network Connectivity

```bash
# Test Sentry API reachability
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
  https://sentry.io/api/0/

# Test ingest endpoint (replace with your DSN host)
curl -s -o /dev/null -w "HTTP %{http_code}" \
  https://o0.ingest.sentry.io/api/0/envelope/

# DNS resolution
dig +short o0.ingest.sentry.io

# Check for proxy interference
curl -v https://sentry.io/api/0/ 2>&1 | grep -i proxy
```

### 4. Capture and Verify Test Event

```typescript
// Send test event and capture the event ID
Sentry.init({ dsn: process.env.SENTRY_DSN, debug: true });

const eventId = Sentry.captureMessage('Debug bundle test event', 'info');
console.log(`Test event ID: ${eventId}`);

const flushed = await Sentry.flush(10000);
console.log(`Flush result: ${flushed ? 'SUCCESS' : 'TIMEOUT'}`);

// Use event ID to look up in Sentry:
// https://sentry.io/organizations/YOUR_ORG/issues/?query=event.id:EVENT_ID
```

### 5. Source Map Diagnostics

```bash
# List uploaded files for a release
sentry-cli releases files "$SENTRY_RELEASE" list

# Explain source map resolution for a specific event
sentry-cli sourcemaps explain \
  --org "$SENTRY_ORG" \
  --project "$SENTRY_PROJECT" \
  EVENT_ID

# Validate source maps locally before upload
sentry-cli sourcemaps upload --validate --dry-run \
  --release="$SENTRY_RELEASE" \
  --url-prefix="~/static/js" \
  ./dist
```

### 6. Check Project Rate Limits and Quotas

```bash
# Project stats (last 24h)
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$SENTRY_ORG/$SENTRY_PROJECT/stats/" \
  | python3 -m json.tool 2>/dev/null || echo "Auth token may be invalid"

# Organization usage
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/stats_v2/?field=sum(quantity)&groupBy=category&interval=1d&statsPeriod=24h"
```

### 7. Generate Debug Bundle Report

```bash
#!/bin/bash
# scripts/sentry-debug-bundle.sh
set -euo pipefail

REPORT="sentry-debug-$(date +%Y%m%d-%H%M%S).md"

cat > "$REPORT" << EOF
# Sentry Debug Bundle
**Generated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Node.js:** $(node --version 2>/dev/null || echo N/A)
**OS:** $(uname -a)

## SDK Packages
\`\`\`
$(npm list 2>/dev/null | grep -i sentry || echo "No packages found")
\`\`\`

## CLI Version
\`\`\`
$(sentry-cli --version 2>/dev/null || echo "Not installed")
\`\`\`

## Environment Variables (sanitized)
- SENTRY_DSN: $([ -n "${SENTRY_DSN:-}" ] && echo "SET ($(echo $SENTRY_DSN | sed 's/\/\/.*@/\/\/***@/'))" || echo "NOT SET")
- SENTRY_ORG: ${SENTRY_ORG:-NOT SET}
- SENTRY_PROJECT: ${SENTRY_PROJECT:-NOT SET}
- SENTRY_ENVIRONMENT: ${SENTRY_ENVIRONMENT:-NOT SET}
- SENTRY_RELEASE: ${SENTRY_RELEASE:-NOT SET}
- NODE_ENV: ${NODE_ENV:-NOT SET}

## Network Connectivity
$(curl -s -o /dev/null -w "sentry.io: HTTP %{http_code} (%{time_total}s)" https://sentry.io/api/0/ 2>/dev/null || echo "sentry.io: UNREACHABLE")

## Release Artifacts
\`\`\`
$(sentry-cli releases files "${SENTRY_RELEASE:-unknown}" list 2>/dev/null || echo "No release found or auth failed")
\`\`\`
EOF

echo "Debug bundle saved to: $REPORT"
```

### 8. Integration Health Check

```typescript
// lib/sentry-health.ts — runtime health check endpoint
import * as Sentry from '@sentry/node';

export async function sentryHealthCheck(): Promise<{
  status: 'healthy' | 'degraded' | 'unhealthy';
  details: Record<string, unknown>;
}> {
  const client = Sentry.getClient();

  if (!client) {
    return { status: 'unhealthy', details: { error: 'Client not initialized' } };
  }

  const options = client.getOptions();

  // Send a test event and check if flush succeeds
  Sentry.captureMessage('health-check', 'debug');
  const flushed = await Sentry.flush(3000);

  return {
    status: flushed ? 'healthy' : 'degraded',
    details: {
      sdk_version: Sentry.SDK_VERSION,
      dsn_configured: !!options.dsn,
      environment: options.environment,
      release: options.release,
      flush_success: flushed,
    },
  };
}
```

## Output
- Debug bundle markdown report with all diagnostics
- SDK version and configuration documented (DSN redacted)
- Network connectivity verified to Sentry endpoints
- Test event capture confirmed with event ID
- Source map upload status and validation results

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `sentry-cli info` fails | Auth token invalid or expired | Regenerate at sentry.io/settings/auth-tokens/ |
| `sourcemaps explain` shows no match | URL prefix mismatch | Compare `--url-prefix` with actual script URLs in error event |
| Flush times out | Network blocking outbound to sentry.io | Check firewall, proxy, or VPN settings |
| Package version mismatch | Multiple @sentry/* packages at different versions | Run `npm dedupe` or align all versions in package.json |
| No client after init | SDK initialization failed silently | Set `debug: true` and check console for init errors |

## Resources
- [Sentry Support](https://sentry.io/support/)
- [Troubleshooting](https://docs.sentry.io/platforms/javascript/troubleshooting/)
- [Source Maps Explain](https://docs.sentry.io/platforms/javascript/sourcemaps/troubleshooting_js/)
- [GitHub Issues](https://github.com/getsentry/sentry-javascript/issues)
