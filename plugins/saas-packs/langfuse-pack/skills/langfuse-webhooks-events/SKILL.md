---
name: langfuse-webhooks-events
description: |
  Configure Langfuse webhooks and event callbacks for real-time notifications.
  Use when setting up trace notifications, configuring evaluation callbacks,
  or integrating Langfuse events with external systems.
  Trigger with phrases like "langfuse webhooks", "langfuse events",
  "langfuse notifications", "langfuse callbacks", "langfuse alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Webhooks & Events

## Overview
Configure webhooks and event callbacks to receive real-time notifications from Langfuse.

## Prerequisites
- Langfuse account with webhook access
- HTTPS endpoint to receive webhooks
- Understanding of event-driven architecture

## Instructions

### Step 1: Create Webhook Endpoint

```typescript
// api/webhooks/langfuse/route.ts (Next.js App Router)
import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

const WEBHOOK_SECRET = process.env.LANGFUSE_WEBHOOK_SECRET!;

interface LangfuseWebhookPayload {
  event: string;
  timestamp: string;
  data: {
    traceId?: string;
    observationId?: string;
    scoreId?: string;
    projectId: string;
    [key: string]: any;
  };
}

function verifySignature(payload: string, signature: string): boolean {
  const expectedSignature = crypto
    .createHmac("sha256", WEBHOOK_SECRET)
    .update(payload)
    .digest("hex");

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

export async function POST(request: NextRequest) {
  const payload = await request.text();
  const signature = request.headers.get("x-langfuse-signature");

  // Verify webhook signature
  if (!signature || !verifySignature(payload, signature)) {
    console.error("Invalid webhook signature");
    return NextResponse.json({ error: "Invalid signature" }, { status: 401 });  # HTTP 401 Unauthorized
  }

  const event: LangfuseWebhookPayload = JSON.parse(payload);

  console.log(`Received Langfuse event: ${event.event}`);

  // Handle different event types
  switch (event.event) {
    case "trace.created":
      await handleTraceCreated(event.data);
      break;

    case "trace.updated":
      await handleTraceUpdated(event.data);
      break;

    case "score.created":
      await handleScoreCreated(event.data);
      break;

    case "generation.created":
      await handleGenerationCreated(event.data);
      break;

    default:
      console.log(`Unhandled event type: ${event.event}`);
  }

  return NextResponse.json({ received: true });
}

async function handleTraceCreated(data: any) {
  console.log(`New trace created: ${data.traceId}`);
  // Trigger downstream actions
}

async function handleTraceUpdated(data: any) {
  // Check for errors
  if (data.level === "ERROR") {
    await sendAlertNotification({
      title: "Langfuse Error Trace",
      traceId: data.traceId,
      message: data.statusMessage,
    });
  }
}

async function handleScoreCreated(data: any) {
  // Alert on low scores
  if (data.value < 0.5) {
    await sendAlertNotification({
      title: "Low Score Alert",
      traceId: data.traceId,
      score: data.name,
      value: data.value,
    });
  }
}

async function handleGenerationCreated(data: any) {
  // Track token usage
  if (data.usage) {
    await trackTokenUsage({
      model: data.model,
      promptTokens: data.usage.promptTokens,
      completionTokens: data.usage.completionTokens,
    });
  }
}
```

### Step 2: Configure Webhook in Langfuse Dashboard

```markdown
1. Go to Langfuse Dashboard -> Settings -> Webhooks
2. Click "Add Webhook"
3. Configure:
   - URL: https://your-domain.com/api/webhooks/langfuse
   - Events: Select events to subscribe to
   - Secret: Generate and save webhook secret
4. Test webhook with "Send Test Event"
```

### Step 3: Implement Event Processing Queue

```typescript
// lib/webhook-queue.ts
import { Queue, Worker } from "bullmq";
import Redis from "ioredis";

const connection = new Redis(process.env.REDIS_URL!);

// Queue for processing webhook events
export const langfuseQueue = new Queue("langfuse-events", { connection });

// Webhook handler adds to queue
export async function queueWebhookEvent(event: LangfuseWebhookPayload) {
  await langfuseQueue.add(event.event, event, {
    removeOnComplete: 1000,  # 1000: 1 second in ms
    removeOnFail: 5000,  # 5000: 5 seconds in ms
    attempts: 3,
    backoff: {
      type: "exponential",
      delay: 1000,  # 1 second in ms
    },
  });
}

// Worker processes events
const worker = new Worker(
  "langfuse-events",
  async (job) => {
    const event = job.data as LangfuseWebhookPayload;

    switch (job.name) {
      case "trace.created":
        await processTraceCreated(event);
        break;

      case "score.created":
        await processScoreCreated(event);
        break;

      // ... other handlers
    }
  },
  { connection }
);

worker.on("failed", (job, error) => {
  console.error(`Job ${job?.id} failed:`, error);
});
```

