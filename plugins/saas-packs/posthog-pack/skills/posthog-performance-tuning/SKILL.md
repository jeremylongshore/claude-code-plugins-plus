---
name: posthog-performance-tuning
description: |
  Optimize PostHog API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for PostHog integrations.
  Trigger with phrases like "posthog performance", "optimize posthog",
  "posthog latency", "posthog caching", "posthog slow", "posthog batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# PostHog Performance Tuning

## Overview
Optimize PostHog event capture, feature flag evaluation, and analytics queries. Focus on client-side batching, local flag evaluation to eliminate network calls, event sampling for high-volume apps, and efficient HogQL queries.

## Prerequisites
- PostHog project with API key
- `posthog-node` SDK installed
- Understanding of PostHog event model
- Feature flags configured (if applicable)

## Instructions

### Step 1: Configure Optimal Client Batching
```typescript
import { PostHog } from 'posthog-node';

const posthog = new PostHog(process.env.POSTHOG_API_KEY!, {
  host: 'https://us.i.posthog.com',
  flushAt: 20,         // Batch size before sending (default 20)
  flushInterval: 5000, // Max wait time in ms (default 10000)
  requestTimeout: 10000,
  maxRetries: 3,
  // Disable for tests
  ...(process.env.NODE_ENV === 'test' && { enable: false }),
});

// Ensure events are sent before process exits
process.on('SIGTERM', async () => {
  await posthog.shutdown();
  process.exit(0);
});
```

### Step 2: Local Feature Flag Evaluation
```typescript
// Fetch flag definitions once, evaluate locally (no network per-call)
let flagDefinitions: any = null;
let lastFetch = 0;
const CACHE_TTL = 30000; // 30 seconds

async function getFeatureFlag(
  flagKey: string,
  distinctId: string,
  properties?: Record<string, any>
) {
  // Refresh definitions periodically
  if (!flagDefinitions || Date.now() - lastFetch > CACHE_TTL) {
    flagDefinitions = await posthog.getAllFlags(distinctId, {
      personProperties: properties,
    });
    lastFetch = Date.now();
  }

  return flagDefinitions[flagKey] ?? false;
}

// For boolean flags in hot paths
async function isFeatureEnabled(flagKey: string, userId: string) {
  const flags = await posthog.getAllFlags(userId);
  return !!flags[flagKey];
}
```

### Step 3: Event Sampling for High-Volume Capture
```typescript
function shouldSample(eventName: string): boolean {
  const sampleRates: Record<string, number> = {
    '$pageview': 1.0,       // Capture all pageviews
    'button_clicked': 1.0,  // Capture all clicks
    'api_call': 0.1,        // Sample 10% of API calls
    'scroll_depth': 0.05,   // Sample 5% of scroll events
  };

  const rate = sampleRates[eventName] ?? 0.5;
  return Math.random() < rate;
}

function captureWithSampling(
  distinctId: string,
  event: string,
  properties?: Record<string, any>
) {
  if (!shouldSample(event)) return;

  posthog.capture({
    distinctId,
    event,
    properties: {
      ...properties,
      $sample_rate: getSampleRate(event),
    },
  });
}
```

### Step 4: Efficient HogQL Queries
```typescript
async function queryPostHog(hogql: string) {
  const response = await fetch(
    `https://us.i.posthog.com/api/projects/${process.env.POSTHOG_PROJECT_ID}/query/`,
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

// Optimized: filter early, limit results
const efficientQuery = `
  SELECT
    properties.$current_url AS url,
    count() AS views,
    uniq(distinct_id) AS unique_visitors
  FROM events
  WHERE event = '$pageview'
    AND timestamp > now() - interval 7 day
  GROUP BY url
  ORDER BY views DESC
  LIMIT 50
`;
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Events dropped | Flush not called on exit | Add shutdown hook with `posthog.shutdown()` |
| Flag evaluation slow | Network call per evaluation | Use `getAllFlags` with caching |
| High event volume cost | Capturing everything | Implement sampling for noisy events |
| HogQL timeout | Unfiltered full-table scan | Add date filters and LIMIT |

## Examples

### Feature Flag A/B Test Tracking
```typescript
async function trackExperiment(userId: string, experimentKey: string) {
  const variant = await posthog.getFeatureFlag(experimentKey, userId);

  posthog.capture({
    distinctId: userId,
    event: 'experiment_viewed',
    properties: {
      experiment: experimentKey,
      variant: variant || 'control',
    },
  });

  return variant;
}
```

## Resources
- [PostHog Node SDK](https://posthog.com/docs/libraries/node)
- [PostHog Feature Flags](https://posthog.com/docs/feature-flags)
- [HogQL Documentation](https://posthog.com/docs/hogql)
