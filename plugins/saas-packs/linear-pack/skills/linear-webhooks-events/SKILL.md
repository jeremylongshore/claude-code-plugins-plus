---
name: linear-webhooks-events
description: |
  Configure and handle Linear webhooks for real-time event processing.
  Use when setting up webhooks, handling issue/project/cycle events,
  or building real-time integrations with Linear.
  Trigger: "linear webhooks", "linear events", "linear real-time",
  "handle linear webhook", "linear webhook setup", "linear webhook payload".
allowed-tools: Read, Write, Edit, Bash(ngrok:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, webhooks]

---
# Linear Webhooks & Events

## Overview
Set up and handle Linear webhooks for real-time event processing. Linear sends HTTP POST requests for data changes on Issues, Comments, Issue Attachments, Documents, Emoji Reactions, Projects, Project Updates, Cycles, Labels, Users, and Issue SLAs.

**Webhook headers:**
- `Linear-Signature` — HMAC-SHA256 hex digest of the raw body
- `Linear-Delivery` — Unique delivery ID for deduplication
- `Linear-Event` — Event type (e.g., "Issue")
- `Content-Type: application/json; charset=utf-8`

**Payload body includes:** `action`, `type`, `data`, `url`, `actor`, `updatedFrom` (previous values on update), `createdAt`, `webhookTimestamp` (UNIX ms).

## Prerequisites
- Linear workspace admin access (required for webhook creation)
- Public HTTPS endpoint for webhook delivery
- Webhook signing secret (generated in Linear Settings > API > Webhooks)

## Instructions

### Step 1: Build Webhook Receiver with Signature Verification
```typescript
import express from "express";
import crypto from "crypto";

const app = express();

// CRITICAL: use raw body parser — JSON parsing destroys the original for signature verification
app.post("/webhooks/linear", express.raw({ type: "*/*" }), (req, res) => {
  const signature = req.headers["linear-signature"] as string;
  const delivery = req.headers["linear-delivery"] as string;
  const eventType = req.headers["linear-event"] as string;
  const rawBody = req.body.toString();

  // 1. Verify HMAC-SHA256 signature
  const expected = crypto
    .createHmac("sha256", process.env.LINEAR_WEBHOOK_SECRET!)
    .update(rawBody)
    .digest("hex");

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    console.error(`Invalid signature for delivery ${delivery}`);
    return res.status(401).json({ error: "Invalid signature" });
  }

  // 2. Parse and verify timestamp (guard against replay attacks)
  const event = JSON.parse(rawBody);
  const age = Date.now() - event.webhookTimestamp;
  if (age > 60000) {
    return res.status(400).json({ error: "Webhook expired" });
  }

  // 3. Respond 200 immediately, process asynchronously
  res.json({ received: true });
  processEvent(event, delivery).catch(err =>
    console.error(`Failed processing ${delivery}:`, err)
  );
});

app.listen(3000, () => console.log("Webhook server on :3000"));
```

### Step 2: Event Type Definition
```typescript
interface LinearWebhookPayload {
  action: "create" | "update" | "remove";
  type: string; // "Issue", "Comment", "Project", "Cycle", "IssueLabel", etc.
  data: Record<string, any>;
  url: string;
  actor?: {
    id: string;
    type: string; // "user", "application"
    name?: string;
  };
  updatedFrom?: Record<string, any>; // Only contains fields that changed
  createdAt: string;
  webhookTimestamp: number;
}
```