### Step 4: Real-Time Event Streaming (Alternative)

```typescript
// For real-time updates without webhooks
// Use Langfuse API polling with caching

import { Langfuse } from "langfuse";

class LangfuseEventStream {
  private langfuse: Langfuse;
  private lastChecked: Date;
  private pollInterval: number;

  constructor(pollIntervalMs: number = 5000) {  # 5000: 5 seconds in ms
    this.langfuse = new Langfuse();
    this.lastChecked = new Date();
    this.pollInterval = pollIntervalMs;
  }

  async start(handlers: {
    onTrace?: (trace: any) => void;
    onScore?: (score: any) => void;
  }) {
    setInterval(async () => {
      await this.pollForUpdates(handlers);
    }, this.pollInterval);
  }

  private async pollForUpdates(handlers: {
    onTrace?: (trace: any) => void;
    onScore?: (score: any) => void;
  }) {
    try {
      const traces = await this.langfuse.fetchTraces({
        fromTimestamp: this.lastChecked,
      });

      for (const trace of traces.data) {
        handlers.onTrace?.(trace);
      }

      this.lastChecked = new Date();
    } catch (error) {
      console.error("Failed to poll Langfuse:", error);
    }
  }
}

// Usage
const stream = new LangfuseEventStream(10000); // 10 second poll  # 10000: 10 seconds in ms
stream.start({
  onTrace: (trace) => {
    if (trace.level === "ERROR") {
      sendSlackAlert(`Error in trace ${trace.id}`);
    }
  },
});
```

### Step 5: Integration with External Services

```typescript
// Slack notification on errors
async function sendSlackNotification(event: LangfuseWebhookPayload) {
  if (event.data.level !== "ERROR") return;

  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      blocks: [
        {
          type: "header",
          text: {
            type: "plain_text",
            text: "Langfuse Error Alert",
          },
        },
        {
          type: "section",
          fields: [
            {
              type: "mrkdwn",
              text: `*Trace ID:*\n${event.data.traceId}`,
            },
            {
              type: "mrkdwn",
              text: `*Error:*\n${event.data.statusMessage}`,
            },
          ],
        },
        {
          type: "actions",
          elements: [
            {
              type: "button",
              text: { type: "plain_text", text: "View Trace" },
              url: `https://cloud.langfuse.com/trace/${event.data.traceId}`,
            },
          ],
        },
      ],
    }),
  });
}

// PagerDuty for critical alerts
async function sendPagerDutyAlert(event: LangfuseWebhookPayload) {
  await fetch("https://events.pagerduty.com/v2/enqueue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      routing_key: process.env.PAGERDUTY_ROUTING_KEY,
      event_action: "trigger",
      payload: {
        summary: `Langfuse: ${event.event}`,
        severity: "critical",
        source: "langfuse",
        custom_details: event.data,
      },
    }),
  });
}
```

## Output
- Secure webhook endpoint with signature verification
- Event processing queue for reliability
- Real-time polling alternative
- External service integrations (Slack, PagerDuty)

## Webhook Event Types

| Event | Description | Use Case |
|-------|-------------|----------|
| `trace.created` | New trace started | Real-time monitoring |
| `trace.updated` | Trace modified | Error detection |
| `generation.created` | LLM call logged | Token tracking |
| `score.created` | Score added | Quality alerts |
| `score.updated` | Score modified | Evaluation updates |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify webhook secret |
| Missed events | Handler failure | Use queue with retries |
| Duplicate events | No idempotency | Track processed event IDs |
| Timeout | Slow handler | Queue events, respond fast |

## Examples

### Idempotent Event Processing
```typescript
const processedEvents = new Set<string>();

async function handleWebhook(event: LangfuseWebhookPayload) {
  const eventId = `${event.event}-${event.timestamp}-${event.data.traceId}`;

  if (processedEvents.has(eventId)) {
    console.log(`Skipping duplicate event: ${eventId}`);
    return;
  }

  processedEvents.add(eventId);
  // Process event...

  // Clean up old events periodically
  if (processedEvents.size > 10000) {  # 10000: 10 seconds in ms
    processedEvents.clear();
  }
}
```

## Resources
- [Langfuse Webhooks](https://langfuse.com/docs/webhooks)
- [Langfuse API Reference](https://langfuse.com/docs/api-reference)
- [BullMQ Documentation](https://docs.bullmq.io/)

## Next Steps
For performance optimization, see `langfuse-performance-tuning`.