---
name: posthog-cost-tuning
description: |
  Optimize PostHog costs: autocapture tuning, event sampling with before_send,
  bot filtering, session recording sampling, and billing monitoring.
  Trigger: "posthog cost", "posthog billing", "reduce posthog costs",
  "posthog pricing", "posthog expensive", "posthog budget", "posthog free tier".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, api, monitoring, cost-optimization]
---

# PostHog Cost Tuning

## Overview

PostHog Cloud pricing is event-based: 1M events/month free, then usage-based pricing beyond that. Session recordings, feature flag evaluations, and surveys each have their own free tiers. The biggest cost drivers are typically `$autocapture` events, `$pageview` on high-traffic pages, and bot traffic. This skill covers specific techniques to reduce event volume without losing analytical value.

## Prerequisites

- PostHog Cloud account with billing access
- Application instrumented with posthog-js
- Understanding of which events drive your analytics

## PostHog Cloud Free Tiers (2025)

| Product | Free Tier | Overage |
|---------|-----------|---------|
| Product analytics | 1M events/month | ~$0.00031/event |
| Session recordings | 5K sessions/month | ~$0.04/session |
| Feature flags | 1M API requests/month | ~$0.0001/request |
| Surveys | 250 responses/month | ~$0.10/response |

## Instructions

### Step 1: Audit Current Event Volume

```bash
set -euo pipefail
# See which events consume the most quota (last 30 days)
curl "https://app.posthog.com/api/projects/$POSTHOG_PROJECT_ID/query/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT event, count() AS total FROM events WHERE timestamp > now() - interval 30 day GROUP BY event ORDER BY total DESC LIMIT 20"
    }
  }' | jq '.results[] | {event: .[0], count: .[1]}'
```

### Step 2: Tune Autocapture

`$autocapture` is often the largest event volume. Restrict it to only useful interactions.

```typescript
import posthog from 'posthog-js';

posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://us.i.posthog.com',
  autocapture: {
    // Only capture click and submit events (skip change, scroll, etc.)
    dom_event_allowlist: ['click', 'submit'],
    // Only capture meaningful elements
    element_allowlist: ['a', 'button', 'form', 'input[type=submit]'],
    // Only capture elements with this CSS class
    css_selector_allowlist: ['.track-click', '[data-track]'],
    // Skip internal/admin pages entirely
    url_ignorelist: ['/admin', '/health', '/api/internal', '/_next'],
  },
});
```

### Step 3: Event Sampling with before_send

```typescript
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://us.i.posthog.com',
  before_send: (event) => {
    // 1. Always send business-critical events (no sampling)
    const critical = ['purchase', 'signup', 'subscription_started', 'subscription_canceled', 'error'];
    if (critical.includes(event.event)) return event;

    // 2. Drop bot traffic entirely
    const ua = navigator?.userAgent?.toLowerCase() || '';
    if (/bot|crawler|spider|scrapy|headless|phantom|puppeteer/i.test(ua)) {
      return null;
    }

    // 3. Sample pageviews to 25% on high-traffic pages
    if (event.event === '$pageview') {
      const highTraffic = ['/', '/pricing', '/blog'];
      const url = event.properties?.$current_url || '';
      if (highTraffic.some(p => url.endsWith(p))) {
        return Math.random() < 0.25 ? event : null;
      }
      return event; // Keep other pageviews at 100%
    }

    // 4. Sample autocapture to 20%
    if (event.event === '$autocapture') {
      return Math.random() < 0.2 ? event : null;
    }

    // 5. Sample pageleave to 50%
    if (event.event === '$pageleave') {
      return Math.random() < 0.5 ? event : null;
    }

    return event; // Keep all other events
  },
});
```

### Step 4: Optimize Session Recording Costs

```typescript
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://us.i.posthog.com',
  session_recording: {
    // Record only 10% of sessions (saves 90% on recording costs)
    sampleRate: 0.1,
    // Don't record sessions shorter than 5 seconds (bounces)
    minimumDurationMilliseconds: 5000,
    // Record 100% of sessions with errors (most valuable for debugging)
    // This is configured in PostHog dashboard under Session Replay settings
  },
});

// Alternatively: disable recording for non-paying users
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://us.i.posthog.com',
  disable_session_recording: true, // Start disabled
});

// Enable only for paying users
if (user.plan !== 'free') {
  posthog.startSessionRecording();
}
```

### Step 5: Monitor Usage and Set Alerts

```bash
set -euo pipefail
# Check current month's event usage
curl "https://app.posthog.com/api/projects/$POSTHOG_PROJECT_ID/query/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT count() AS total_events, uniq(distinct_id) AS unique_users, count() / dateDiff('"'"'day'"'"', toStartOfMonth(now()), now()) AS events_per_day FROM events WHERE timestamp > toStartOfMonth(now())"
    }
  }' | jq '.results[0] | {
    total_events: .[0],
    unique_users: .[1],
    avg_events_per_day: .[2],
    projected_monthly: (.[2] * 30),
    over_free_tier: (.[2] * 30 > 1000000)
  }'
```

```typescript
// Automated cost monitoring
async function checkPostHogBudget() {
  const result = await queryPostHog(`
    SELECT count() AS events_this_month
    FROM events
    WHERE timestamp > toStartOfMonth(now())
  `);

  const eventsThisMonth = result.results[0][0];
  const FREE_TIER = 1_000_000;
  const projectedMonthly = eventsThisMonth / (new Date().getDate() / 30);

  if (projectedMonthly > FREE_TIER * 0.8) {
    // Alert: approaching free tier limit
    await sendSlackAlert(`PostHog usage alert: ${Math.round(projectedMonthly / 1000)}K events projected this month (free tier: 1M)`);
  }
}
```

## Cost Reduction Estimates

| Technique | Typical Reduction | Impact on Analytics |
|-----------|------------------|-------------------|
| Restrict autocapture elements | 40-60% | Low (keep meaningful clicks) |
| Filter bot traffic | 10-30% | None (bots are noise) |
| Sample $pageview on high-traffic | 20-40% | Low (trends still accurate) |
| Session recording at 10% | 90% on recordings | Medium (fewer sessions to review) |
| Disable $pageleave | 15-20% | Low (rarely analyzed) |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Event volume spike | New feature without volume estimate | Forecast events before launch |
| Bill higher than expected | Bot traffic | Add bot filtering in `before_send` |
| Missing critical events | Sampling too aggressive | Exclude revenue events from sampling |
| Free tier exceeded mid-month | Autocapture too broad | Restrict to `.track-click` elements only |

## Output

- Autocapture restricted to meaningful interactions
- Event sampling reducing volume by 30-50%
- Bot traffic filtered
- Session recording sampled to 10%
- Budget monitoring with alerting

## Resources

- [PostHog Pricing](https://posthog.com/pricing)
- [PostHog Autocapture Config](https://posthog.com/docs/product-analytics/autocapture)
- [PostHog before_send](https://posthog.com/docs/libraries/js/config)
- [Session Recording Control](https://posthog.com/docs/session-replay/how-to-control-which-sessions-you-record)
