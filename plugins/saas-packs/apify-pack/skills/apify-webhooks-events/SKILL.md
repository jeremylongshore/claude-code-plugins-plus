---
name: apify-webhooks-events
description: |
  Implement Apify webhooks for Actor run notifications and event-driven pipelines.
  Use when setting up run completion alerts, building event-driven scraping pipelines,
  or configuring ad-hoc webhooks for individual runs.
  Trigger: "apify webhook", "apify events", "actor run notification",
  "apify run succeeded webhook", "apify ad-hoc webhook".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Webhooks & Events

## Overview

Configure webhooks to receive notifications when Actor runs complete, fail, or time out. Apify supports both persistent webhooks (for all runs of an Actor) and ad-hoc webhooks (for a single run). Event-driven architecture is the recommended pattern for production Apify integrations.

## Event Types

| Event | Fired When |
|-------|-----------|
| `ACTOR.RUN.CREATED` | A new Actor run starts |
| `ACTOR.RUN.SUCCEEDED` | Run finishes with `SUCCEEDED` status |
| `ACTOR.RUN.FAILED` | Run finishes with `FAILED` status |
| `ACTOR.RUN.ABORTED` | Run is manually or programmatically aborted |
| `ACTOR.RUN.TIMED_OUT` | Run exceeds its timeout |
| `ACTOR.RUN.RESURRECTED` | A finished run is resurrected |

## Instructions

### Step 1: Create a Persistent Webhook

Persistent webhooks fire for every run of an Actor:

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

const webhook = await client.webhooks().create({
  eventTypes: [
    'ACTOR.RUN.SUCCEEDED',
    'ACTOR.RUN.FAILED',
    'ACTOR.RUN.TIMED_OUT',
  ],
  condition: {
    actorId: 'YOUR_ACTOR_ID',
  },
  requestUrl: 'https://your-app.com/api/webhooks/apify',
  payloadTemplate: JSON.stringify({
    eventType: '{{eventType}}',
    createdAt: '{{createdAt}}',
    actorId: '{{actorId}}',
    actorRunId: '{{actorRunId}}',
    defaultDatasetId: '{{resource.defaultDatasetId}}',
    defaultKeyValueStoreId: '{{resource.defaultKeyValueStoreId}}',
    status: '{{resource.status}}',
    statusMessage: '{{resource.statusMessage}}',
    startedAt: '{{resource.startedAt}}',
    finishedAt: '{{resource.finishedAt}}',
  }),
  isAdHoc: false,
});

console.log(`Webhook created: ${webhook.id}`);
```

### Step 2: Use Ad-Hoc Webhooks for Single Runs

Ad-hoc webhooks are created at run time and fire only for that specific run:

```typescript
// Ad-hoc webhook via API (pass webhooks array when starting a run)
const run = await client.actor('username/my-actor').start(
  { startUrls: [{ url: 'https://example.com' }] },
  {
    webhooks: [
      {
        eventTypes: ['ACTOR.RUN.SUCCEEDED', 'ACTOR.RUN.FAILED'],
        requestUrl: 'https://your-app.com/api/webhooks/apify',
        payloadTemplate: JSON.stringify({
          runId: '{{actorRunId}}',
          status: '{{resource.status}}',
          datasetId: '{{resource.defaultDatasetId}}',
        }),
      },
    ],
  },
);
```

Via REST API with curl:

```bash
curl -X POST \
  "https://api.apify.com/v2/acts/USERNAME~ACTOR_NAME/runs" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "startUrls": [{"url": "https://example.com"}],
    "webhooks": [
      {
        "eventTypes": ["ACTOR.RUN.SUCCEEDED"],
        "requestUrl": "https://your-app.com/webhook"
      }
    ]
  }'
```

### Step 3: Build the Webhook Handler

```typescript
import express from 'express';
import { ApifyClient } from 'apify-client';

const app = express();
const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

app.use(express.json());

// Webhook endpoint
app.post('/api/webhooks/apify', async (req, res) => {
  // Respond immediately (Apify expects 2xx within 30 seconds)
  res.status(200).json({ received: true });

  // Process asynchronously
  try {
    await processWebhook(req.body);
  } catch (error) {
    console.error('Webhook processing failed:', error);
  }
});

