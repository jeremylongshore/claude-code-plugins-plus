---
name: posthog-cost-tuning
description: |
  Optimize PostHog costs through tier selection, sampling, and usage monitoring.
  Use when analyzing PostHog billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "posthog cost", "posthog billing",
  "reduce posthog costs", "posthog pricing", "posthog expensive", "posthog budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# PostHog Cost Tuning

## Overview
Reduce PostHog event-based pricing costs by controlling event volume, optimizing autocapture settings, and leveraging the generous free tier. PostHog charges per event with a free tier of 1M events/month, then ~$0.00031 per event beyond that. The biggest cost levers are: disabling autocapture on high-frequency elements (a single button clicked 100K times/month = $31), filtering out bot traffic, and sampling non-critical events. Session recordings and feature flags have separate pricing tiers.

## Prerequisites
- PostHog Cloud account with billing dashboard access
- Application instrumented with PostHog SDK
- Understanding of which events drive business value

## Instructions

### Step 1: Audit Event Volume by Type
```bash
# Check which events consume the most quota
curl "https://app.posthog.com/api/projects/PROJECT_ID/insights/trend/?events=[{\"id\":\"$pageview\"},{\"id\":\"$autocapture\"},{\"id\":\"$screen\"}]&date_from=-30d&interval=week" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" | \
  jq '.result[] | {event: .label, total_30d: (.data | add)}'
```

### Step 2: Disable Unnecessary Autocapture
```typescript
// posthog-init.ts - Configure autocapture to skip noisy elements
posthog.init('phc_YOUR_KEY', {
  autocapture: {
    dom_event_allowlist: ['click', 'submit'], // Skip scroll, change, etc.
    element_allowlist: ['a', 'button', 'form', 'input[type=submit]'],
    css_selector_allowlist: ['.track-click'], // Only track explicitly marked elements
    url_ignorelist: ['/health', '/api/internal'], // Skip internal endpoints
  },
  // Disable session recording for anonymous users to save on recording quota
  session_recording: {
    maskAllInputs: true,
  },
});
```

### Step 3: Sample High-Volume Events
```typescript
// Reduce non-critical event volume by sampling
posthog.init('phc_YOUR_KEY', {
  // Only send 10% of pageview events (still statistically significant)
  before_send: (event) => {
    if (event.event === '$pageview') {
      return Math.random() < 0.1 ? event : null; // 90% reduction
    }
    // Always send business-critical events
    if (['purchase', 'signup', 'upgrade'].includes(event.event)) {
      return event;
    }
    // Sample other events at 50%
    return Math.random() < 0.5 ? event : null;
  },
});
```

### Step 4: Filter Bot Traffic
```typescript
// Bots generate significant event volume without business value
posthog.init('phc_YOUR_KEY', {
  before_send: (event) => {
    const ua = navigator.userAgent.toLowerCase();
    const isBot = /bot|crawler|spider|scrapy|headless|phantom/i.test(ua);
    return isBot ? null : event;
  },
});
```

### Step 5: Monitor Monthly Costs
```bash
# Check current event usage vs billing tier
curl "https://app.posthog.com/api/organizations/ORG_ID/billing/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" | \
  jq '{
    events_used: .events_current_usage,
    events_limit: .events_plan_limit,
    usage_pct: (.events_current_usage / .events_plan_limit * 100),
    estimated_cost: (if .events_current_usage > 1000000 then ((.events_current_usage - 1000000) * 0.00031) else 0 end)
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Event volume spike | Autocapture on high-frequency element | Add element to `css_selector_denylist` |
| Bill higher than expected | Bot traffic generating events | Add bot filtering in `before_send` |
| Missing critical events | Sampling too aggressive | Exclude business events from sampling |
| Free tier exceeded early | New feature launched without volume estimate | Forecast events before launch |

## Examples
```typescript
// Cost projection calculator
const monthlyEvents = 5_000_000;
const freeEvents = 1_000_000;
const costPerEvent = 0.00031;
const monthlyCost = (monthlyEvents - freeEvents) * costPerEvent;
console.log(`Projected cost: $${monthlyCost.toFixed(2)}/month`);
// $1,240/month -> with 50% sampling on non-critical: $620/month
```
