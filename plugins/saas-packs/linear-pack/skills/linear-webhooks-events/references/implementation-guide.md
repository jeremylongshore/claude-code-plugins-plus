# Linear Webhooks & Events - Implementation Guide

Detailed implementation examples and code patterns.

## Available Event Types

| Event Type | Description |
|------------|-------------|
| `Issue` | Issue created, updated, or removed |
| `IssueComment` | Comment added or updated |
| `Project` | Project changes |
| `Cycle` | Cycle (sprint) changes |
| `Label` | Label changes |
| `Reaction` | Emoji reactions |

## Instructions

### Step 1: Create Webhook Endpoint
```typescript
// api/webhooks/linear.ts (Vercel/Next.js style)
import crypto from "crypto";
import type { NextApiRequest, NextApiResponse } from "next";

export const config = {
  api: {
    bodyParser: false, // Need raw body for signature
  },
};

async function getRawBody(req: NextApiRequest): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

function verifySignature(payload: string, signature: string): boolean {
  const secret = process.env.LINEAR_WEBHOOK_SECRET!;
  const hmac = crypto.createHmac("sha256", secret);
  const expectedSignature = hmac.update(payload).digest("hex");

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const rawBody = await getRawBody(req);
  const signature = req.headers["linear-signature"] as string;

  if (!signature || !verifySignature(rawBody, signature)) {
    return res.status(401).json({ error: "Invalid signature" });
  }

  const event = JSON.parse(rawBody);

  // Process event
  await processLinearEvent(event);

  return res.status(200).json({ received: true });
}
```

### Step 2: Event Processing Router
```typescript
// lib/webhook-handlers.ts
interface LinearWebhookPayload {
  action: "create" | "update" | "remove";
  type: string;
  data: Record<string, unknown>;
  createdAt: string;
  organizationId: string;
  webhookTimestamp: number;
  webhookId: string;
}

type EventHandler = (data: Record<string, unknown>, action: string) => Promise<void>;

const handlers: Record<string, EventHandler> = {
  Issue: handleIssueEvent,
  IssueComment: handleCommentEvent,
  Project: handleProjectEvent,
  Cycle: handleCycleEvent,
};

export async function processLinearEvent(payload: LinearWebhookPayload) {
  const handler = handlers[payload.type];

  if (!handler) {
    console.log(`No handler for event type: ${payload.type}`);
    return;
  }

  try {
    await handler(payload.data, payload.action);
  } catch (error) {
    console.error(`Error processing ${payload.type} event:`, error);
    throw error;
  }
}

async function handleIssueEvent(data: Record<string, unknown>, action: string) {
  const issue = data as {
    id: string;
    identifier: string;
    title: string;
    state: { name: string };
    priority: number;
    team: { key: string };
  };

  console.log(`Issue ${action}: ${issue.identifier} - ${issue.title}`);

  switch (action) {
    case "create":
      await onIssueCreated(issue);
      break;
    case "update":
      await onIssueUpdated(issue);
      break;
    case "remove":
      await onIssueRemoved(issue.id);
      break;
  }
}

async function handleCommentEvent(data: Record<string, unknown>, action: string) {
  const comment = data as {
    id: string;
    body: string;
    issue: { identifier: string };
    user: { name: string };
  };

  console.log(`Comment ${action} on ${comment.issue.identifier} by ${comment.user.name}`);
}

async function handleProjectEvent(data: Record<string, unknown>, action: string) {
  console.log(`Project ${action}:`, data);
}

async function handleCycleEvent(data: Record<string, unknown>, action: string) {
  console.log(`Cycle ${action}:`, data);
}
```

### Step 3: Business Logic Handlers
```typescript
// lib/linear-handlers.ts
import { sendSlackNotification } from "./slack";
import { syncToDatabase } from "./database";

async function onIssueCreated(issue: any) {
  // Sync to local database
  await syncToDatabase("issues", issue.id, issue);

  // Notify Slack for high-priority issues
  if (issue.priority <= 2) {
    await sendSlackNotification({
      channel: "#engineering-alerts",
      text: `New high-priority issue: ${issue.identifier} - ${issue.title}`,
    });
  }
}

async function onIssueUpdated(issue: any) {
  // Update local cache
  await syncToDatabase("issues", issue.id, issue);

  // Check for state changes
  if (issue.state?.name === "Done") {
    await celebrateCompletion(issue);
  }
}

async function onIssueRemoved(issueId: string) {
  await syncToDatabase("issues", issueId, null); // Soft delete
}

async function celebrateCompletion(issue: any) {
  console.log(`Issue completed: ${issue.identifier}`);
}
```

### Step 4: Register Webhook in Linear
```bash
# Using Linear UI:
# 1. Go to Settings > API > Webhooks
# 2. Click "Create webhook"
# 3. Enter your endpoint URL
# 4. Select events to receive
# 5. Save and copy the signing secret
```

```typescript
// Or via API
import { LinearClient } from "@linear/sdk";

async function createWebhook() {
  const client = new LinearClient({
    apiKey: process.env.LINEAR_API_KEY!,
  });

  const result = await client.createWebhook({
    url: "https://your-domain.com/api/webhooks/linear",
    label: "My Integration Webhook",
    teamId: "your-team-id", // Optional: limit to specific team
    resourceTypes: ["Issue", "IssueComment", "Project"],
  });

  if (result.success) {
    const webhook = await result.webhook;
    console.log("Webhook created:", webhook?.id);
    console.log("Secret (save this!):", webhook?.secret);
  }
}
```

### Step 5: Local Development with ngrok
```bash
# Start your local server
npm run dev  # Runs on localhost:3000

# In another terminal, start ngrok
ngrok http 3000

# Copy the https URL and add to Linear webhook settings
# Example: https://abc123.ngrok.io/api/webhooks/linear
```

### Step 6: Idempotent Event Processing
```typescript
// lib/idempotency.ts
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

export async function processIdempotent(
  webhookId: string,
  processor: () => Promise<void>
): Promise<boolean> {
  const key = `webhook:${webhookId}`;

  // Check if already processed
  const exists = await redis.exists(key);
  if (exists) {
    console.log(`Webhook ${webhookId} already processed, skipping`);
    return false;
  }

  // Mark as processing
  await redis.setex(key, 86400, "processing"); // 24 hour TTL

  try {
    await processor();
    await redis.setex(key, 86400, "completed");
    return true;
  } catch (error) {
    await redis.del(key); // Allow retry
    throw error;
  }
}

// Usage in webhook handler
await processIdempotent(payload.webhookId, async () => {
  await processLinearEvent(payload);
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid signature` | Wrong secret or tampering | Verify webhook secret |
| `Timeout` | Processing too slow | Use async queue |
| `Duplicate events` | Webhook retry | Implement idempotency |
| `Missing data` | Partial event | Handle gracefully |
