---
name: posthog-observability
description: |
  Set up comprehensive observability for PostHog integrations with metrics, traces, and alerts.
  Use when implementing monitoring for PostHog operations, setting up dashboards,
  or configuring alerting for PostHog integration health.
  Trigger with phrases like "posthog monitoring", "posthog metrics",
  "posthog observability", "monitor posthog", "posthog alerts", "posthog tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# PostHog Observability

## Overview
Monitor PostHog event ingestion health, query performance, and feature flag evaluation reliability. Key signals include event ingestion rate and latency (time from `posthog.capture()` to event appearing in queries), feature flag evaluation latency (critical for server-side flags in hot paths), event volume by type (to detect instrumentation regressions), and API rate limit consumption. PostHog's event-based pricing means tracking event volume is directly tied to billing.

## Prerequisites
- PostHog Cloud or self-hosted instance
- Personal API key with read access
- Application instrumented with PostHog SDK

## Instructions

### Step 1: Monitor Event Ingestion Health
```bash
# Check recent event ingestion via the API
curl "https://app.posthog.com/api/projects/PROJECT_ID/insights/trend/?events=[{\"id\":\"$pageview\"}]&date_from=-24h" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" | \
  jq '.result[0].data | {total: add, last_hour: .[-1], trend: (if .[-1] > .[-2] then "up" else "down" end)}'
```

### Step 2: Track Feature Flag Evaluation Performance
```typescript
// posthog-flag-monitor.ts
import PostHog from 'posthog-node';
const posthog = new PostHog(process.env.POSTHOG_API_KEY!);

async function monitorFlagLatency(flagKey: string, distinctId: string) {
  const start = performance.now();
  const value = await posthog.getFeatureFlag(flagKey, distinctId);
  const duration = performance.now() - start;

  emitHistogram('posthog_flag_eval_ms', duration, { flag: flagKey });
  emitCounter('posthog_flag_evals_total', 1, { flag: flagKey, result: String(value) });

  if (duration > 200) {
    console.warn(`Slow flag evaluation: ${flagKey} took ${duration.toFixed(0)}ms`);
  }
}
```

### Step 3: Monitor Event Volume for Billing
```typescript
// Track event counts to predict billing
async function checkEventVolume() {
  const res = await fetch(`https://app.posthog.com/api/projects/${PROJECT_ID}/insights/trend/?events=[{"id":"$pageview"},{"id":"$autocapture"}]&date_from=-7d`, {
    headers: { Authorization: `Bearer ${POSTHOG_KEY}` },
  });
  const data = await res.json();
  const weeklyTotal = data.result.reduce((sum: number, series: any) => sum + series.data.reduce((a: number, b: number) => a + b, 0), 0);
  emitGauge('posthog_weekly_events', weeklyTotal);
  emitGauge('posthog_projected_monthly_events', weeklyTotal * 4.3);
}
```

### Step 4: Alert on Anomalies
```yaml
groups:
  - name: posthog
    rules:
      - alert: PostHogIngestionDrop
        expr: rate(posthog_events_ingested[1h]) < rate(posthog_events_ingested[1h] offset 1d) * 0.5
        annotations: { summary: "PostHog event ingestion dropped >50% vs yesterday" }
      - alert: PostHogFlagSlow
        expr: histogram_quantile(0.95, rate(posthog_flag_eval_ms_bucket[5m])) > 500
        annotations: { summary: "PostHog feature flag P95 evaluation exceeds 500ms" }
      - alert: PostHogEventBudgetHigh
        expr: posthog_projected_monthly_events > 10000000
        annotations: { summary: "Projected PostHog events exceed 10M/month (check billing tier)" }
      - alert: PostHogApiErrors
        expr: rate(posthog_api_errors_total[5m]) > 0.1
        annotations: { summary: "PostHog API errors elevated" }
```

### Step 5: Dashboard Panels
Track: event ingestion rate over time, event volume by type ($pageview, $autocapture, custom), feature flag evaluation latency, projected monthly events vs billing tier, API response times, and session recording count. An ingestion drop often means broken SDK instrumentation -- catch it early.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Events not appearing | SDK not initialized or blocked | Check browser console for PostHog errors, verify API key |
| Flag always returns default | Flag not enabled for environment | Check flag filters and rollout percentage |
| Event volume spike | Autocapture on high-frequency element | Exclude element from autocapture config |
| API `429` rate limited | Too many insight queries | Cache insight results, reduce poll frequency |

## Examples
```bash
# Quick check: event ingestion working?
curl -s "https://app.posthog.com/api/projects/PROJECT_ID/events/?limit=5" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" | \
  jq '.results[] | {event: .event, timestamp, distinct_id}'
```
