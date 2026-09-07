# Klaviyo Core Workflow B — Full Implementation

Complete, copy-ready code for every step of the events / segments / campaigns / flows
workflow. Each step is independent — start a `session` once, then use the API classes you need.

```typescript
import {
  ApiKeySession,
  EventsApi,
  EventEnum,
  ProfileEnum,
  MetricsApi,
} from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
```

## Step 1: Track Server-Side Events

```typescript
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

## Step 2: Query Events and Metrics

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

## Step 3: Work with Segments

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

## Step 4: Create an Email Campaign

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
      name: 'Weekly Sale - Spring Promo',
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

## Step 5: Query Flows (Read-Only)

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
