---
name: apify-webhooks-events
description: 'Implement Apify webhooks for Actor run notifications and event-driven
  pipelines.

  Use when setting up run completion alerts, building event-driven scraping pipelines,

  or configuring ad-hoc webhooks for individual runs.

  Trigger with "apify webhook", "apify events", "actor run notification",

  "apify run succeeded webhook", "apify ad-hoc webhook".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Webhooks & Events

## Overview

Configure webhooks to receive notifications when Actor runs complete, fail, or time out. Apify supports both persistent webhooks (for all runs of an Actor) and ad-hoc webhooks (for a single run). Event-driven architecture is the recommended pattern for production Apify integrations.

## Prerequisites

- `npm install apify-client` in your project (and `express` if you build an HTTP handler)
- An API token in `APIFY_TOKEN` — read it from the environment
  (`process.env.APIFY_TOKEN`) or pass `Authorization: Bearer $APIFY_TOKEN` on REST
  calls, never hard-code it
- A public HTTPS endpoint for Apify to POST to (use ngrok while developing)
- Familiarity with `apify-sdk-patterns`

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

Persistent webhooks fire for every run of an Actor. Set `condition.actorId`, list
the `eventTypes` you care about, and shape the delivered body with
`payloadTemplate`:

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

const webhook = await client.webhooks().create({
  eventTypes: ['ACTOR.RUN.SUCCEEDED', 'ACTOR.RUN.FAILED', 'ACTOR.RUN.TIMED_OUT'],
  condition: { actorId: 'YOUR_ACTOR_ID' },
  requestUrl: 'https://your-app.com/api/webhooks/apify',
  payloadTemplate: JSON.stringify({
    eventType: '{{eventType}}',
    actorRunId: '{{actorRunId}}',
    defaultDatasetId: '{{resource.defaultDatasetId}}',
    status: '{{resource.status}}',
    statusMessage: '{{resource.statusMessage}}',
  }),
  isAdHoc: false,
});

console.log(`Webhook created: ${webhook.id}`);
```

The full payload template (all run fields) and the complete variable table are in
[payload templates & local testing](references/examples.md).

### Step 2: Use Ad-Hoc Webhooks for Single Runs

Ad-hoc webhooks are created at run time and fire only for that specific run — pass
a `webhooks` array when starting the Actor:

```typescript
const run = await client.actor('username/my-actor').start(
  { startUrls: [{ url: 'https://example.com' }] },
  {
    webhooks: [{
      eventTypes: ['ACTOR.RUN.SUCCEEDED', 'ACTOR.RUN.FAILED'],
      requestUrl: 'https://your-app.com/api/webhooks/apify',
    }],
  },
);
```

The equivalent REST/`curl` form is in [payload templates & local testing](references/examples.md).

### Step 3: Handle the Webhook

Your endpoint must return a `2xx` within 30 seconds, so acknowledge immediately and
process asynchronously. On `SUCCEEDED`, fetch the dataset via `defaultDatasetId`; on
`FAILED`/`TIMED_OUT`, pull the run log and alert:

```typescript
app.post('/api/webhooks/apify', async (req, res) => {
  res.status(200).json({ received: true }); // ack first
  try {
    await processWebhook(req.body); // switch on eventType, fetch dataset, alert
  } catch (error) {
    console.error('Webhook processing failed:', error);
  }
});
```

The full `processWebhook` switch (dataset fetch, log tail, oncall alerting) is in
[full implementation](references/implementation.md).

### Step 4: Make Processing Idempotent, Chain Pipelines, and Manage Webhooks

Apify may deliver a webhook more than once, so dedupe on
`${actorRunId}:${eventType}` before doing work. You can also chain Actors (Stage 1
`SUCCEEDED` → start Stage 2) and manage the webhook lifecycle (`list`, `update`,
`delete`, inspect `dispatches`). All three patterns — idempotent processing,
event-driven pipeline, and lifecycle management — are in
[full implementation](references/implementation.md).

## Output

- A created webhook returns its `id` (persistent webhooks are visible under
  `client.webhooks().list()`; ad-hoc webhooks are scoped to one run)
- On each matching event, Apify POSTs the rendered `payloadTemplate` JSON to your
  `requestUrl`
- `client.webhook(id).dispatches().list()` returns the delivery history — each entry
  carries a `status`, `createdAt`, and the endpoint's `responseStatus` so you can
  confirm delivery or diagnose retries

## Examples

- **Persistent + ad-hoc webhook creation** — Steps 1 and 2 above
- **Full handler, idempotency, pipeline chaining, lifecycle management** — [full implementation](references/implementation.md)
- **Payload template variables, REST/`curl` creation, and local testing with ngrok** — [payload templates & local testing](references/examples.md)

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
