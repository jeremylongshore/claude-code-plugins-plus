---
name: klaviyo-core-workflow-b
description: |
  Execute Klaviyo secondary workflow: event tracking, segments, and campaigns.
  Use when tracking customer events, creating segments, building campaigns,
  or triggering flows via the Klaviyo API.
  Trigger with phrases like "klaviyo events", "klaviyo segments",
  "klaviyo campaigns", "track klaviyo event", "klaviyo flow trigger".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Core Workflow B -- Events, Segments & Campaigns

## Overview

Secondary workflow: track customer events, query segments, create/send campaigns, and trigger metric-based flows via the `klaviyo-api` SDK.

## Prerequisites

- Completed `klaviyo-core-workflow-a` (profiles/lists set up)
- API key scopes: `events:write`, `segments:read`, `campaigns:read`, `campaigns:write`, `flows:read`

## Instructions

### Step 1: Track Server-Side Events

```typescript
import {
  ApiKeySession,
  EventsApi,
  EventEnum,
  ProfileEnum,
  MetricsApi,
} from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const eventsApi = new EventsApi(session);

// Track a purchase event (creates the metric if it doesn't exist)
await eventsApi.createEvent({
  data: {
    type: EventEnum.Event,
    attributes: {
      metric: {
        data: {
          type: 'metric',
          attributes: { name: 'Placed Order' },
        },
      },
      profile: {
        data: {
          type: ProfileEnum.Profile,
          attributes: { email: 'customer@example.com' },
        },
      },
      properties: {
        orderId: 'ORD-12345',
        items: [
          { productId: 'SKU-001', name: 'Widget', quantity: 2, price: 29.99 },
          { productId: 'SKU-002', name: 'Gadget', quantity: 1, price: 49.99 },
        ],
        itemCount: 3,
        discount: 10.00,
      },
      // Monetary value for revenue attribution
      value: 99.97,
      time: new Date().toISOString(),
      uniqueId: 'ORD-12345',  // Deduplication key
    },
  },
});

// Track a custom event (triggers flows listening for this metric)
await eventsApi.createEvent({
  data: {
    type: EventEnum.Event,
    attributes: {
      metric: {
        data: { type: 'metric', attributes: { name: 'Started Checkout' } },
      },
      profile: {
        data: { type: ProfileEnum.Profile, attributes: { email: 'customer@example.com' } },
      },
      properties: {
        cartValue: 149.97,
        cartUrl: 'https://shop.example.com/cart/abc123',
        items: ['Widget x2', 'Gadget x1'],
      },
      value: 149.97,
      time: new Date().toISOString(),
    },
  },
});
```

### Step 2: Query Events and Metrics

```typescript
const metricsApi = new MetricsApi(session);

// List all metrics (event types) in your account
const metrics = await metricsApi.getMetrics();
for (const m of metrics.body.data) {
  console.log(`${m.attributes.name} (${m.id})`);
}

// Get recent events sorted by newest first
const events = await eventsApi.getEvents({
  sort: '-datetime',
  filter: 'equals(metric_id,"METRIC_ID_HERE")',
});

for (const event of events.body.data) {
  console.log(`${event.attributes.datetime}: ${event.attributes.eventProperties?.orderId}`);
}
```

### Step 3: Work with Segments

```typescript
import { SegmentsApi } from 'klaviyo-api';

const segmentsApi = new SegmentsApi(session);

// List all segments
const segments = await segmentsApi.getSegments();
for (const seg of segments.body.data) {
  console.log(`${seg.attributes.name} (${seg.id}) - active: ${seg.attributes.isActive}`);
}

// Get profiles in a segment
const segmentProfiles = await segmentsApi.getSegmentProfiles({
  id: 'SEGMENT_ID',
});
for (const profile of segmentProfiles.body.data) {
  console.log(profile.attributes.email);
}

// Check segment size (useful before campaign sends)
const segmentWithCount = await segmentsApi.getSegment({
  id: 'SEGMENT_ID',
  additionalFieldsSegment: ['profile_count'],
});
console.log(`Segment size: ${segmentWithCount.body.data.attributes.profileCount}`);
```

### Step 4: Create an Email Campaign

```typescript
import { CampaignsApi, CampaignEnum, TemplatesApi } from 'klaviyo-api';

const campaignsApi = new CampaignsApi(session);
const templatesApi = new TemplatesApi(session);

// 1. Create an email template
const template = await templatesApi.createTemplate({
  data: {
    type: 'template',
    attributes: {
      name: 'Weekly Sale Announcement',
      editorType: 'CODE',
      html: `
        <html>
          <body>
            <h1>Hey {{ first_name|default:"there" }}!</h1>
            <p>Check out our weekly deals.</p>
            <a href="{{ url }}">Shop Now</a>
            {% unsubscribe %}Unsubscribe{% endunsubscribe %}
          </body>
        </html>
      `,
    },
  },
});

// 2. Create a campaign targeting a list or segment
const campaign = await campaignsApi.createCampaign({
  data: {
    type: CampaignEnum.Campaign,
    attributes: {
      name: 'Weekly Sale - March 2025',
      channel: 'email',
      audiences: {
        included: [{ type: 'segment', id: 'SEGMENT_ID' }],
        excluded: [{ type: 'list', id: 'SUPPRESSION_LIST_ID' }],
      },
      sendOptions: {
        useSmartSending: true,  // Skip recently emailed contacts
      },
    },
  },
});
const campaignId = campaign.body.data.id;

// 3. Assign template to campaign message
const messages = await campaignsApi.getCampaignCampaignMessages({ id: campaignId });
const messageId = messages.body.data[0].id;

await campaignsApi.assignTemplateToCampaignMessage({
  id: messageId,
  body: {
    data: {
      type: 'template',
      id: template.body.data.id,
    },
  },
});

// 4. Send the campaign (or schedule)
await campaignsApi.createCampaignSendJob({
  data: {
    type: 'campaign-send-job',
    id: campaignId,
  },
});
console.log('Campaign queued for sending');
```

### Step 5: Query Flows (Read-Only)

```typescript
import { FlowsApi } from 'klaviyo-api';

const flowsApi = new FlowsApi(session);

// List all flows
const flows = await flowsApi.getFlows();
for (const flow of flows.body.data) {
  console.log(`${flow.attributes.name} - status: ${flow.attributes.status}`);
}

// Get flow actions (the steps in a flow)
const flowActions = await flowsApi.getFlowFlowActions({ id: 'FLOW_ID' });
for (const action of flowActions.body.data) {
  console.log(`  Action: ${action.attributes.actionType} - ${action.attributes.status}`);
}
```

## Common Event Names for Flow Triggers

| Event Name | Typical Trigger | Flow Type |
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

## Resources

- [Events API](https://developers.klaviyo.com/en/reference/events_api_overview)
- [Segments API](https://developers.klaviyo.com/en/reference/segments_api_overview)
- [Campaigns API](https://developers.klaviyo.com/en/reference/campaigns_api_overview)
- [Flows API](https://developers.klaviyo.com/en/reference/flows_api_overview)
- [Metrics API](https://developers.klaviyo.com/en/reference/metrics_api_overview)

## Next Steps

For common errors, see `klaviyo-common-errors`.
