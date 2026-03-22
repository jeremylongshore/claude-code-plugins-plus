---
name: hootsuite-campaign-delivery
description: |
  Execute Hootsuite primary workflow: Campaign & Message Delivery.
  Use when sending targeted email campaigns to user segments,
  triggering transactional messages on user actions, or scheduling multi-channel drip sequences.
  Trigger with phrases like "hootsuite send campaign",
  "create and send campaign with hootsuite".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hootsuite]
---

# Hootsuite Campaign & Message Delivery

## Overview
Create and send targeted messaging campaigns (email, SMS, push, in-app).
This is the primary workflow — reach the right audience with the right message.


## Prerequisites
- Completed `hootsuite-install-auth` setup

- Understanding of Hootsuite core concepts

- Valid API credentials configured

## Instructions

### Step 1: Define Audience Segment
```typescript
const segment = await client.segments.create({
  name: 'Active Users — Last 30 Days',
  filters: [
    { field: 'last_active', operator: 'after', value: thirtyDaysAgo },
    { field: 'plan', operator: 'eq', value: 'pro' },
  ],
});
console.log(`Segment created: ${segment.id} (${segment.count} users)`);

```

### Step 2: Create Campaign
```typescript
const campaign = await client.campaigns.create({
  name: 'March Product Update',
  segmentId: segment.id,
  channel: 'email',
  subject: 'New features just dropped',
  body: emailTemplate,
  trackOpens: true,
  trackClicks: true,
});

```

### Step 3: Send and Monitor
```typescript
const result = await client.campaigns.send(campaign.id);
console.log(`Sent to ${result.recipientCount} recipients`);

// Check delivery stats after a few minutes
const stats = await client.campaigns.stats(campaign.id);
console.log(`Delivered: ${stats.delivered}, Opens: ${stats.opens}, Clicks: ${stats.clicks}`);

```

## Output
- Completed Campaign & Message Delivery execution

- Expected results from Hootsuite API

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid Recipient | Email/phone number failed validation or is on suppression list | Validate recipient data before sending. Check suppression list status. |
| Template Rendering Failed | Template variable referenced but not provided in send payload | Ensure all template variables have values. Use default values in templates. |

## Examples

### Complete Workflow
```typescript
const client = new MessagingClient({ apiKey: process.env.API_KEY });

async function sendCampaign(segmentId: string, template: string) {
  const campaign = await client.campaigns.create({
    segmentId,
    channel: 'email',
    templateId: template,
  });
  return client.campaigns.send(campaign.id);
}

```

### Common Variations
- **Transactional**: Single messages triggered by user events (welcome, receipt, password reset)
- **Drip sequence**: Multi-step flows with delays and conditions between messages
- **Multi-channel**: Send via email, SMS, push, or in-app based on user preference


## Resources
- [Hootsuite Documentation](https://docs.hootsuite.com)
- [Hootsuite API Reference](https://docs.hootsuite.com/api)

## Next Steps
For secondary workflow, see `hootsuite-event-tracking`.