---
name: sentry-rate-limits
description: |
  Manage Sentry rate limits, quotas, and event volume optimization.
  Use when hitting rate limits, optimizing event volume,
  or managing Sentry costs.
  Trigger with phrases like "sentry rate limit", "sentry quota",
  "reduce sentry events", "sentry 429".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, cost-optimization, rate-limiting, quotas]

---
# Sentry Rate Limits

## Prerequisites
- Understanding of current event volume (check sentry.io/stats/)
- Sentry billing plan and quota known
- High-volume error sources identified
- Noisy error patterns documented

## Instructions

### 1. Understanding Sentry's Rate Limiting

When you exceed your quota, Sentry returns `429 Too Many Requests` with a `Retry-After` header. The SDK respects this and stops sending events until the cooldown expires. Events during this window are permanently dropped.

**Quota categories (billed separately):**
- Errors (exceptions and messages)
- Transactions (performance spans)
- Replays (session recordings)
- Attachments (file uploads)
- Profiles (code profiling data)

### 2. Client-Side Sampling (First Line of Defense)

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Error sampling: 0.0 to 1.0
  sampleRate: 0.5, // Capture 50% of errors

  // Transaction sampling: 0.0 to 1.0
  tracesSampleRate: 0.01, // Capture 1% of transactions

  // Dynamic transaction sampling — most effective for cost control
  tracesSampler: (samplingContext) => {
    const { name } = samplingContext;

    // Drop noisy health checks entirely
    if (name === 'GET /health' || name === 'GET /readiness') return 0;

    // High-value: payment flows at 100%
    if (name?.includes('/api/payment')) return 1.0;

    // Medium-value: API routes at 10%
    if (name?.startsWith('GET /api/')) return 0.1;

    // Low-value: static assets at 0%
    if (name?.startsWith('GET /static/')) return 0;

    return 0.05; // Default 5%
  },
});
```

### 3. Client-Side Filtering with beforeSend

Filter events before they count against your quota:

```typescript
Sentry.init({
  beforeSend(event, hint) {
    const error = hint?.originalException;

    // Drop browser extension errors
    if (event.exception?.values?.some(e =>
      e.stacktrace?.frames?.some(f =>
        f.filename?.includes('extensions://') ||
        f.filename?.includes('moz-extension://')
      )
    )) {
      return null;
    }

    // Drop specific error types
    if (error?.name === 'AbortError') return null;
    if (error?.message?.match(/ResizeObserver loop/)) return null;
    if (error?.message?.match(/Non-Error promise rejection/)) return null;

    return event;
  },

  // Pattern-based filtering
  ignoreErrors: [
    'ResizeObserver loop completed with undelivered notifications',
    'Non-Error promise rejection captured',
    /Loading chunk \d+ failed/,
    'Network request failed',
    'Failed to fetch',
    'AbortError',
    /^Script error\.?$/,
  ],

  // Block errors from third-party scripts
  denyUrls: [
    /extensions\//i,
    /^chrome:\/\//i,
    /^moz-extension:\/\//i,
    /hotjar\.com/,
    /google-analytics\.com/,
  ],
});
```

### 4. Server-Side Inbound Data Filters

Configure in Sentry dashboard: **Project Settings > Inbound Filters**

These filters run BEFORE quota — filtered events are free:
- **Legacy browsers** — drop IE9, old Safari, etc.
- **Browser extensions** — filter extension-caused errors
- **Localhost events** — filter events from localhost/127.0.0.1
- **Web crawlers** — filter bot-generated errors
- **Filtered releases** — block specific release versions
- **Error message patterns** — custom regex filters

### 5. Set Project Rate Limits

Via dashboard: **Project Settings > Client Keys > Rate Limiting**

```bash
# Or via API — set rate limit to 1000 events/hour
curl -X PUT \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rateLimit": {"window": 3600, "count": 1000}}' \
  "https://sentry.io/api/0/projects/$SENTRY_ORG/$SENTRY_PROJECT/keys/KEY_ID/"
```

### 6. Reduce Event Payload Size

```typescript
Sentry.init({
  // Reduce breadcrumb count (default: 100)
  maxBreadcrumbs: 30,

  // Limit string length in event data
  maxValueLength: 500, // Default: 250

  // Reduce request body size
  beforeSend(event) {
    // Truncate large request bodies
    if (event.request?.data && typeof event.request.data === 'string') {
      event.request.data = event.request.data.substring(0, 1000);
    }
    return event;
  },
});
```

### 7. Deduplication

The SDK includes built-in deduplication, but you can enhance it:

```typescript
Sentry.init({
  integrations: [
    Sentry.dedupeIntegration(), // Built-in, enabled by default
  ],

  beforeSend(event) {
    // Custom dedup: group similar errors
    if (event.exception?.values?.[0]) {
      const { type, value } = event.exception.values[0];
      // Normalize dynamic values in error messages
      event.fingerprint = [type || 'unknown', value?.replace(/\d+/g, 'N') || ''];
    }
    return event;
  },
});
```

### 8. Monitor Quota Usage

```bash
# Check organization usage stats
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/stats_v2/?\
field=sum(quantity)&groupBy=category&interval=1d&statsPeriod=7d" \
  | python3 -m json.tool

# Set up spend alerts in Sentry dashboard:
# Settings > Subscription > Spend Allocations > Alerts
```

### 9. Spike Protection

Enable in **Organization Settings > Spike Protection**. When enabled, Sentry detects sudden increases in event volume and temporarily rate-limits the project, preventing quota exhaustion from error storms.

## Output
- Sampling rates configured to reduce event volume
- Client-side filtering dropping noisy errors before they count against quota
- Server-side inbound filters enabled (free filtering)
- Project rate limits set to cap maximum events
- Spend alerts configured for budget monitoring
- Spike protection enabled for burst protection

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Quota exhausted for billing period | Lower `sampleRate`/`tracesSampleRate`, add `ignoreErrors`, set project rate limits |
| Events silently dropped | Client-side rate limit active | SDK respects `Retry-After` header; reduce volume at source |
| Critical errors missed | `sampleRate` too low | Use `beforeSend` to always capture critical errors at rate 1.0 |
| Quota used up early in period | No per-project limits set | Set hourly rate limits per project to spread quota evenly |
| Spike consuming entire quota | No spike protection | Enable spike protection in organization settings |

## Resources
- [Quota Management](https://docs.sentry.io/pricing/quotas/)
- [Manage Error Quota](https://docs.sentry.io/pricing/quotas/manage-event-stream-guide/)
- [Sampling](https://docs.sentry.io/platforms/javascript/configuration/sampling/)
- [Filtering](https://docs.sentry.io/platforms/javascript/configuration/filtering/)
