---
name: customerio-webhooks-events
description: |
  Implement Customer.io webhook and reporting event handling.
  Use when processing email delivery events, click/open tracking,
  bounce handling, or streaming to a data warehouse.
  Trigger: "customer.io webhook", "customer.io events",
  "customer.io delivery status", "customer.io bounces", "customer.io open tracking".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, webhooks, events, delivery]

---
# Customer.io Webhooks & Events

## Overview

Implement Customer.io reporting webhook handling: receive real-time delivery events (sent, delivered, opened, clicked, bounced, complained, unsubscribed), verify HMAC-SHA256 signatures, process events reliably with queuing, and stream to a data warehouse.

## How Reporting Webhooks Work

```
Customer.io                    Your Server                   Data Warehouse
──────────                    ───────────                   ──────────────
Email sent   →  POST /webhooks/cio  →  Verify signature
Email opened →  POST /webhooks/cio  →  Parse event type
Link clicked →  POST /webhooks/cio  →  Route to handler  →  INSERT INTO events
Email bounced → POST /webhooks/cio  →  Suppress user
```

Configure at: Data & Integrations > Integrations > Reporting Webhooks

## Prerequisites

- Public HTTPS endpoint for webhook receiver
- Webhook signing key from Customer.io dashboard
- Express or similar HTTP framework

## Instructions

### Step 1: Define Webhook Event Types

```typescript
// types/customerio-webhooks.ts

// Customer.io reporting webhook event metrics
type CioMetric =
  | "sent"          // Message sent to delivery provider
  | "delivered"     // Delivery provider confirmed receipt
  | "opened"        // Recipient opened the email
  | "clicked"       // Recipient clicked a link
  | "converted"     // Recipient completed a conversion goal
  | "bounced"       // Email bounced (hard or soft)
  | "spammed"       // Recipient marked as spam
  | "unsubscribed"  // Recipient unsubscribed
  | "dropped"       // Message dropped (suppressed, invalid)
  | "deferred"      // Delivery temporarily deferred
  | "failed";       // Delivery failed

interface CioWebhookEvent {
  // Event metadata
  event_id: string;
  metric: CioMetric;
  timestamp: number;          // Unix seconds

  // Recipient info
  customer_id: string;
  email_address?: string;

  // Message info
  subject?: string;
  template_id?: number;
  campaign_id?: number;
  broadcast_id?: number;
  action_id?: number;

  // Delivery details
  delivery_id?: string;

  // Link tracking (for "clicked" events)
  href?: string;
  link_id?: number;
}
```

### Step 2: Webhook Handler with Signature Verification

```typescript
// routes/webhooks/customerio.ts
import { createHmac, timingSafeEqual } from "crypto";
import { Router, Request, Response } from "express";

const WEBHOOK_SECRET = process.env.CUSTOMERIO_WEBHOOK_SECRET!;

function verifySignature(rawBody: Buffer, signature: string): boolean {
  const expected = createHmac("sha256", WEBHOOK_SECRET)
    .update(rawBody)
    .digest("hex");

  try {
    return timingSafeEqual(
      Buffer.from(signature, "utf-8"),
      Buffer.from(expected, "utf-8")
    );
  } catch {
    return false;
  }
}

const router = Router();

// IMPORTANT: Use raw body parser for this route — JSON parsing breaks signature verification
router.post("/webhooks/customerio", (req: Request, res: Response) => {
  const signature = req.headers["x-cio-signature"] as string;
  const rawBody = (req as any).rawBody as Buffer;

  if (!signature || !rawBody) {
    res.status(401).json({ error: "Missing signature" });
    return;
  }

  if (!verifySignature(rawBody, signature)) {
    console.error("CIO webhook: invalid signature");
    res.status(401).json({ error: "Invalid signature" });
    return;
  }

  const event: CioWebhookEvent = JSON.parse(rawBody.toString());

  // Respond 200 immediately — process async to avoid timeouts
  res.sendStatus(200);

  // Process event asynchronously
  handleWebhookEvent(event).catch((err) =>
    console.error("Webhook processing failed:", err)
  );
});
```

### Step 3: Event Router and Handlers

```typescript
// services/customerio-webhook-handler.ts
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

// Deduplication set (use Redis in production)
const processedEvents = new Set<string>();

async function handleWebhookEvent(event: CioWebhookEvent): Promise<void> {
  // Deduplicate by event_id
  if (processedEvents.has(event.event_id)) return;
  processedEvents.add(event.event_id);

  // Limit in-memory set size
  if (processedEvents.size > 100_000) {
    const iterator = processedEvents.values();
    for (let i = 0; i < 50_000; i++) iterator.next();
    // In production, use Redis with TTL instead
  }

  switch (event.metric) {
    case "bounced":
      await handleBounce(event);
      break;
    case "spammed":
      await handleSpamComplaint(event);
      break;
    case "unsubscribed":
      await handleUnsubscribe(event);
      break;
    case "opened":
    case "clicked":
      await handleEngagement(event);
      break;
    case "delivered":
    case "sent":
      await handleDelivery(event);
      break;
    default:
      console.log(`CIO webhook: ${event.metric} for ${event.customer_id}`);
  }
}

async function handleBounce(event: CioWebhookEvent): Promise<void> {
  console.warn(`BOUNCE: ${event.email_address} (user: ${event.customer_id})`);

  // Update user profile with bounce info
  await cio.identify(event.customer_id, {
    email_bounced: true,
    email_bounced_at: event.timestamp,
    last_bounce_delivery_id: event.delivery_id,
  });

  // Suppress after hard bounce to protect sender reputation
  await cio.suppress(event.customer_id);
}

async function handleSpamComplaint(event: CioWebhookEvent): Promise<void> {
  console.error(`SPAM COMPLAINT: ${event.email_address}`);

  // Suppress immediately — spam complaints damage sender reputation
  await cio.suppress(event.customer_id);

  // Record for compliance
  await cio.identify(event.customer_id, {
    spam_complaint: true,
    spam_complaint_at: event.timestamp,
  });
}

async function handleUnsubscribe(event: CioWebhookEvent): Promise<void> {
  await cio.identify(event.customer_id, {
    unsubscribed: true,
    unsubscribed_at: event.timestamp,
  });
}

async function handleEngagement(event: CioWebhookEvent): Promise<void> {
  await cio.identify(event.customer_id, {
    last_email_engaged_at: event.timestamp,
    last_email_metric: event.metric,
  });
}

async function handleDelivery(event: CioWebhookEvent): Promise<void> {
  // Log for analytics — lightweight processing
  console.log(
    `${event.metric}: ${event.delivery_id} to ${event.customer_id}`
  );
}
```

### Step 4: Express Server Setup

```typescript
// server.ts
import express from "express";
import webhookRouter from "./routes/webhooks/customerio";

const app = express();

// Raw body parser for webhook signature verification
// MUST be before any JSON body parser
app.use(
  "/webhooks/customerio",
  express.raw({ type: "application/json" }),
  (req, _res, next) => {
    (req as any).rawBody = req.body;
    req.body = JSON.parse(req.body.toString());
    next();
  }
);

// JSON parser for all other routes
app.use(express.json());

app.use(webhookRouter);

app.listen(3000, () => console.log("Webhook server on :3000"));
```

### Step 5: Stream to Data Warehouse (BigQuery)

```typescript
// services/customerio-warehouse.ts
import { BigQuery } from "@google-cloud/bigquery";

const bq = new BigQuery();
const dataset = bq.dataset("messaging");
const table = dataset.table("customerio_events");

async function streamToWarehouse(event: CioWebhookEvent): Promise<void> {
  await table.insert({
    event_id: event.event_id,
    metric: event.metric,
    customer_id: event.customer_id,
    email_address: event.email_address,
    delivery_id: event.delivery_id,
    campaign_id: event.campaign_id,
    template_id: event.template_id,
    href: event.href,
    timestamp: new Date(event.timestamp * 1000).toISOString(),
    received_at: new Date().toISOString(),
  });
}
```

## Dashboard Configuration

1. Go to **Data & Integrations** > **Integrations** > **Reporting Webhooks**
2. Click **Add Reporting Webhook**
3. Enter your endpoint URL: `https://your-domain.com/webhooks/customerio`
4. Select events to receive (recommended: all for analytics)
5. Copy the webhook signing key to `CUSTOMERIO_WEBHOOK_SECRET`

## Error Handling

| Issue | Solution |
|-------|----------|
| Invalid signature | Verify webhook secret matches dashboard value |
| Duplicate events | Deduplicate by `event_id` (use Redis SET with TTL in production) |
| Slow processing | Return 200 immediately, process async |
| Missing events | Check endpoint is publicly accessible, verify IP allowlist |

## Resources

- [Reporting Webhooks](https://docs.customer.io/integrations/data-out/connections/webhooks/)
- [Webhooks Reference](https://docs.customer.io/integrations/api/webhooks/)
- [Webhook Action in Campaigns](https://docs.customer.io/journeys/webhooks-action/)

## Next Steps

After webhook setup, proceed to `customerio-performance-tuning` for optimization.