### Step 3: Event Router
```typescript
type Handler = (event: LinearWebhookPayload) => Promise<void>;

const handlers: Record<string, Record<string, Handler>> = {
  Issue: {
    create: async (e) => {
      console.log(`New issue: ${e.data.identifier} — ${e.data.title}`);
      console.log(`  Priority: ${e.data.priority}, Team: ${e.data.team?.key}`);
      // e.g., notify Slack, sync to external system
    },
    update: async (e) => {
      // updatedFrom contains ONLY the fields that changed
      if (e.updatedFrom?.stateId) {
        console.log(`${e.data.identifier} state -> ${e.data.state?.name}`);
        if (e.data.state?.type === "completed") {
          await notifySlack(`Done: ${e.data.identifier} ${e.data.title}`);
        }
      }
      if (e.updatedFrom?.assigneeId) {
        console.log(`${e.data.identifier} assigned to ${e.data.assignee?.name}`);
      }
      if (e.updatedFrom?.priority !== undefined) {
        console.log(`${e.data.identifier} priority changed to ${e.data.priority}`);
      }
    },
    remove: async (e) => {
      console.log(`Issue deleted: ${e.data.identifier}`);
    },
  },
  Comment: {
    create: async (e) => {
      console.log(`Comment on ${e.data.issue?.identifier}: ${e.data.body?.substring(0, 100)}`);
    },
  },
  Project: {
    update: async (e) => {
      if (e.updatedFrom?.state) {
        console.log(`Project "${e.data.name}" -> ${e.data.state}`);
      }
    },
  },
  Cycle: {
    update: async (e) => {
      if (e.updatedFrom?.completedAt && e.data.completedAt) {
        console.log(`Cycle "${e.data.name}" completed`);
      }
    },
  },
  ProjectUpdate: {
    create: async (e) => {
      // e.data includes diffMarkdown showing changes since last update
      console.log(`Project update: ${e.data.body?.substring(0, 100)}`);
    },
  },
};

async function processEvent(event: LinearWebhookPayload, deliveryId: string): Promise<void> {
  const handler = handlers[event.type]?.[event.action];
  if (handler) {
    await handler(event);
  } else {
    console.log(`Unhandled: ${event.type}.${event.action} (delivery: ${deliveryId})`);
  }
}
```

### Step 4: Idempotent Processing
Linear may retry failed deliveries. Deduplicate using the `Linear-Delivery` header.

```typescript
// In-memory for simple apps; use Redis/DB for distributed systems
const processedDeliveries = new Set<string>();
const MAX_TRACKED = 10000;

function isDuplicate(deliveryId: string): boolean {
  if (processedDeliveries.has(deliveryId)) return true;
  processedDeliveries.add(deliveryId);
  if (processedDeliveries.size > MAX_TRACKED) {
    const entries = [...processedDeliveries];
    entries.slice(0, MAX_TRACKED / 2).forEach(id => processedDeliveries.delete(id));
  }
  return false;
}

// In webhook handler, after signature verification:
if (isDuplicate(delivery)) {
  return res.json({ status: "duplicate, skipped" });
}
```

### Step 5: Register Webhook
```bash
# Via Linear UI:
# Settings > API > Webhooks > New webhook
# URL: https://your-app.com/webhooks/linear
# Resource types: Issues, Comments, Projects, Cycles
# Teams: All public teams (or select specific ones)

# Via GraphQL API:
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { webhookCreate(input: { url: \"https://your-app.com/webhooks/linear\", resourceTypes: [\"Issue\", \"Comment\", \"Project\", \"Cycle\"], allPublicTeams: true }) { success webhook { id enabled secret } } }"
  }'
```

### Step 6: List and Manage Webhooks via SDK
```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

// List all webhooks
const webhooks = await client.webhooks();
for (const wh of webhooks.nodes) {
  console.log(`${wh.url} — enabled: ${wh.enabled}, types: ${wh.resourceTypes?.join(", ")}`);
}

// Disable a webhook
await client.updateWebhook("webhook-id", { enabled: false });

// Delete a webhook
await client.deleteWebhook("webhook-id");
```

### Step 7: Local Development with ngrok
```bash
# Terminal 1: Start webhook server
npm run dev

# Terminal 2: Expose port 3000
ngrok http 3000
# Copy the https://xxxx.ngrok-free.app URL

# Register in Linear Settings > API > Webhooks > New webhook
# URL: https://xxxx.ngrok-free.app/webhooks/linear
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Invalid signature | Wrong secret or body parsed as JSON | Use `express.raw()`, verify secret matches Linear |
| Webhook not received | URL not publicly accessible | Check HTTPS, firewall rules, ngrok tunnel |
| Duplicate processing | Linear retried delivery | Deduplicate using `Linear-Delivery` header |
| Handler timeout | Processing takes too long | Respond 200 immediately, process async |
| Missing `updatedFrom` | Field didn't change | `updatedFrom` only contains changed field keys |
| `actor` is null | System-triggered event | Check `actor.type` before accessing `.name` |

## Examples

### Slack Notification on Issue Completion
```typescript
async function notifySlack(message: string) {
  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: message }),
  });
}

// In Issue.update handler:
if (e.updatedFrom?.stateId && e.data.state?.type === "completed") {
  await notifySlack(
    `*${e.data.identifier}* completed by ${e.actor?.name ?? "system"}\n${e.data.title}`
  );
}
```

## Resources
- [Linear Webhooks Documentation](https://linear.app/developers/webhooks)
- [Webhook Payload Format](https://developers.linear.app/docs/graphql/webhooks)
- [ngrok Documentation](https://ngrok.com/docs)
