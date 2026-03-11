---
name: instantly-webhooks-events
description: |
  Implement Instantly webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Instantly event notifications securely.
  Trigger with phrases like "instantly webhook", "instantly events",
  "instantly webhook signature", "handle instantly events", "instantly notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Instantly Webhooks & Events

## Overview
Handle Instantly webhooks for real-time email outreach event notifications. Instantly fires webhooks when emails are sent, opened, replied to, bounced, or when leads change status.

## Prerequisites
- Instantly account with API access enabled
- Instantly API key stored in `INSTANTLY_API_KEY` environment variable
- HTTPS endpoint for receiving webhook deliveries
- Active email campaigns configured in Instantly

## Webhook Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `email.sent` | Email delivered | Lead email, campaign ID, step |
| `email.opened` | Recipient opens email | Lead email, open count, timestamp |
| `email.replied` | Recipient replies | Lead email, reply text, sentiment |
| `email.bounced` | Email bounced | Lead email, bounce type, reason |
| `email.unsubscribed` | Recipient unsubscribes | Lead email, campaign |
| `lead.interested` | Lead marked interested | Lead data, campaign context |
| `lead.meeting_booked` | Meeting scheduled | Lead data, calendar details |

## Instructions

### Step 1: Configure Webhook Endpoint
```typescript
import express from "express";

const app = express();
app.use(express.json());

app.post("/webhooks/instantly", async (req, res) => {
  const apiKey = req.headers["x-api-key"] as string;

  if (apiKey !== process.env.INSTANTLY_WEBHOOK_SECRET) {
    return res.status(401).json({ error: "Unauthorized" });  # HTTP 401 Unauthorized
  }

  const { event_type, data, timestamp } = req.body;
  res.status(200).json({ received: true });  # HTTP 200 OK

  await handleInstantlyEvent(event_type, data);
});
```

### Step 2: Route and Process Events
```typescript
async function handleInstantlyEvent(eventType: string, data: any) {
  switch (eventType) {
    case "email.replied":
      await handleReply(data);
      break;
    case "email.opened":
      await handleOpen(data);
      break;
    case "email.bounced":
      await handleBounce(data);
      break;
    case "lead.interested":
      await handleInterestedLead(data);
      break;
    case "lead.meeting_booked":
      await handleMeetingBooked(data);
      break;
  }
}

async function handleReply(data: any) {
  const { lead_email, campaign_id, reply_text, reply_sentiment } = data;

  console.log(`Reply from ${lead_email} (sentiment: ${reply_sentiment})`);

  // Sync to CRM
  await crmClient.updateLead(lead_email, {
    status: reply_sentiment === "positive" ? "interested" : "replied",
    lastActivity: new Date(),
    lastReply: reply_text,
  });

  // Notify sales team for positive replies
  if (reply_sentiment === "positive") {
    await slackNotify("#sales-leads", {
      text: `Positive reply from ${lead_email}!\nCampaign: ${campaign_id}`,
    });
  }
}

async function handleBounce(data: any) {
  const { lead_email, bounce_type, reason } = data;

  // Remove hard bounces from all campaigns
  if (bounce_type === "hard") {
    await fetch("https://api.instantly.ai/api/v1/lead/delete", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.INSTANTLY_API_KEY}`,
      },
      body: JSON.stringify({
        email: lead_email,
        delete_from_all_campaigns: true,
      }),
    });
  }
}
```

### Step 3: Register Webhook via API
```bash
set -euo pipefail
curl -X POST https://api.instantly.ai/api/v1/webhooks \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://api.yourapp.com/webhooks/instantly",
    "event_types": ["email.replied", "email.bounced", "lead.interested"],
    "secret": "your-webhook-secret"
  }'
```

### Step 4: Track Campaign Analytics
```typescript
async function handleOpen(data: any) {
  const { lead_email, campaign_id, open_count } = data;

  await analyticsDb.trackEvent({
    event: "email_opened",
    campaignId: campaign_id,
    leadEmail: lead_email,
    openCount: open_count,
    timestamp: new Date(),
  });
}

async function handleMeetingBooked(data: any) {
  const { lead_email, meeting_time, calendar_link } = data;

  await crmClient.createDeal({
    contactEmail: lead_email,
    stage: "meeting_scheduled",
    meetingTime: meeting_time,
  });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing events | Webhook not registered | Verify webhook URL in Instantly dashboard |
| Duplicate replies | Retry delivery | Deduplicate by lead_email + timestamp |
| Invalid API key | Key expired | Regenerate in Instantly settings |
| High bounce rate | Bad lead list | Clean list with email verification service |

## Examples

### Campaign Performance Dashboard
```typescript
async function getCampaignStats(campaignId: string) {
  const response = await fetch(
    `https://api.instantly.ai/api/v1/analytics/campaign?campaign_id=${campaignId}`,
    { headers: { "Authorization": `Bearer ${process.env.INSTANTLY_API_KEY}` } }
  );
  return response.json();
}
```

## Resources
- [Instantly API Documentation](https://developer.instantly.ai)
- [Instantly Webhooks Guide](https://developer.instantly.ai/webhooks)

## Next Steps
For deployment setup, see `instantly-deploy-integration`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale