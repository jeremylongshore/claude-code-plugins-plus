---
name: instantly-webhooks-events
description: |
  Implement Instantly.ai webhook event handling with real API v2 event types.
  Use when setting up webhook endpoints, processing email events,
  or building CRM sync pipelines from Instantly notifications.
  Trigger with phrases like "instantly webhook", "instantly events",
  "instantly webhook handler", "handle instantly events", "instantly notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, webhooks, events, crm-sync]

---
# Instantly Webhooks & Events

## Overview
Handle Instantly API v2 webhooks for real-time email outreach event notifications. Instantly fires events when emails are sent, opened, clicked, replied to, or bounced, and when leads change interest status. Webhooks require Hypergrowth plan ($97/mo) or higher. Delivery retries: **3 times within 30 seconds** on failure.

## Prerequisites
- Instantly Hypergrowth plan or higher (required for webhooks)
- API key with `all:all` or appropriate webhook scopes
- Public HTTPS endpoint for receiving webhook payloads
- `INSTANTLY_API_KEY` environment variable set

## Webhook Event Types

| Event Type | Trigger | Key Payload Fields |
|------------|---------|-------------------|
| `email_sent` | Email delivered to recipient | `lead_email`, `campaign_id`, `step` |
| `email_opened` | Recipient opens email | `lead_email`, `campaign_id`, `open_count` |
| `email_link_clicked` | Recipient clicks a link | `lead_email`, `campaign_id`, `link_url` |
| `reply_received` | Recipient replies | `lead_email`, `campaign_id`, `reply_text` |
| `email_bounced` | Email bounces | `lead_email`, `bounce_type`, `reason` |
| `lead_unsubscribed` | Lead unsubscribes | `lead_email`, `campaign_id` |
| `campaign_completed` | All leads in campaign processed | `campaign_id`, `campaign_name` |
| `account_error` | Sending account error | `email`, `error_type` |
| `lead_interested` | Lead marked interested | `lead_email`, `campaign_id` |
| `lead_not_interested` | Lead marked not interested | `lead_email`, `campaign_id` |
| `lead_meeting_booked` | Meeting booked | `lead_email`, `campaign_id` |
| `lead_meeting_completed` | Meeting completed | `lead_email` |
| `lead_closed` | Lead closed/won | `lead_email` |
| `lead_out_of_office` | OOO reply detected | `lead_email` |
| `lead_wrong_person` | Wrong person response | `lead_email` |
| `all_events` | Subscribe to everything | Varies by event |

## Instructions

### Step 1: Create Webhook via API
```typescript
import { instantly } from "./src/instantly";

async function createWebhook() {
  // Create webhook for specific events
  const webhook = await instantly<{ id: string; name: string }>("/webhooks", {
    method: "POST",
    body: JSON.stringify({
      name: "CRM Sync — Replies & Meetings",
      target_hook_url: "https://api.yourapp.com/webhooks/instantly",
      event_type: "reply_received",
      headers: {
        "X-Webhook-Secret": process.env.INSTANTLY_WEBHOOK_SECRET,
      },
    }),
  });
  console.log(`Webhook created: ${webhook.id}`);

  // Create additional webhooks for other events
  for (const event of ["lead_interested", "lead_meeting_booked", "email_bounced"]) {
    await instantly("/webhooks", {
      method: "POST",
      body: JSON.stringify({
        name: `CRM Sync — ${event}`,
        target_hook_url: "https://api.yourapp.com/webhooks/instantly",
        event_type: event,
        headers: { "X-Webhook-Secret": process.env.INSTANTLY_WEBHOOK_SECRET },
      }),
    });
  }

  // Or subscribe to ALL events with one webhook
  await instantly("/webhooks", {
    method: "POST",
    body: JSON.stringify({
      name: "All Events Monitor",
      target_hook_url: "https://api.yourapp.com/webhooks/instantly/all",
      event_type: "all_events",
      headers: { "X-Webhook-Secret": process.env.INSTANTLY_WEBHOOK_SECRET },
    }),
  });
}
```

### Step 2: Build Event Handler
```typescript
import express from "express";

const app = express();
app.use(express.json());

app.post("/webhooks/instantly", async (req, res) => {
  // Validate secret
  if (req.headers["x-webhook-secret"] !== process.env.INSTANTLY_WEBHOOK_SECRET) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  // Respond 200 immediately — Instantly retries 3x in 30s on failure
  res.status(200).json({ received: true });

  const { event_type, data } = req.body;
  console.log(`Event: ${event_type}`, JSON.stringify(data).slice(0, 300));

  try {
    await routeEvent(event_type, data);
  } catch (err) {
    console.error(`Failed to process ${event_type}:`, err);
  }
});

async function routeEvent(eventType: string, data: any) {
  switch (eventType) {
    case "reply_received":
      await handleReply(data);
      break;
    case "email_bounced":
      await handleBounce(data);
      break;
    case "lead_interested":
    case "lead_meeting_booked":
    case "lead_closed":
      await handlePositiveOutcome(eventType, data);
      break;
    case "lead_unsubscribed":
      await handleUnsubscribe(data);
      break;
    case "campaign_completed":
      await handleCampaignComplete(data);
      break;
    case "account_error":
      await handleAccountError(data);
      break;
    default:
      console.log(`Unhandled event: ${eventType}`);
  }
}
```

