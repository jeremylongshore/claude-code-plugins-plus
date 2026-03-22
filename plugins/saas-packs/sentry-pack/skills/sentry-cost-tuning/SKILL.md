---
name: sentry-cost-tuning
description: |
  Optimize Sentry costs and event volume.
  Use when managing Sentry billing, reducing event volume,
  or optimizing quota usage.
  Trigger with phrases like "reduce sentry costs", "sentry billing",
  "sentry quota", "optimize sentry spend".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, cost-optimization, billing, quotas]

---
# Sentry Cost Tuning

## Prerequisites
- Current Sentry billing plan and quota known
- Event volume metrics available (sentry.io > Stats)
- High-volume error sources identified
- Cost reduction target defined

## Instructions

### 1. Understand Sentry Billing Categories

Each category is billed independently:
| Category | What counts | Typical cost driver |
|----------|------------|-------------------|
| Errors | `captureException`, `captureMessage`, unhandled errors | Noisy errors, error storms |
| Transactions | Performance spans/traces | High-traffic API endpoints |
| Replays | Session recordings | High-traffic frontend apps |
| Attachments | File uploads with events | Large crash reports |
| Profiles | Code profiling data | Always-on profiling |

### 2. Audit Current Usage

```bash
# Check usage stats for the last 30 days
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/stats_v2/?\
field=sum(quantity)&groupBy=category&interval=1d&statsPeriod=30d" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for group in data.get('groups', []):
    category = group['by']['category']
    total = sum(s['totals']['sum(quantity)'] for s in [group])
    print(f'{category}: {total:,} events')
"
```

### 3. Error Volume Reduction (Biggest Impact)

```typescript
Sentry.init({
  // A. Sample non-critical errors
  sampleRate: 0.5, // 50% error sampling saves 50% cost

  // B. Filter noisy errors that don't need tracking
  ignoreErrors: [
    'ResizeObserver loop completed',
    'Non-Error promise rejection',
    /Loading chunk \d+ failed/,
    'Network request failed',
    'Failed to fetch',
    'AbortError',
    /^Script error\.?$/,
    'TypeError: cancelled',
    'TypeError: NetworkError',
  ],

  // C. Block third-party script errors
  denyUrls: [
    /extensions\//i,
    /^chrome:\/\//i,
    /^moz-extension:\/\//i,
    /hotjar\.com/,
    /google-analytics\.com/,
    /googletagmanager\.com/,
  ],

  // D. Smart filtering with beforeSend
  beforeSend(event, hint) {
    const error = hint?.originalException;

    // Drop browser extension errors
    if (event.exception?.values?.some(e =>
      e.stacktrace?.frames?.some(f =>
        f.filename?.includes('extension')
      )
    )) return null;

    // Drop known non-actionable errors
    if (error?.message?.match(/timeout/i) && error?.message?.match(/health/i)) {
      return null;
    }

    return event;
  },
});
```

### 4. Transaction Volume Reduction (Second Biggest Impact)

```typescript
Sentry.init({
  // A. Low global rate
  tracesSampleRate: 0.01, // 1% baseline

  // B. Smart sampling per endpoint
  tracesSampler: ({ name }) => {
    // Zero-value: health checks, bots, static
    if (name?.match(/\/(health|ping|ready|robots\.txt)/)) return 0;
    if (name?.match(/\.(js|css|png|jpg|ico)/)) return 0;

    // Business-critical: higher rates
    if (name?.includes('/payment') || name?.includes('/checkout')) return 0.5;
    if (name?.includes('/api/')) return 0.05;

    return 0.01; // Default 1%
  },
});
```

### 5. Reduce Event Payload Size

```typescript
Sentry.init({
  maxBreadcrumbs: 20, // Default 100 — saves bandwidth
  maxValueLength: 250, // Truncate long strings

  beforeSend(event) {
    // Truncate large request bodies
    if (event.request?.data && typeof event.request.data === 'string') {
      if (event.request.data.length > 1000) {
        event.request.data = event.request.data.substring(0, 1000) + '...[truncated]';
      }
    }

    // Remove unnecessary headers
    if (event.request?.headers) {
      const keep = ['content-type', 'user-agent', 'referer'];
      event.request.headers = Object.fromEntries(
        Object.entries(event.request.headers)
          .filter(([k]) => keep.includes(k.toLowerCase()))
      );
    }

    return event;
  },
});
```

### 6. Disable Unused Features

```typescript
Sentry.init({
  // Disable features you're not using
  // Each saves quota in its respective category

  // Disable replays if not needed (saves replay quota)
  replaysSessionSampleRate: 0,
  replaysOnErrorSampleRate: 0,

  // Disable profiling if not needed (saves profile quota)
  profilesSampleRate: 0,

  // Disable performance if not needed (saves transaction quota)
  tracesSampleRate: 0,
});
```

### 7. Server-Side Inbound Filters (Free)

These filter events BEFORE they count against quota:
- **Project Settings > Inbound Filters**
- Enable: Legacy browsers, browser extensions, localhost, web crawlers
- Add custom error message filters for patterns you want to ignore

### 8. Set Spend Alerts and Rate Limits

```bash
# Set project-level rate limit (events per hour)
# Dashboard: Project Settings > Client Keys > Rate Limiting

# Set organization spend alerts:
# Settings > Subscription > Spend Allocations
# Alert at 80% of monthly budget

# Spike protection (Organization Settings > Spike Protection)
# Automatically rate-limits during sudden spikes
```

### 9. Cost Projection Template

```
Current plan: Team ($26/month)
Included:  50K errors, 100K transactions, 500 replays
Current:   45K errors, 800K transactions, 0 replays
Overage:   0 errors, 700K transactions x $0.000025 = $17.50/month

After optimization:
- tracesSampler: 800K -> 40K transactions (95% reduction)
- ignoreErrors: 45K -> 30K errors (33% reduction)
- Projected overage: $0
- Annual savings: ~$210
```

## Output
- Error volume reduced via ignoreErrors, denyUrls, and beforeSend filtering
- Transaction volume reduced via tracesSampler with endpoint-specific rates
- Unused features disabled (replays, profiling)
- Server-side inbound filters enabled (free filtering)
- Spend alerts and rate limits preventing quota overruns

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Critical errors missed | `sampleRate` too aggressive | Use `beforeSend` to always pass critical errors regardless of sample rate |
| No performance data | `tracesSampleRate: 0` | Set to at least 0.01 for business-critical endpoints |
| Overage charges | No rate limits set | Set project rate limits and organization spend alerts |
| Spike consuming quota | No spike protection | Enable in Organization Settings > Spike Protection |

## Resources
- [Quota Management](https://docs.sentry.io/pricing/quotas/)
- [Manage Error Quota](https://docs.sentry.io/pricing/quotas/manage-event-stream-guide/)
- [Pricing](https://sentry.io/pricing/)
- [Filtering](https://docs.sentry.io/platforms/javascript/configuration/filtering/)
