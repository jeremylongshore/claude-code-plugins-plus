---
name: sentry-advanced-troubleshooting
description: |
  Advanced Sentry troubleshooting techniques.
  Use when debugging complex SDK issues, missing events,
  source map problems, or performance anomalies.
  Trigger with phrases like "sentry not working", "debug sentry",
  "sentry events missing", "fix sentry issues".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*), Bash(npm:*), Bash(curl:*), Bash(sentry-cli:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, debugging, performance, troubleshooting]

---
# Sentry Advanced Troubleshooting

## Prerequisites
- Debug mode enabled in SDK (`debug: true`)
- Access to application logs and Sentry dashboard
- Sentry CLI installed for source map debugging
- Network diagnostic tools available (curl, dig)

## Instructions

### 1. SDK Initialization Debugging

```typescript
// Enable maximum debug output
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: true, // Prints all SDK activity to console

  // Add transport debugging
  transport: (options) => {
    const transport = Sentry.makeNodeTransport(options);
    return {
      ...transport,
      send: async (envelope) => {
        console.log('[Sentry Transport] Sending envelope:', {
          type: envelope[0]?.type,
          items: envelope[1]?.length,
        });
        const result = await transport.send(envelope);
        console.log('[Sentry Transport] Result:', result);
        return result;
      },
    };
  },
});

// Verify initialization
const client = Sentry.getClient();
if (!client) {
  console.error('CRITICAL: Sentry client not initialized');
  console.error('Check: DSN valid? Import order correct?');
} else {
  console.log('Sentry initialized:', {
    dsn: client.getDsn()?.host,
    release: client.getOptions().release,
    environment: client.getOptions().environment,
    integrations: client.getOptions().integrations?.map(i => i.name),
  });
}
```

### 2. Event Not Appearing — Systematic Diagnosis

```typescript
async function diagnoseEventCapture() {
  // Step 1: Is the client initialized?
  const client = Sentry.getClient();
  if (!client) {
    console.error('Client not initialized — check init order');
    return;
  }

  // Step 2: Is DSN valid?
  const dsn = client.getDsn();
  console.log('DSN host:', dsn?.host);
  console.log('DSN project:', dsn?.projectId);

  // Step 3: Is beforeSend dropping events?
  const options = client.getOptions();
  if (options.beforeSend) {
    console.log('beforeSend is configured — test with a known event');
    // Temporarily bypass to test
  }

  // Step 4: Is sampling dropping events?
  console.log('sampleRate:', options.sampleRate);
  console.log('tracesSampleRate:', options.tracesSampleRate);

  // Step 5: Can we send an event?
  const eventId = Sentry.captureMessage('Diagnostic test', 'debug');
  console.log('Event ID:', eventId || 'NONE — event was dropped');

  // Step 6: Does flush succeed?
  const flushed = await Sentry.flush(10000);
  console.log('Flush:', flushed ? 'SUCCESS' : 'TIMEOUT — network issue');
}
```

### 3. Source Map Debugging

```bash
# Step 1: Verify source maps exist in build output
ls -la dist/*.map 2>/dev/null || echo "No source maps found in dist/"

# Step 2: Verify source maps are uploaded to correct release
RELEASE=$(node -e "console.log(process.env.SENTRY_RELEASE || 'unknown')")
echo "Release: $RELEASE"
sentry-cli releases files "$RELEASE" list 2>/dev/null || echo "No files for release"

# Step 3: Use explain command for a specific event
# Get event ID from Sentry dashboard or API
sentry-cli sourcemaps explain \
  --org "$SENTRY_ORG" \
  --project "$SENTRY_PROJECT" \
  "EVENT_ID_HERE"

# Step 4: Check URL prefix alignment
# In browser DevTools Network tab, check the URL of your JS files:
# If served at: https://example.com/static/js/main.abc123.js
# Then url-prefix should be: ~/static/js

# Step 5: Validate source maps before upload
sentry-cli sourcemaps upload \
  --release="$RELEASE" \
  --url-prefix="~/static/js" \
  --validate \
  --dry-run \
  ./dist
```

### 4. Performance Monitoring Debugging

```typescript
// Why are transactions not appearing?

// Check 1: Is tracing enabled?
console.log('tracesSampleRate:', Sentry.getClient()?.getOptions().tracesSampleRate);
// If 0, no transactions are captured

// Check 2: Is tracesSampler returning 0?
Sentry.init({
  tracesSampler: (context) => {
    const rate = calculateRate(context);
    console.log(`[Sentry Sampler] ${context.name}: ${rate}`);
    return rate;
  },
});

// Check 3: Are spans being created?
await Sentry.startSpan(
  { name: 'debug.test', op: 'test' },
  async (span) => {
    console.log('Span created:', span ? 'YES' : 'NO');
    console.log('Span ID:', span?.spanContext().spanId);
    console.log('Trace ID:', span?.spanContext().traceId);
    await new Promise(r => setTimeout(r, 100));
  }
);
```

### 5. Network Connectivity Issues

