---
name: posthog-performance-tuning
description: |
  Optimize PostHog performance: local flag evaluation, client batching config,
  event sampling, efficient HogQL queries, and serverless flush patterns.
  Trigger: "posthog performance", "optimize posthog", "posthog latency",
  "posthog caching", "posthog slow", "posthog batch", "posthog fast".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, api, performance]
---

# PostHog Performance Tuning

## Overview

Optimize PostHog for production workloads. The biggest performance wins are: local feature flag evaluation (eliminates network calls), proper batching configuration, event sampling for high-volume apps, and efficient HogQL queries with date filters.

## Prerequisites

- `posthog-node` and/or `posthog-js` installed
- Personal API key (`phx_...`) for local flag evaluation
- Feature flags configured (if applicable)

## Instructions

### Step 1: Enable Local Feature Flag Evaluation

The single biggest performance improvement. Without local evaluation, every `getFeatureFlag()` call makes a network request (~50-200ms). With local evaluation, flag definitions are cached and evaluation is instant (~0.1ms).

```typescript
import { PostHog } from 'posthog-node';

const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  host: 'https://us.i.posthog.com',
  // This is the key: personal API key enables local flag evaluation
  personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY,
  // Flag definitions are polled every 30 seconds by default
  // Adjust if you need faster flag updates:
  // featureFlagsPollingInterval: 10000, // 10 seconds
});

// With personalApiKey set, this evaluates locally (no network call)
const variant = await posthog.getFeatureFlag('pricing-experiment', 'user-123', {
  personProperties: { plan: 'pro', country: 'US' },
});

// Get all flags at once (still local, still fast)
const allFlags = await posthog.getAllFlags('user-123', {
  personProperties: { plan: 'pro' },
  groupProperties: { company: { industry: 'SaaS' } },
});
```

### Step 2: Optimize Client Batching

```typescript
// Production: batch events for network efficiency
const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  host: 'https://us.i.posthog.com',
  flushAt: 20,           // Send batch when 20 events accumulated (default)
  flushInterval: 10000,  // Or flush every 10 seconds (default)
  requestTimeout: 10000, // 10 second timeout per request
  maxRetries: 3,         // Retry failed sends
});

// Serverless: flush immediately (function may exit)
const serverless = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  host: 'https://us.i.posthog.com',
  flushAt: 1,       // Send every event immediately
  flushInterval: 0, // Don't wait
});

// CRITICAL: Always shutdown before process exits
process.on('SIGTERM', async () => {
  await posthog.shutdown();
  process.exit(0);
});
```

### Step 3: Event Sampling (Browser)

```typescript
import posthog from 'posthog-js';

posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://us.i.posthog.com',
  before_send: (event) => {
    // Always capture business-critical events
    const alwaysCapture = ['purchase', 'signup', 'subscription_started', 'subscription_canceled'];
    if (alwaysCapture.includes(event.event)) return event;

    // Sample high-volume events
    const sampleRates: Record<string, number> = {
      '$pageview': 1.0,        // Keep all pageviews
      '$pageleave': 0.5,       // Sample 50%
      '$autocapture': 0.1,     // Sample 10% of autocapture
      'scroll_depth': 0.05,    // Sample 5%
    };

    const rate = sampleRates[event.event] ?? 0.5;
    if (Math.random() >= rate) return null; // Drop event

    // Tag sampled events so you can adjust in analysis
    event.properties = { ...event.properties, $sample_rate: rate };
    return event;
  },
});
```

### Step 4: Efficient HogQL Queries

```typescript
async function queryPostHog(hogql: string) {
  const response = await fetch(
    `https://app.posthog.com/api/projects/${process.env.POSTHOG_PROJECT_ID}/query/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.POSTHOG_PERSONAL_API_KEY}`,
      },
      body: JSON.stringify({
        query: { kind: 'HogQLQuery', query: hogql },
      }),
    }
  );
  return response.json();
}

// FAST: Filtered by time, limited results
const fast = await queryPostHog(`
  SELECT
    properties.$current_url AS url,
    count() AS views,
    uniq(distinct_id) AS visitors
  FROM events
  WHERE event = '$pageview'
    AND timestamp > now() - interval 7 day
  GROUP BY url
  ORDER BY views DESC
  LIMIT 50
`);

// SLOW (avoid): No time filter, scans entire table
// SELECT * FROM events WHERE event = '$pageview'

// OPTIMIZED: Use subqueries for complex analysis
const retention = await queryPostHog(`
  SELECT
    dateTrunc('week', first_seen) AS cohort_week,
    dateTrunc('week', timestamp) AS activity_week,
    uniq(distinct_id) AS users
  FROM events
  INNER JOIN (
    SELECT distinct_id, min(timestamp) AS first_seen
    FROM events
    WHERE event = 'user_signed_up'
      AND timestamp > now() - interval 90 day
    GROUP BY distinct_id
  ) AS cohorts ON events.distinct_id = cohorts.distinct_id
  WHERE timestamp > now() - interval 90 day
  GROUP BY cohort_week, activity_week
  ORDER BY cohort_week, activity_week
`);
```

### Step 5: Session Recording Performance

```typescript
// Limit session recording to reduce data volume and cost
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://us.i.posthog.com',
  session_recording: {
    // Only record 10% of sessions
    sampleRate: 0.1,
    // Minimum session duration to record (skip quick bounces)
    minimumDurationMilliseconds: 5000,
    // Mask all text inputs by default
    maskAllInputs: true,
    // Mask specific CSS selectors
    maskTextSelector: '.sensitive-data',
  },
});
```

## Performance Benchmarks

| Operation | Without Optimization | With Optimization |
|-----------|---------------------|-------------------|
| Feature flag evaluation | 50-200ms (network) | <1ms (local eval) |
| Event capture | Individual sends | Batched (20 events/req) |
| HogQL query (7d) | 2-5s | <1s (with filters) |
| HogQL query (no filter) | 30-60s (timeout risk) | N/A (always filter) |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Events dropped on exit | No shutdown hook | Add `posthog.shutdown()` to SIGTERM handler |
| Flag evaluation slow | No `personalApiKey` | Add personal API key for local evaluation |
| High event cost | Capturing everything | Implement `before_send` sampling |
| HogQL timeout | No date filter | Always include `timestamp > now() - interval N day` |
| Session recordings large | Recording all sessions | Set `sampleRate` to 0.1-0.25 |

## Output

- Local feature flag evaluation (<1ms per check)
- Optimized batching configuration
- Event sampling with `before_send`
- Efficient HogQL query patterns
- Session recording sampling

## Resources

- [PostHog Local Evaluation](https://posthog.com/docs/feature-flags/local-evaluation)
- [PostHog Node SDK Config](https://posthog.com/docs/libraries/node)
- [HogQL Documentation](https://posthog.com/docs/sql)
- [Session Recording Config](https://posthog.com/docs/session-replay/how-to-control-which-sessions-you-record)