### Step 3: Implement Event Handlers
```typescript
async function handleReply(data: {
  lead_email: string;
  campaign_id: string;
  reply_text: string;
}) {
  console.log(`Reply from ${data.lead_email} in campaign ${data.campaign_id}`);

  // Sync to CRM
  await crmClient.updateContact(data.lead_email, {
    status: "replied",
    lastReply: data.reply_text,
    lastActivity: new Date(),
  });

  // Notify sales team
  await slackNotify("#sales-replies", {
    text: `Reply from ${data.lead_email}:\n${data.reply_text.slice(0, 500)}`,
  });
}

async function handleBounce(data: {
  lead_email: string;
  bounce_type: string;
  reason: string;
}) {
  console.log(`Bounce: ${data.lead_email} (${data.bounce_type})`);

  if (data.bounce_type === "hard") {
    // Add to global block list
    await instantly("/block-lists-entries", {
      method: "POST",
      body: JSON.stringify({ bl_value: data.lead_email }),
    });
    console.log(`Added ${data.lead_email} to block list`);
  }
}

async function handlePositiveOutcome(
  eventType: string,
  data: { lead_email: string; campaign_id: string }
) {
  const statusMap: Record<string, string> = {
    lead_interested: "interested",
    lead_meeting_booked: "meeting_scheduled",
    lead_closed: "closed_won",
  };

  await crmClient.updateContact(data.lead_email, {
    status: statusMap[eventType] || eventType,
    lastActivity: new Date(),
  });

  if (eventType === "lead_meeting_booked") {
    await slackNotify("#sales-wins", {
      text: `Meeting booked with ${data.lead_email}!`,
    });
  }
}

async function handleUnsubscribe(data: { lead_email: string }) {
  // Add to block list to prevent future outreach across all campaigns
  await instantly("/block-lists-entries", {
    method: "POST",
    body: JSON.stringify({ bl_value: data.lead_email }),
  });
  console.log(`Unsubscribed + blocked: ${data.lead_email}`);
}

async function handleCampaignComplete(data: { campaign_id: string }) {
  // Pull final analytics
  const analytics = await instantly(`/campaigns/analytics?id=${data.campaign_id}`);
  console.log(`Campaign complete:`, analytics);
}

async function handleAccountError(data: { email: string; error_type: string }) {
  console.error(`Account error: ${data.email} — ${data.error_type}`);
  await slackNotify("#ops-alerts", {
    text: `Instantly account error: ${data.email}\nType: ${data.error_type}`,
  });
}
```

### Step 4: Manage Webhooks
```typescript
// List all webhooks
async function listWebhooks() {
  const webhooks = await instantly<Array<{
    id: string; name: string; event_type: string; target_hook_url: string;
  }>>("/webhooks?limit=50");

  for (const w of webhooks) {
    console.log(`${w.id}: ${w.name} [${w.event_type}] -> ${w.target_hook_url}`);
  }
}

// Test a webhook
async function testWebhook(webhookId: string) {
  await instantly(`/webhooks/${webhookId}/test`, { method: "POST" });
}

// Resume a paused webhook
async function resumeWebhook(webhookId: string) {
  await instantly(`/webhooks/${webhookId}/resume`, { method: "POST" });
}

// Check delivery status
async function checkDeliveryHealth() {
  const summary = await instantly("/webhook-events/summary");
  console.log("Webhook delivery summary:", summary);

  const byDate = await instantly("/webhook-events/summary-by-date");
  console.log("By date:", byDate);
}

// Delete a webhook
async function deleteWebhook(webhookId: string) {
  await instantly(`/webhooks/${webhookId}`, { method: "DELETE" });
}
```

## Key API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks` | Create webhook subscription |
| `GET` | `/webhooks` | List webhooks |
| `PATCH` | `/webhooks/{id}` | Update webhook |
| `DELETE` | `/webhooks/{id}` | Delete webhook |
| `POST` | `/webhooks/{id}/test` | Send test event |
| `POST` | `/webhooks/{id}/resume` | Resume paused webhook |
| `GET` | `/webhook-events` | List webhook events |
| `GET` | `/webhook-events/summary` | Delivery summary |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No events delivered | Webhook not registered or paused | Check `GET /webhooks`, resume if paused |
| Duplicate events | Retry delivery | Deduplicate by event ID + timestamp |
| Webhook paused automatically | Too many delivery failures | Fix endpoint, then `POST /webhooks/{id}/resume` |
| 30s timeout | Handler takes too long | Return 200 immediately, process async |
| Missing event_type | Using custom label events | Check `custom_interest_value` field |

## Resources
- [Instantly Webhook API](https://developer.instantly.ai/api/v2/webhook)
- [Instantly Webhook Events](https://developer.instantly.ai/api/v2/webhook)
- [Instantly Blog: Webhooks Guide](https://instantly.ai/blog/api-webhooks-custom-integrations-for-outreach/)

## Next Steps
For performance optimization, see `instantly-performance-tuning`.
