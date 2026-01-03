---
name: sentry-cost-tuning
description: |
  Optimize Sentry costs and event volume.
  Use when managing Sentry billing, reducing event volume,
  or optimizing quota usage.
  Trigger with phrases like "reduce sentry costs", "sentry billing",
  "sentry quota", "optimize sentry spend".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Cost Tuning

## Overview
Strategies to optimize Sentry costs while maintaining visibility.

## Understanding Sentry Pricing

### Event Types
- **Errors** - Exception events
- **Transactions** - Performance traces
- **Replays** - Session replays
- **Attachments** - Files attached to events

### Cost Factors
1. Total event volume
2. Data retention period
3. Team size
4. Features used

## Reduce Error Volume

### 1. Client-Side Filtering
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Sample errors
  sampleRate: 0.5, // Send 50% of errors

  // Ignore common noisy errors
  ignoreErrors: [
    'ResizeObserver loop limit exceeded',
    'Non-Error promise rejection',
    /Loading chunk \d+ failed/,
    'Network request failed',
    'AbortError',
  ],

  // Ignore errors from specific URLs
  denyUrls: [
    /extensions\//i,
    /^chrome:\/\//i,
    /^moz-extension:\/\//i,
    /^safari-extension:\/\//i,
  ],
});
```

### 2. Server-Side Filtering (Inbound Filters)
Enable in Sentry Dashboard:
1. Project Settings > Inbound Filters
2. Enable:
   - Legacy browsers
   - Browser extensions
   - Web crawlers
   - Filtered by IP

### 3. Rate Limits
```bash
# Set project rate limit
curl -X PUT \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"options": {"sentry:rate-limit": 1000}}' \
  "https://sentry.io/api/0/projects/$ORG/$PROJECT/"
```

## Reduce Transaction Volume

### Aggressive Sampling
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Low sample rate in production
  tracesSampleRate: 0.01, // 1%

  // Or dynamic sampling
  tracesSampler: (ctx) => {
    // Never trace health checks
    if (ctx.transactionContext.name.includes('health')) return 0;

    // Very low rate for common endpoints
    if (ctx.transactionContext.name.includes('/api/')) return 0.001;

    return 0.01;
  },
});
```

### Skip Unimportant Transactions
```typescript
tracesSampler: (ctx) => {
  const name = ctx.transactionContext.name;

  // Skip static assets
  if (/\.(js|css|png|jpg|svg)$/.test(name)) return 0;

  // Skip bots
  const userAgent = ctx.request?.headers?.['user-agent'];
  if (userAgent?.includes('bot')) return 0;

  return 0.05;
},
```

## Optimize What You Send

### Reduce Event Size
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Limit string lengths
  maxValueLength: 250,

  // Limit breadcrumbs
  maxBreadcrumbs: 20,

  // Strip large data
  beforeSend(event) {
    // Remove large request bodies
    if (event.request?.data) {
      const size = JSON.stringify(event.request.data).length;
      if (size > 1000) {
        event.request.data = '[TRUNCATED]';
      }
    }
    return event;
  },
});
```

### Disable Unused Features
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Disable session tracking if not needed
  autoSessionTracking: false,

  // Disable profiling if not needed
  profilesSampleRate: 0,

  // Disable replay if not needed
  replaysSessionSampleRate: 0,
  replaysOnErrorSampleRate: 0,
});
```

## Cost Monitoring

### Track Usage
```bash
# Get current usage via API
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$ORG/stats/v2/?field=sum(quantity)&category=error&category=transaction"
```

### Set Alerts
In Sentry Dashboard:
1. Settings > Subscription
2. Configure spend alerts
3. Set notification thresholds

## Cost-Effective Architecture

### Tiered Environments
```typescript
const config = {
  development: {
    sampleRate: 1.0,
    tracesSampleRate: 1.0,
    enabled: false, // Don't send dev errors
  },
  staging: {
    sampleRate: 1.0,
    tracesSampleRate: 0.5,
    enabled: true,
  },
  production: {
    sampleRate: 0.5,
    tracesSampleRate: 0.01,
    enabled: true,
  },
};

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  ...config[process.env.NODE_ENV],
});
```

### Per-Project Budgets
- Allocate quota per project
- Set rate limits per project
- Monitor high-volume projects

## Monthly Cost Estimation

```
Errors: 100,000/month × $0.00025 = $25
Transactions: 1,000,000/month × $0.000025 = $25
Total: ~$50/month

After optimization (50% reduction):
Errors: 50,000/month = $12.50
Transactions: 100,000/month = $2.50
Total: ~$15/month
```

## Resources
- [Sentry Pricing](https://sentry.io/pricing/)
- [Quota Management](https://docs.sentry.io/product/accounts/quotas/)
