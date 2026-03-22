---
name: posthog-observability
description: |
  Monitor PostHog integration health: event ingestion rates, feature flag
  evaluation latency, billing volume tracking, and Prometheus/Grafana alerting.
  Trigger: "posthog monitoring", "posthog metrics", "posthog observability",
  "monitor posthog", "posthog alerts", "posthog dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, monitoring, observability, dashboard]
---

# PostHog Observability

## Overview

Monitor PostHog integration health with four key signals: event ingestion rate (are events flowing?), feature flag evaluation latency (are flags fast enough for hot paths?), event volume by type (detect instrumentation regressions), and API rate limit consumption (are we approaching 429s?).

## Prerequisites

- PostHog project with personal API key (`phx_...`)
- Application instrumented with PostHog SDK
- Prometheus/Grafana or equivalent monitoring stack (optional)

## Instructions

### Step 1: Event Ingestion Health Check

```bash
set -euo pipefail
# Check if events are flowing (last 24 hours)
curl "https://app.posthog.com/api/projects/$POSTHOG_PROJECT_ID/query/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT toStartOfHour(timestamp) AS hour, count() AS events FROM events WHERE timestamp > now() - interval 24 hour GROUP BY hour ORDER BY hour"
    }
  }' | jq '.results | map({hour: .[0], events: .[1]}) | .[-3:]'
```

### Step 2: Instrument Flag Evaluation Latency

```typescript
// posthog-instrumented.ts
import { PostHog } from 'posthog-node';

const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  host: 'https://us.i.posthog.com',
  personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY,
});

// Wrap flag evaluation with timing
async function getFlag(flagKey: string, userId: string): Promise<any> {
  const start = performance.now();
  const value = await posthog.getFeatureFlag(flagKey, userId);
  const durationMs = performance.now() - start;

  // Emit metrics to your monitoring system
  emitHistogram('posthog_flag_eval_duration_ms', durationMs, { flag: flagKey });
  emitCounter('posthog_flag_evals_total', 1, { flag: flagKey, result: String(value) });

  // Alert on slow evaluations (likely means local eval not configured)
  if (durationMs > 200) {
    console.warn(`[PostHog] Slow flag eval: ${flagKey} took ${durationMs.toFixed(0)}ms — check personalApiKey`);
  }

  return value;
}

// Example: emit to Prometheus via prom-client
import { Histogram, Counter, Gauge } from 'prom-client';

const flagDuration = new Histogram({
  name: 'posthog_flag_eval_duration_ms',
  help: 'PostHog feature flag evaluation duration',
  labelNames: ['flag'],
  buckets: [1, 5, 10, 50, 100, 200, 500, 1000],
});

const flagEvals = new Counter({
  name: 'posthog_flag_evals_total',
  help: 'Total PostHog feature flag evaluations',
  labelNames: ['flag', 'result'],
});

function emitHistogram(name: string, value: number, labels: Record<string, string>) {
  flagDuration.observe(labels, value);
}

function emitCounter(name: string, value: number, labels: Record<string, string>) {
  flagEvals.inc(labels, value);
}
```

### Step 3: Monitor Event Volume and Billing

```typescript
// Run on a cron (e.g., every 6 hours)
async function checkEventVolume() {
  const result = await fetch(
    `https://app.posthog.com/api/projects/${process.env.POSTHOG_PROJECT_ID}/query/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.POSTHOG_PERSONAL_API_KEY}`,
      },
      body: JSON.stringify({
        query: {
          kind: 'HogQLQuery',
          query: `
            SELECT
              count() AS events_this_month,
              uniq(distinct_id) AS unique_users,
              count() / dateDiff('day', toStartOfMonth(now()), now()) AS daily_avg
            FROM events
            WHERE timestamp > toStartOfMonth(now())
          `,
        },
      }),
    }
  );

  const data = await result.json();
  const [eventsThisMonth, uniqueUsers, dailyAvg] = data.results[0];
  const projectedMonthly = dailyAvg * 30;
  const FREE_TIER = 1_000_000;

  const metrics = {
    events_this_month: eventsThisMonth,
    unique_users: uniqueUsers,
    daily_average: Math.round(dailyAvg),
    projected_monthly: Math.round(projectedMonthly),
    pct_of_free_tier: Math.round((projectedMonthly / FREE_TIER) * 100),
  };

  // Emit gauge metrics
  const volumeGauge = new Gauge({
    name: 'posthog_events_month_total',
    help: 'PostHog events this month',
  });
  volumeGauge.set(eventsThisMonth);

  // Alert if approaching limits
  if (projectedMonthly > FREE_TIER * 0.8) {
    await sendAlert(`PostHog: projected ${Math.round(projectedMonthly / 1000)}K events this month (free tier: 1M)`);
  }

  return metrics;
}
```

### Step 4: Prometheus Alert Rules

```yaml
# prometheus/posthog-alerts.yml
groups:
  - name: posthog
    rules:
      - alert: PostHogIngestionDrop
        expr: |
          rate(posthog_events_captured_total[1h])
          < rate(posthog_events_captured_total[1h] offset 1d) * 0.5
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "PostHog event ingestion dropped >50% vs yesterday"

      - alert: PostHogFlagEvalSlow
        expr: |
          histogram_quantile(0.95, rate(posthog_flag_eval_duration_ms_bucket[5m])) > 200
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PostHog flag eval P95 > 200ms — check if personalApiKey is set"

      - alert: PostHogBillingAlert
        expr: posthog_events_month_total > 800000
        labels:
          severity: info
        annotations:
          summary: "PostHog events approaching 1M free tier limit"

      - alert: PostHogCaptureErrors
        expr: rate(posthog_capture_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "PostHog capture errors elevated — events may be lost"
```

### Step 5: Health Check Dashboard Queries

```typescript
// Dashboard panels to track PostHog health
const dashboardQueries = {
  // Events per hour (last 24h)
  eventRate: `
    SELECT toStartOfHour(timestamp) AS hour, count() AS events
    FROM events WHERE timestamp > now() - interval 24 hour
    GROUP BY hour ORDER BY hour
  `,

  // Events by type (last 7 days)
  eventsByType: `
    SELECT event, count() AS total
    FROM events WHERE timestamp > now() - interval 7 day
    GROUP BY event ORDER BY total DESC LIMIT 15
  `,

  // Unique users per day (last 30 days)
  dailyActiveUsers: `
    SELECT toDate(timestamp) AS day, uniq(distinct_id) AS users
    FROM events WHERE timestamp > now() - interval 30 day
    GROUP BY day ORDER BY day
  `,

  // Event ingestion latency estimate
  ingestionFreshness: `
    SELECT max(timestamp) AS latest_event,
           dateDiff('second', max(timestamp), now()) AS seconds_behind
    FROM events
  `,
};
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Zero events for 1h+ | SDK not initialized or API down | Check PostHog status, verify SDK init |
| Flag eval >200ms | No `personalApiKey` | Add personal key for local evaluation |
| Event volume spike | New feature autocapturing | Review autocapture config, add filters |
| Rate limit 429 | Too many API queries | Cache results, reduce poll frequency |

## Output

- Flag evaluation latency instrumentation
- Event volume and billing monitoring
- Prometheus alert rules for PostHog health
- HogQL dashboard queries for key metrics
- Automated alerts for ingestion drops and billing limits

## Resources

- [PostHog API Overview](https://posthog.com/docs/api)
- [PostHog HogQL](https://posthog.com/docs/sql)
- [PostHog Status Page](https://status.posthog.com)
- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)
