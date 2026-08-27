---
name: intercom-webhooks-events
description: 'Implement Intercom webhook handling and data event tracking.

  Use when setting up webhook endpoints, processing Intercom notifications,

  or submitting custom data events for contact activity tracking.

  Trigger with phrases like "intercom webhook", "intercom events",

  "intercom webhook signature", "handle intercom events", "intercom data events",

  "track intercom events".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Webhooks & Events

## Overview

Handle incoming Intercom webhooks (notifications) with signature verification and implement outbound data event tracking via the Events API. Incoming webhooks push conversation and contact changes to your endpoint; outbound data events push custom activity into Intercom for segmentation and messaging.

The full, copy-ready code lives in `references/`; this file walks the workflow at a high level so you can follow it start to finish, then drill in for depth.

## Prerequisites

- HTTPS endpoint accessible from internet
- Webhook secret from Intercom Developer Hub
- Access token from Intercom Developer Hub (for outbound data events)
- `intercom-client` SDK installed
- Redis or database for idempotency (recommended)

## Authentication

Two distinct credentials, both issued from the Intercom Developer Hub and read from environment variables — never hard-code them:

- **Incoming webhooks** are verified with `INTERCOM_WEBHOOK_SECRET`. Intercom signs every delivery with HMAC-SHA1 in the `X-Hub-Signature` header; you recompute the digest over the **raw** request body and compare with `crypto.timingSafeEqual`. Reject any request that fails or is missing the header.
- **Outbound data events** authenticate with a bearer `INTERCOM_ACCESS_TOKEN` passed to `IntercomClient`.

## Instructions

Read the relevant reference file, then use Write/Edit to scaffold the handler into the target project.

1. **Build the signed endpoint.** Create an Express route that captures the **raw** body (`express.raw`), verifies the `X-Hub-Signature` HMAC-SHA1 digest against `INTERCOM_WEBHOOK_SECRET`, and returns `200` within 5 seconds — Intercom treats a slower response as a failure. Respond first, process after. See [incoming webhooks walkthrough](references/incoming-webhooks.md) Step 1.
2. **Model the payload.** Every delivery is a `notification_event` envelope carrying `topic`, `id`, and `data.item` (the changed resource). Type it so the router is safe. See [incoming webhooks walkthrough](references/incoming-webhooks.md) Step 2.
3. **Route by topic.** Dispatch on `notification.topic` through a handler map; log and no-op unknown topics rather than throwing. Pick topics from the [topics reference](references/webhook-topics.md). See [incoming webhooks walkthrough](references/incoming-webhooks.md) Step 3.
4. **Add idempotency.** Intercom retries a failed delivery once after ~1 minute. Guard each `notification.id` with a Redis `SET NX` lock so retries never double-process; release the lock on failure to allow a genuine retry. See [incoming webhooks walkthrough](references/incoming-webhooks.md) Step 4.
5. **Track outbound events.** Submit custom activity with `client.dataEvents.create` using a past-tense `verb-noun` `eventName`, a Unix `createdAt`, the contact's external `userId`, and optional `metadata`. See [data events walkthrough](references/data-events.md) Step 5.
6. **Submit in bulk when needed.** There is no batch events endpoint — throttle individual `dataEvents.create` calls (e.g. a short delay every 50) and tally succeeded/failed. See [data events walkthrough](references/data-events.md) Step 6.

## Output

A working integration produces:

- A signed `/webhooks/intercom` endpoint that returns `200 {"received": true}` on valid deliveries and `401` on missing/invalid signatures.
- Per-topic handler execution logged as `Processed <topic>: <id>`, with unknown topics logged and skipped.
- Idempotent processing — duplicate `notification.id` deliveries are skipped with `Duplicate webhook skipped: <id>`.
- Outbound `dataEvents.create` calls that appear on the contact's Intercom timeline; bulk runs return `{ succeeded, failed }` counts.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Secret mismatch | Verify secret matches Developer Hub |
| Timeout (5s) | Slow processing | Queue events, respond immediately |
| Duplicate events | Retry delivery | Implement idempotency with Redis |
| Missing topic handler | New topic added | Log unhandled topics, add handler |
| Event rejected (422) | Invalid user_id or event_name | Verify contact exists, use verb-noun naming |

## Examples

**Verify a signature and respond fast** (skeleton — full version in [incoming webhooks](references/incoming-webhooks.md)):

```typescript
const expected = "sha1=" + crypto
  .createHmac("sha1", process.env.INTERCOM_WEBHOOK_SECRET!)
  .update(req.body)              // raw Buffer, not parsed JSON
  .digest("hex");
if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
  return res.status(401).json({ error: "Invalid signature" });
}
res.status(200).json({ received: true });   // respond within 5s, then process async
```

**Track a custom data event** (full version in [data events](references/data-events.md)):

```typescript
await client.dataEvents.create({
  eventName: "completed-onboarding",         // past-tense verb-noun
  createdAt: Math.floor(Date.now() / 1000),
  userId: "user-12345",                      // contact's external ID
  metadata: { steps_completed: 5, plan: "pro" },
});
```

More: [incoming webhooks](references/incoming-webhooks.md) · [data events](references/data-events.md) · [webhook topics](references/webhook-topics.md).

## Resources

- [Webhook Setup](https://developers.intercom.com/docs/webhooks/setting-up-webhooks)
- [Webhook Topics](https://developers.intercom.com/docs/references/webhooks/webhook-models)
- [Webhook Notifications](https://developers.intercom.com/docs/webhooks/webhook-notifications)
- [Data Events API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/data-events)

## Next Steps

For performance optimization once the webhook endpoint and event pipeline are live, see the `intercom-performance-tuning` skill to profile throughput and tune rate limits.
