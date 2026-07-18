---
name: klaviyo-core-workflow-b
description: |
  Execute the Klaviyo secondary workflow: event tracking, segments, and campaigns.
  Use when you need to track customer events, query or size segments, build and send
  email campaigns, or inspect metric-triggered flows through the Klaviyo API.
  Trigger with phrases like "klaviyo events", "klaviyo segments", "klaviyo campaigns",
  "track klaviyo event", "klaviyo flow trigger".
allowed-tools: Read, Write, Bash(npm:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Core Workflow B -- Events, Segments & Campaigns

## Overview

Secondary workflow: track customer events, query segments, create/send campaigns, and
trigger metric-based flows via the `klaviyo-api` SDK. This page summarizes the five steps
and their skeletons; the full copy-ready code lives in
[references/implementation.md](references/implementation.md) and worked scenarios in
[references/examples.md](references/examples.md).

## Prerequisites

- Completed `klaviyo-core-workflow-a` (profiles/lists set up)
- API key scopes: `events:write`, `segments:read`, `campaigns:read`, `campaigns:write`, `flows:read`
- `klaviyo-api` installed and `KLAVIYO_PRIVATE_KEY` set in the environment

## Instructions

Open one session, then use the API class each step needs. Full parameter shapes for every
step are in [references/implementation.md](references/implementation.md).

```typescript
import { ApiKeySession, EventsApi } from 'klaviyo-api';
const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
```

1. **Step 1 — Track server-side events.** `new EventsApi(session).createEvent(...)`. Include
   `metric.data.attributes.name` (auto-creates the metric), a `profile`, a `value` for revenue
   attribution, and a `uniqueId` for deduplication. Custom metrics trigger listening flows.
2. **Step 2 — Query events and metrics.** `MetricsApi.getMetrics()` lists event types;
   `EventsApi.getEvents({ sort: '-datetime', filter: 'equals(metric_id,"...")' })` reads recent events.
3. **Step 3 — Work with segments.** `SegmentsApi.getSegments()` lists them,
   `getSegmentProfiles()` reads members, and `getSegment({ additionalFieldsSegment: ['profile_count'] })`
   returns the size — check it before a send.
4. **Step 4 — Create an email campaign.** Four ordered calls: create a template, create the
   campaign (with `audiences.included`/`excluded`), assign the template to the campaign message,
   then create the `campaign-send-job`. Sending before the template is assigned returns a 400.
5. **Step 5 — Query flows (read-only).** `FlowsApi.getFlows()` lists flows;
   `getFlowFlowActions({ id })` returns each flow's steps and their status.

## Output

- **Event tracking** returns an HTTP 202 Accepted acknowledgement (Klaviyo queues events
  asynchronously); the event appears in the profile's
  activity feed and fires any flow listening on that metric.
- **Metric/segment/flow queries** return a `body.data` array of records with `id` and
  `attributes` (name, status, `profileCount`, etc.).
- **Campaign creation** yields a campaign `id`; the send job queues the campaign, and Klaviyo
  reports delivery back in the app's campaign analytics.

## Common Event Names for Flow Triggers

| Event name | Typical trigger | Flow type |
|-----------|----------------|-----------|
| `Placed Order` | Purchase completed | Post-purchase / cross-sell |
| `Started Checkout` | Cart created | Abandoned cart |
| `Viewed Product` | Product page visit | Browse abandonment |
| `Ordered Product` | Per-item tracking | Product review request |
| `Fulfilled Order` | Shipment sent | Shipping confirmation |
| `Cancelled Order` | Order cancelled | Win-back |
| `Subscribed to List` | Email/SMS signup | Welcome series |
| `Custom Event` | Any API event | Custom automation |

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| Invalid metric name | 400 | Empty or null metric | Always include `metric.data.attributes.name` |
| Segment not found | 404 | Wrong segment ID | List segments with `getSegments()` |
| Campaign send failed | 400 | Missing template/audience | Assign template and set audience first |
| Duplicate event | N/A | Same `uniqueId` | Deduplication built-in; safe to retry |

## Examples

Concrete, runnable scenarios are collected in
[references/examples.md](references/examples.md):

- **Fire an abandoned-cart signal** — track a `Started Checkout` event for a flow to pick up.
- **Size a segment before sending** — read `profileCount` and refuse to send to an empty audience.
- **Create and send a campaign to a segment** — the ordered template → campaign → assign → send-job chain.

A minimal event track:

```typescript
import { EventsApi, EventEnum, ProfileEnum } from 'klaviyo-api';
const eventsApi = new EventsApi(session);

await eventsApi.createEvent({
  data: {
    type: EventEnum.Event,
    attributes: {
      metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
      profile: { data: { type: ProfileEnum.Profile, attributes: { email: 'customer@example.com' } } },
      value: 99.97,
      time: new Date().toISOString(),
      uniqueId: 'ORD-12345',
    },
  },
});
```

## Resources

- [Full implementation walkthrough](references/implementation.md) — copy-ready code for all five steps
- [Worked examples](references/examples.md) — end-to-end scenarios
- [Events API](https://developers.klaviyo.com/en/reference/events_api_overview)
- [Segments API](https://developers.klaviyo.com/en/reference/segments_api_overview)
- [Campaigns API](https://developers.klaviyo.com/en/reference/campaigns_api_overview)
- [Flows API](https://developers.klaviyo.com/en/reference/flows_api_overview)
- [Metrics API](https://developers.klaviyo.com/en/reference/metrics_api_overview)
- For common errors, see the `klaviyo-common-errors` skill.
