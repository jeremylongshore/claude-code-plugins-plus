# Klaviyo Core Workflow B — Worked Examples

End-to-end scenarios that chain the steps from
[implementation.md](implementation.md). Each assumes a `session` is already open:

```typescript
import { ApiKeySession } from 'klaviyo-api';
const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
```

## Example 1: Fire an abandoned-cart signal

Track a `Started Checkout` event so a metric-triggered flow can pick it up. See Step 1
in [implementation.md](implementation.md) for the full event shape.

```typescript
import { EventsApi, EventEnum, ProfileEnum } from 'klaviyo-api';
const eventsApi = new EventsApi(session);

await eventsApi.createEvent({
  data: {
    type: EventEnum.Event,
    attributes: {
      metric: { data: { type: 'metric', attributes: { name: 'Started Checkout' } } },
      profile: { data: { type: ProfileEnum.Profile, attributes: { email: 'customer@example.com' } } },
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

## Example 2: Size a segment before sending

Guard a campaign send by checking the audience size first (Step 3):

```typescript
import { SegmentsApi } from 'klaviyo-api';
const segmentsApi = new SegmentsApi(session);

const seg = await segmentsApi.getSegment({
  id: 'SEGMENT_ID',
  additionalFieldsSegment: ['profile_count'],
});
const size = seg.body.data.attributes.profileCount;
if (size === 0) {
  throw new Error('Segment is empty — nothing to send.');
}
console.log(`Sending to ${size} profiles`);
```

## Example 3: Create and send a campaign to a segment

The full four-part campaign creation (template → campaign → assign template → send job)
lives in Step 4 of [implementation.md](implementation.md). The critical ordering:

1. Create the template.
2. Create the campaign with `audiences.included` pointing at the segment and
   `audiences.excluded` pointing at a suppression list.
3. Fetch the campaign's message (`getCampaignCampaignMessages`) and assign the template to it.
4. Only then create the `campaign-send-job`. Sending before a template is assigned returns a 400.

```typescript
import { CampaignsApi } from 'klaviyo-api';
const campaignsApi = new CampaignsApi(session);

// After template + campaign + template-assignment (see Step 4):
await campaignsApi.createCampaignSendJob({
  data: { type: 'campaign-send-job', id: campaignId },
});
console.log('Campaign queued for sending');
```