async function processWebhook(payload: {
  eventType: string;
  actorRunId: string;
  defaultDatasetId?: string;
  status: string;
  statusMessage?: string;
}) {
  const { eventType, actorRunId, defaultDatasetId } = payload;

  switch (eventType) {
    case 'ACTOR.RUN.SUCCEEDED': {
      if (!defaultDatasetId) return;

      // Fetch results from the dataset
      const { items } = await client
        .dataset(defaultDatasetId)
        .listItems({ limit: 10000 });

      console.log(`Run ${actorRunId} succeeded with ${items.length} items`);

      // Process results: save to DB, trigger downstream jobs, etc.
      await saveToDatabase(items);
      await notifyTeam(`Scrape completed: ${items.length} items`);
      break;
    }

    case 'ACTOR.RUN.FAILED':
    case 'ACTOR.RUN.TIMED_OUT': {
      console.error(`Run ${actorRunId} ${eventType}: ${payload.statusMessage}`);

      // Get full run log for debugging
      const log = await client.run(actorRunId).log().get();
      await alertOncall({
        subject: `Apify run ${eventType}`,
        runId: actorRunId,
        message: payload.statusMessage,
        logTail: log?.slice(-1000),
      });
      break;
    }

    case 'ACTOR.RUN.ABORTED':
      console.warn(`Run ${actorRunId} was aborted`);
      break;

    default:
      console.log(`Unhandled event: ${eventType}`);
  }
}
```

### Step 4: Idempotent Processing

Webhooks may be delivered more than once. Guard against duplicates:

```typescript
// Using a Set for in-memory dedup (use Redis/DB in production)
const processedRuns = new Set<string>();

async function processWebhookIdempotent(payload: {
  actorRunId: string;
  eventType: string;
}) {
  const dedupeKey = `${payload.actorRunId}:${payload.eventType}`;

  if (processedRuns.has(dedupeKey)) {
    console.log(`Skipping duplicate: ${dedupeKey}`);
    return;
  }

  processedRuns.add(dedupeKey);

  // Process the webhook...
  await processWebhook(payload);

  // Cleanup old entries (keep last 10000)
  if (processedRuns.size > 10000) {
    const entries = Array.from(processedRuns);
    entries.slice(0, entries.length - 10000).forEach(e => processedRuns.delete(e));
  }
}
```

### Step 5: Event-Driven Pipeline

Chain Actors together using webhooks:

```typescript
// Actor A finishes → webhook triggers → start Actor B

app.post('/api/webhooks/pipeline', async (req, res) => {
  res.status(200).json({ received: true });

  const { eventType, actorRunId, defaultDatasetId } = req.body;

  if (eventType !== 'ACTOR.RUN.SUCCEEDED') return;

  // Stage 1 completed, start Stage 2
  console.log(`Pipeline Stage 1 done (run ${actorRunId}). Starting Stage 2...`);

  const stage2Run = await client.actor('username/data-processor').start(
    {
      sourceDatasetId: defaultDatasetId,
      outputFormat: 'json',
    },
    {
      webhooks: [{
        eventTypes: ['ACTOR.RUN.SUCCEEDED', 'ACTOR.RUN.FAILED'],
        requestUrl: 'https://your-app.com/api/webhooks/pipeline-stage3',
      }],
    },
  );

  console.log(`Stage 2 started: ${stage2Run.id}`);
});
```

### Step 6: Manage Webhooks

```typescript
// List all webhooks
const { items: webhooks } = await client.webhooks().list();
webhooks.forEach(wh => {
  console.log(`${wh.id} | ${wh.eventTypes.join(',')} | ${wh.requestUrl}`);
});

// Update a webhook
await client.webhook('WEBHOOK_ID').update({
  requestUrl: 'https://new-url.com/webhook',
  isEnabled: true,
});

// Delete a webhook
await client.webhook('WEBHOOK_ID').delete();

// Get webhook dispatch history (see delivery attempts)
const { items: dispatches } = await client
  .webhook('WEBHOOK_ID')
  .dispatches()
  .list();
dispatches.forEach(d => {
  console.log(`${d.status} | ${d.createdAt} | HTTP ${d.responseStatus}`);
});
```

## Webhook Payload Template Variables

| Variable | Description |
|----------|-------------|
| `{{eventType}}` | Event type string |
| `{{eventData}}` | Full event data object |
| `{{createdAt}}` | Event creation timestamp |
| `{{actorId}}` | Actor ID |
| `{{actorRunId}}` | Run ID |
| `{{actorTaskId}}` | Task ID (if run from a task) |
| `{{resource.*}}` | Any field from the run object |

## Testing Webhooks Locally

```bash
# Use ngrok to expose local server
ngrok http 3000
# Copy the HTTPS URL

# Create a test webhook pointing to ngrok
# Then trigger a run to see the webhook fire

# Or manually simulate a webhook payload
curl -X POST http://localhost:3000/api/webhooks/apify \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "ACTOR.RUN.SUCCEEDED",
    "actorRunId": "test-run-123",
    "defaultDatasetId": "test-dataset-456",
    "status": "SUCCEEDED"
  }'
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not delivered | URL unreachable | Verify HTTPS, check firewall |
| Duplicate processing | Webhook retry on non-2xx | Implement idempotency |
| Slow processing | Handler takes >30s | Respond 200 immediately, process async |
| Missing data in payload | Wrong template vars | Check template variable spelling |
| Webhook disabled | Too many failures | Re-enable in Console or via API |

## Resources

- [Webhook Event Types](https://docs.apify.com/platform/integrations/webhooks/events)
- [Webhook Actions](https://docs.apify.com/platform/integrations/webhooks/actions)
- [Ad-Hoc Webhooks](https://docs.apify.com/platform/integrations/webhooks/ad-hoc-webhooks)

## Next Steps

For performance optimization, see `apify-performance-tuning`.
