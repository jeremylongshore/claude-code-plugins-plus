---
name: klaviyo-webhooks-events
description: 'Implement Klaviyo webhooks with HMAC-SHA256 signature verification and
  event handling.

  Use when setting up webhook endpoints, handling Klaviyo event notifications,

  or creating event-driven integrations with Klaviyo.

  Trigger with phrases like "klaviyo webhook", "klaviyo events",

  "klaviyo webhook signature", "handle klaviyo events", "klaviyo notifications".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Webhooks & Events

## Overview

Set up Klaviyo webhooks with HMAC-SHA256 signature verification, event routing, idempotency handling, and the Webhooks API for programmatic subscription management.

This skill covers the full endpoint lifecycle in six steps: create a webhook subscription via the API, verify each request's signature, receive events in an Express handler, route them to per-topic handlers, deduplicate with Redis, and manage subscriptions. The high-level flow and the security-critical signature check live here; the complete step-by-step source is in [references/implementation.md](references/implementation.md) and worked scenarios are in [references/examples.md](references/examples.md).

## Prerequisites

- Klaviyo account with webhooks enabled
- HTTPS endpoint accessible from internet
- API key with scopes: `webhooks:read`, `webhooks:write`
- Redis or database for idempotency (recommended)

## Klaviyo Webhook Architecture

Klaviyo webhooks fire when specific **topics** occur in your account. Each webhook is signed with a **secret key** using HMAC-SHA256, sent in the `webhook-signature` header.

| Topic Category | Example Topics |
|---------------|---------------|
| Profile | `profile.created`, `profile.updated`, `profile.deleted` |
| List | `list.member.added`, `list.member.removed` |
| Segment | `segment.member.added`, `segment.member.removed` |
| Campaign | `campaign.sent`, `campaign.delivered` |
| Flow | `flow.triggered`, `flow.message.sent` |
| Event | Custom metric events |

## Instructions

Follow these six steps in order. Each is fully sourced in [references/implementation.md](references/implementation.md); the security-critical signature check is inlined below because getting it wrong is the most common failure.

1. **Create a webhook subscription** — call `webhooksApi.createWebhook` with the target `endpointUrl` and `webhookTopics`, then save the signing secret from the response as `KLAVIYO_WEBHOOK_SIGNING_SECRET`.
2. **Verify the signature** — recompute the HMAC-SHA256 over the **raw** request body and compare with a timing-safe check (skeleton below).
3. **Receive events** — mount an Express route with `express.raw({ type: 'application/json' })` so the raw body survives for verification; reject on a bad signature, then parse.
4. **Route by topic** — dispatch `event.type` to a per-topic handler map (`profile.created`, `campaign.sent`, ...).
5. **Deduplicate** — record each processed event ID in Redis with a TTL so Klaviyo retries are short-circuited.
6. **Manage subscriptions** — list, inspect topics, and delete webhooks via the API.

The signature-verification helper is the load-bearing piece — copy it exactly:

```typescript
// src/klaviyo/webhook-verify.ts
import crypto from 'crypto';

export function verifyWebhookSignature(
  rawBody: Buffer | string,
  signature: string,
  secret: string
): boolean {
  if (!signature || !secret) return false;

  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(typeof rawBody === 'string' ? rawBody : rawBody.toString())
    .digest('base64');

  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  } catch {
    return false;
  }
}
```

For the Express handler, event router, Redis idempotency layer, and subscription-management calls, see [references/implementation.md](references/implementation.md).

## Output

A working integration produces:

- **A registered webhook** — `createWebhook` returns a webhook ID and a signing secret; store the secret as `KLAVIYO_WEBHOOK_SIGNING_SECRET`.
- **HTTP responses from your endpoint** — `200 { received: true }` on success, `200 { status: 'already_processed' }` on a replayed event, `401 { error: 'Invalid signature' }` on a bad signature, and `500 { error: 'Processing failed' }` when a handler throws.
- **Side effects per topic** — e.g. a `profile.created` event upserts a row into your users table; a `campaign.sent` event emits an analytics track call.
- **Idempotency keys in Redis** — `klaviyo:webhook:<eventId>` entries with a 7-day TTL that prevent duplicate processing.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong signing secret | Verify secret matches webhook creation response |
| Duplicate events | No idempotency | Track event IDs in Redis/DB |
| Webhook timeout | Slow processing | Return 200 immediately, process async |
| Missing events | Wrong topics subscribed | Check webhook topic subscriptions |
| Body parse error | Using JSON body parser | Must use `express.raw()` for signature verification |

## Examples

Two worked scenarios and the local-testing loop are in [references/examples.md](references/examples.md):

- **Sync new profiles into your own database** — subscribe to `profile.created` / `profile.updated` and upsert each profile into your users table.
- **Track campaign sends into analytics** — subscribe to `campaign.sent` and forward each send to your analytics pipeline, with retries short-circuited by the idempotency layer.

Minimal local-testing loop:

```bash
npm run dev              # start your app on localhost:3000
ngrok http 3000          # expose it publicly
# register the ngrok URL as the webhook endpoint in Klaviyo,
# trigger an event, and watch your logs
```

## Resources

- [Webhooks API Overview](https://developers.klaviyo.com/en/reference/webhooks_api_overview)
- [Working with System Webhooks](https://developers.klaviyo.com/en/docs/working_with_system_webhooks)
- [Understanding Webhook Status Codes](https://developers.klaviyo.com/en/docs/understanding_webhook_status_codes)
- [Full implementation walkthrough](references/implementation.md) · [Worked examples](references/examples.md)
- For performance optimization, see the `klaviyo-performance-tuning` skill.