```bash
# Test DNS resolution
dig +short o0.ingest.sentry.io

# Test HTTPS connectivity
curl -v https://sentry.io/api/0/ 2>&1 | head -30

# Test ingest endpoint (replace with your DSN host)
curl -v "https://o0.ingest.sentry.io/api/0/envelope/" \
  -H "Content-Type: application/x-sentry-envelope" 2>&1 | grep "< HTTP"

# Check for proxy interference
env | grep -i proxy
curl -v --proxy "" https://sentry.io/api/0/ 2>&1 | grep "HTTP"

# Test with a raw envelope (minimal event submission)
DSN_KEY=$(echo $SENTRY_DSN | sed 's/.*\/\///' | sed 's/@.*//')
DSN_HOST=$(echo $SENTRY_DSN | sed 's/.*@//' | sed 's/\/.*//')
PROJECT_ID=$(echo $SENTRY_DSN | sed 's/.*\///')

curl -X POST "https://$DSN_HOST/api/$PROJECT_ID/envelope/" \
  -H "Content-Type: application/x-sentry-envelope" \
  -H "X-Sentry-Auth: Sentry sentry_version=7, sentry_key=$DSN_KEY" \
  -d '{"event_id":"test123"}
{"type":"event"}
{"message":"connectivity test","level":"info"}'
```

### 6. SDK Conflict Resolution

```typescript
// Problem: Multiple Sentry.init() calls
// Symptom: Some events missing, inconsistent behavior

// Diagnosis: Search for multiple init calls
// grep -r "Sentry.init" --include="*.ts" --include="*.js" src/

// Fix: Single initialization point
// instrument.mjs should be the ONLY file calling Sentry.init()

// Problem: Multiple @sentry packages at different versions
// Diagnosis:
// npm ls @sentry/core @sentry/node @sentry/utils 2>/dev/null

// Fix: Align all versions
// npm install @sentry/node@8 @sentry/browser@8
```

### 7. Memory and Performance Impact

```typescript
// Measure Sentry's memory footprint
const before = process.memoryUsage();

Sentry.init({ /* config */ });

const after = process.memoryUsage();
console.log('Sentry memory overhead:', {
  heapUsed: `${((after.heapUsed - before.heapUsed) / 1024 / 1024).toFixed(1)} MB`,
  rss: `${((after.rss - before.rss) / 1024 / 1024).toFixed(1)} MB`,
});

// If overhead is too high:
// - Reduce maxBreadcrumbs (default 100 -> 20)
// - Remove unused integrations
// - Lower tracesSampleRate
// - Disable profiling and replay
```

### 8. Comprehensive Health Check Script

```bash
#!/bin/bash
# scripts/sentry-diagnose.sh
set -euo pipefail

echo "=== Sentry Diagnostic Report ==="

echo -e "\n--- Environment ---"
echo "Node.js: $(node --version 2>/dev/null || echo N/A)"
echo "SENTRY_DSN: $([ -n "${SENTRY_DSN:-}" ] && echo "SET" || echo "MISSING")"
echo "SENTRY_RELEASE: ${SENTRY_RELEASE:-NOT SET}"
echo "SENTRY_ENVIRONMENT: ${SENTRY_ENVIRONMENT:-NOT SET}"
echo "NODE_ENV: ${NODE_ENV:-NOT SET}"

echo -e "\n--- SDK Packages ---"
npm list 2>/dev/null | grep @sentry || echo "No Sentry packages"

echo -e "\n--- CLI ---"
sentry-cli --version 2>/dev/null || echo "Not installed"
sentry-cli info 2>/dev/null || echo "Auth failed or not configured"

echo -e "\n--- Network ---"
curl -s -o /dev/null -w "sentry.io: HTTP %{http_code} (%{time_total}s)\n" \
  https://sentry.io/api/0/ 2>/dev/null || echo "UNREACHABLE"

echo -e "\n--- Source Maps ---"
RELEASE="${SENTRY_RELEASE:-unknown}"
sentry-cli releases files "$RELEASE" list 2>/dev/null | head -5 \
  || echo "No files or auth failed"

echo -e "\n=== Done ==="
```

## Output
- Root cause identified for SDK issues via systematic diagnosis
- Source map problems resolved with explain command
- Event capture verified working with test events
- Network connectivity confirmed to Sentry endpoints
- Performance impact measured and optimized

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `debug: true` shows nothing | SDK not initialized | Check import order; use `--import` flag for ESM |
| `flush()` always times out | Network blocking outbound | Check firewall, proxy, VPN; test with curl |
| Source maps resolve wrong file | URL prefix mismatch | Run `sourcemaps explain EVENT_ID` for exact mismatch |
| Duplicate events | Multiple `Sentry.init()` calls | Search codebase for all init calls, consolidate to one |
| High memory usage | Too many breadcrumbs or integrations | Reduce `maxBreadcrumbs`, remove unused integrations |

## Resources
- [Troubleshooting](https://docs.sentry.io/platforms/javascript/troubleshooting/)
- [Source Maps Troubleshooting](https://docs.sentry.io/platforms/javascript/sourcemaps/troubleshooting_js/)
- [Source Maps Explain](https://docs.sentry.io/cli/sourcemaps/#explain)
- [Transport Configuration](https://docs.sentry.io/platforms/javascript/configuration/transports/)
