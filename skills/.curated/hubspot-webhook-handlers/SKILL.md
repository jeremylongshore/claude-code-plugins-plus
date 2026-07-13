---
name: hubspot-webhook-handlers
description: |
  Build and harden HubSpot v3 webhook handlers that survive production: HMAC-SHA256
  signature verification, Redis SET NX deduplication, async batch processing with
  immediate 200 ACK, dead-letter queuing for permanent failures, and event-ordering
  guards for property-change streams. Use when implementing HubSpot webhooks for the
  first time, hardening an existing handler against retry storms or duplicate
  processing, debugging signature verification failures, or designing a reliable
  event pipeline for contact, company, or deal change events. Trigger with "hubspot
  webhook", "hubspot signature verification", "hubspot webhook dedup", "hubspot
  webhook retry storm", "hubspot event handler", "hubspot property change webhook",
  "hubspot list membership webhook", "hubspot dead letter queue".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Bash(python3:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - webhooks
  - event-driven
  - integration-engineering
---

# HubSpot Webhook Handlers

## Overview

Receive and process HubSpot webhook events reliably at production scale. This is not a walkthrough for getting your first event — it is the handler code your integration runs when HubSpot delivers 100 events in a single payload at 2am, when a misconfigured proxy silently strips your signature header, when a 3-day outage causes events to arrive in a burst after recovery, and when a rapid sequence of property updates arrives reversed because HubSpot sends in delivery order rather than chronological order.

The six production failures this skill prevents:

1. **Signature verification bypass** — skipping or misconfiguring the HMAC-SHA256 check on `X-HubSpot-Signature-v3` allows any party to send spoofed webhook payloads to your endpoint. One misconfigured load balancer or proxy that strips the `X-HubSpot-Signature-v3` header silently disables all security — your handler returns 200 to unauthenticated requests without knowing it.
2. **Duplicate delivery** — HubSpot retries unacknowledged webhooks (non-200 response or timeout) for up to 3 days with exponential backoff. If your handler crashes after processing but before responding, the same contact-update event creates duplicate CRM mutations downstream. Redis SET NX on the event ID is the reliable guard.
3. **No replay API — events are permanently lost after the 3-day retry window** — if your handler is down for more than 3 days, HubSpot drops those events permanently. There is no replay endpoint. Dead-letter queues and recovery runbooks are your only mitigation.
4. **Batch event explosion** — a single webhook delivery contains up to 100 events. Synchronous processing of all 100 within the HTTP request context times out (HubSpot timeout: 5 seconds) and returns 5xx, which triggers a retry storm. The correct pattern is to ACK immediately with 200, enqueue the batch, and process asynchronously.
5. **Property change ordering** — HubSpot sends `contact.propertyChange` events in delivery order, not chronological order. A fast property update followed by a slow one can arrive reversed: your handler sees the newer value first, then overwrites it with the older value. Sequence guards on `occurredAt` are required.
6. **List-membership scope mismatch** — subscribing to `contact.propertyChange` for `lifecyclestage` does not automatically deliver list-membership changes. Those require a separate subscription to the list-membership event type and a separate `oauth` scope or `crm.lists.read` scope on the app.

## Prerequisites

- Node.js 18+ (TypeScript examples) or Python 3.10+
- Express 4.x (or any HTTP server that can expose a raw body buffer for HMAC verification)
- Redis 6+ (for SET NX deduplication)
- A message queue: BullMQ (Redis-backed), RabbitMQ, or SQS (for async batch processing)
- HubSpot app client secret (Settings → App → Client Secret) — not the access token
- `HUBSPOT_CLIENT_SECRET` environment variable set in your runtime
- For list-membership events: `crm.lists.read` scope granted to your app

## Instructions

Build in this order. Each section neutralizes one production failure mode.

### 1. Signature verification (neutralizes spoofing and proxy bypass)

HubSpot v3 signatures use HMAC-SHA256 over the concatenation of your client secret, HTTP method, full request URI (including query string), raw request body, and the timestamp from `X-HubSpot-Request-Timestamp`. You must compute this over the **raw body bytes**, not a parsed JSON string. Any body middleware that re-serializes JSON will produce a signature mismatch.

The full algorithm:

```
HMAC-SHA256(
  clientSecret,
  httpMethod + requestUri + rawBody + timestamp
)
```

The resulting hex digest must match the value in `X-HubSpot-Signature-v3`.

Timestamp tolerance: reject any request where `abs(now - X-HubSpot-Request-Timestamp) > 300 seconds` (5 minutes). This prevents replay attacks.

```typescript
import { createHmac } from "crypto";
import type { Request, Response, NextFunction } from "express";

const SIGNATURE_TOLERANCE_MS = 5 * 60 * 1000; // 5 minutes

export function verifyHubSpotSignature(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const signature = req.headers["x-hubspot-signature-v3"] as string | undefined;
  const timestamp = req.headers["x-hubspot-request-timestamp"] as string | undefined;

  // Reject if either header is missing — do NOT silently pass
  if (!signature || !timestamp) {
    res.status(403).json({
      error: "missing_signature",
      detail: "X-HubSpot-Signature-v3 or X-HubSpot-Request-Timestamp header absent",
    });
    return;
  }

  // Reject stale requests — prevents replay attacks
  const requestAge = Math.abs(Date.now() - parseInt(timestamp, 10));
  if (requestAge > SIGNATURE_TOLERANCE_MS) {
    res.status(403).json({
      error: "timestamp_out_of_window",
      detail: `Request is ${Math.round(requestAge / 1000)}s old; max is 300s`,
    });
    return;
  }

  // Build the signature input string
  // rawBody must be set by express.raw() middleware — NOT express.json()
  const rawBody: Buffer = (req as any).rawBody;
  if (!rawBody) {
    console.error("rawBody not available — check express.raw() middleware ordering");
    res.status(500).json({ error: "misconfigured_middleware" });
    return;
  }

  const method = req.method.toUpperCase();
  // Full URI including query string
  const uri = `${req.protocol}://${req.get("host")}${req.originalUrl}`;
  const signingInput = `${method}${uri}${rawBody.toString("utf8")}${timestamp}`;

  const expected = createHmac("sha256", process.env.HUBSPOT_CLIENT_SECRET!)
    .update(signingInput, "utf8")
    .digest("hex");

  // Constant-time comparison to prevent timing attacks
  const receivedBuf = Buffer.from(signature, "hex");
  const expectedBuf = Buffer.from(expected, "hex");

  if (
    receivedBuf.length !== expectedBuf.length ||
    !crypto.timingSafeEqual(receivedBuf, expectedBuf)
  ) {
    console.warn("HubSpot signature mismatch", {
      expected: expected.slice(0, 8) + "...",
      received: signature.slice(0, 8) + "...",
      uri,
      timestamp,
    });
    res.status(403).json({ error: "invalid_signature" });
    return;
  }

  // Attach parsed body for the route handler
  (req as any).hubspotEvents = JSON.parse(rawBody.toString("utf8"));
  next();
}
```

**Critical: configure Express to capture the raw body.** Body middleware that calls `JSON.stringify(JSON.parse(...))` re-serializes the body and breaks signature verification:

```typescript
import express from "express";

const app = express();

// Use raw() for the webhook route ONLY — not json()
app.use(
  "/webhooks/hubspot",
  express.raw({ type: "application/json", limit: "1mb" }),
  (req, _res, next) => {
    // Preserve the raw buffer before any parsing
    (req as any).rawBody = req.body as Buffer;
    next();
  },
);
```

### 2. Redis SET NX deduplication (neutralizes duplicate delivery)

HubSpot guarantees at-least-once delivery. Every event object carries a unique `eventId`. Use Redis SET NX (set if not exists) with a 24-hour TTL as an idempotency gate. Process the event only if the SET NX succeeds; skip it if the key already exists.

```typescript
import type { Redis } from "ioredis";

const DEDUP_TTL_SECONDS = 86_400; // 24 hours — HubSpot retries for up to 3 days

async function isNewEvent(redis: Redis, eventId: number): Promise<boolean> {
  const key = `hubspot:event:${eventId}`;
  // SET key 1 EX 86400 NX — returns "OK" if set, null if already exists
  const result = await redis.set(key, "1", "EX", DEDUP_TTL_SECONDS, "NX");
  return result === "OK";
}

async function processEventIfNew(
  redis: Redis,
  event: HubSpotEvent,
  handler: (event: HubSpotEvent) => Promise<void>,
): Promise<void> {
  const isNew = await isNewEvent(redis, event.eventId);
  if (!isNew) {
    console.debug("Skipping duplicate event", { eventId: event.eventId, type: event.subscriptionType });
    return;
  }

  try {
    await handler(event);
  } catch (err) {
    // If processing fails, delete the dedup key so retries can reprocess
    // Only do this for transient failures — not for permanent business errors
    await redis.del(`hubspot:event:${event.eventId}`);
    throw err;
  }
}
```

### 3. Immediate ACK with async batch processing (neutralizes retry storms)

HubSpot expects a 200 response within 5 seconds. For a batch of 100 events, synchronous processing will exceed this window under any real load. The correct pattern is to return 200 immediately, enqueue the batch, and process in a background worker.

```typescript
import { Queue } from "bullmq";
import type { Request, Response } from "express";

const eventQueue = new Queue("hubspot-events", {
  connection: { host: process.env.REDIS_HOST, port: parseInt(process.env.REDIS_PORT ?? "6379") },
  defaultJobOptions: {
    attempts: 5,
    backoff: { type: "exponential", delay: 2_000 },
    removeOnComplete: { count: 1000 },
    removeOnFail: false, // keep failed jobs for DLQ inspection
  },
});

export async function webhookHandler(req: Request, res: Response): Promise<void> {
  const events: HubSpotEvent[] = (req as any).hubspotEvents;

  if (!Array.isArray(events) || events.length === 0) {
    res.status(200).json({ accepted: 0 });
    return;
  }

  // ACK immediately — do NOT await processing
  res.status(200).json({ accepted: events.length });

  // Enqueue each event as an individual job
  // Individual jobs allow per-event retry, dedup, and DLQ routing
  await Promise.all(
    events.map((event) =>
      eventQueue.add(event.subscriptionType, event, {
        jobId: `hubspot-${event.eventId}`, // deduplicate at queue level too
      }),
    ),
  );
}
```

### 4. Dead-letter queue for permanent failures (neutralizes silent event loss)

Events that exhaust all retry attempts must land in a dead-letter structure where they can be inspected, replayed, or alerted on. BullMQ's failed job store provides this out of the box, but you need explicit monitoring.

```typescript
import { Worker, type Job } from "bullmq";

// Dead-letter handler — called when a job exhausts all attempts
async function onJobFailed(job: Job | undefined, err: Error): Promise<void> {
  if (!job) return;
  if (job.attemptsMade < (job.opts.attempts ?? 1)) return; // still has retries remaining

  // This job is permanently dead — route to DLQ
  const dlqKey = `hubspot:dlq:${job.name}`;
  await redis.lpush(
    dlqKey,
    JSON.stringify({
      jobId: job.id,
      eventId: job.data.eventId,
      portalId: job.data.portalId,
      objectId: job.data.objectId,
      subscriptionType: job.data.subscriptionType,
      occurredAt: job.data.occurredAt,
      failedAt: Date.now(),
      error: err.message,
      attempts: job.attemptsMade,
    }),
  );

  // Alert — use your notification channel
  console.error("HubSpot event permanently failed", {
    jobId: job.id,
    eventId: job.data.eventId,
    type: job.data.subscriptionType,
    error: err.message,
  });
}

const worker = new Worker(
  "hubspot-events",
  async (job) => {
    await processEventIfNew(redis, job.data, routeEvent);
  },
  {
    connection: { host: process.env.REDIS_HOST, port: parseInt(process.env.REDIS_PORT ?? "6379") },
    concurrency: 10, // process up to 10 events in parallel
  },
);

worker.on("failed", onJobFailed);
```

**DLQ replay pattern** — when your handler is recovered and you need to reprocess failed events:

```typescript
async function replayDeadLetterQueue(
  redis: Redis,
  subscriptionType: string,
  limit = 100,
): Promise<number> {
  const dlqKey = `hubspot:dlq:${subscriptionType}`;
  let replayed = 0;

  for (let i = 0; i < limit; i++) {
    const raw = await redis.rpop(dlqKey);
    if (!raw) break;

    const dead = JSON.parse(raw) as { eventId: number; [key: string]: unknown };

    // Delete the dedup key so the replayed event is treated as new
    await redis.del(`hubspot:event:${dead.eventId}`);

    await eventQueue.add(subscriptionType, dead, {
      jobId: `hubspot-replay-${dead.eventId}-${Date.now()}`,
    });

    replayed++;
  }

  console.info(`Replayed ${replayed} dead-letter events for ${subscriptionType}`);
  return replayed;
}
```

### 5. Property change ordering guard (neutralizes reversed updates)

HubSpot delivers `contact.propertyChange` events in delivery order, not chronological order. When a contact's property changes twice in rapid succession, the second change can arrive before the first. If you apply them in delivery order, you overwrite a newer value with an older one.

Guard every write operation with an `occurredAt` comparison:

```typescript
type PropertyVersion = { value: string; occurredAt: number };

async function applyPropertyChange(
  redis: Redis,
  objectId: number,
  propertyName: string,
  newValue: string,
  occurredAt: number,
): Promise<void> {
  const versionKey = `hubspot:prop:${objectId}:${propertyName}`;

  // Read the last-applied version
  const existingRaw = await redis.get(versionKey);
  const existing: PropertyVersion | null = existingRaw ? JSON.parse(existingRaw) : null;

  if (existing && existing.occurredAt >= occurredAt) {
    console.debug("Ignoring stale property change", {
      objectId,
      propertyName,
      existingTimestamp: existing.occurredAt,
      incomingTimestamp: occurredAt,
    });
    return;
  }

  // Safe to apply — this is the newest value seen for this property
  await redis.set(
    versionKey,
    JSON.stringify({ value: newValue, occurredAt }),
    "EX",
    7 * 86_400, // 7-day TTL — keep long enough to guard burst redeliveries
  );

  // Now apply the change to your downstream system
  await updateContactProperty(objectId, propertyName, newValue);
}
```

### 6. List-membership subscription (neutralizes scope mismatch)

`contact.propertyChange` for `lifecyclestage` does NOT deliver list-membership changes. These require a separate subscription. Use the webhook subscription API to register:

```bash
# Register a contact.propertyChange subscription
curl -X POST "https://api.hubapi.com/webhooks/v3/{appId}/subscriptions" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "contact.propertyChange",
    "propertyName": "lifecyclestage",
    "active": true
  }'

# Register a list-membership subscription (separate subscription required)
# Note: HubSpot does not expose a direct list.membershipChange event type.
# Use contact.propertyChange for hs_all_contact_vids or workflow enrollment events,
# or poll GET /crm/v3/lists/{listId}/memberships for list-driven automation.
```

Verify active subscriptions before debugging delivery:

```bash
curl -s "https://api.hubapi.com/webhooks/v3/{appId}/subscriptions" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" | jq '.results[] | {id, eventType, propertyName, active}'
```

## Error Handling

| HTTP Status | Error | Root Cause | Action |
|---|---|---|---|
| `403 FORBIDDEN` | `missing_signature` | `X-HubSpot-Signature-v3` or `X-HubSpot-Request-Timestamp` header absent | Check proxy/load balancer header passthrough; add header logging at the edge |
| `403 FORBIDDEN` | `invalid_signature` | HMAC digest does not match; raw body was re-serialized | Verify `express.raw()` middleware is used (not `express.json()`); confirm `HUBSPOT_CLIENT_SECRET` is the app client secret, not the access token |
| `403 FORBIDDEN` | `timestamp_out_of_window` | Request timestamp is >5 minutes from server time | Check server NTP sync; clock skew on container or serverless host |
| `500 INTERNAL_SERVER_ERROR` | `misconfigured_middleware` | `rawBody` buffer not attached to request | `express.raw()` must run before signature middleware on the webhook route |
| `200 OK` (but no events processed) | Duplicate suppressed | Redis SET NX returned null; event already processed | Expected — dedup is working |
| `200 OK` (but DLQ growing) | Permanent processing failure | Downstream system error; event exhausted retries | Inspect DLQ via `redis LRANGE hubspot:dlq:<type> 0 -1`; fix downstream, then replay |
| `429 TOO_MANY_REQUESTS` | Rate limit on subscription API | Too many subscription management calls | Back off; subscription changes are rare — cache the subscription list |
| No delivery received | Subscription inactive or app not installed | `active: false` on subscription or app revoked by portal admin | Run `GET /webhooks/v3/{appId}/subscriptions` and verify `active: true` |

## Examples

### Minimal end-to-end wiring (Express)

```typescript
import express from "express";
import { createClient } from "ioredis";
import { verifyHubSpotSignature } from "./middleware/signature";
import { webhookHandler } from "./handlers/webhook";

const app = express();
const redis = createClient({ host: process.env.REDIS_HOST });

// IMPORTANT: raw body capture before JSON parsing
app.use(
  "/webhooks/hubspot",
  express.raw({ type: "application/json", limit: "1mb" }),
  (req, _res, next) => {
    (req as any).rawBody = req.body as Buffer;
    next();
  },
  verifyHubSpotSignature,
  webhookHandler,
);

app.listen(3000, () => console.log("Webhook listener on :3000"));
```

### Test signature verification locally

```bash
# Compute the expected signature for a test payload
CLIENT_SECRET="your-client-secret"
METHOD="POST"
URI="https://your-host.example.com/webhooks/hubspot"
BODY='[{"eventId":1,"subscriptionType":"contact.propertyChange"}]'
TIMESTAMP="$(date +%s%3N)"  # milliseconds

EXPECTED=$(echo -n "${METHOD}${URI}${BODY}${TIMESTAMP}" | \
  openssl dgst -sha256 -hmac "$CLIENT_SECRET" | awk '{print $2}')

curl -X POST "$URI" \
  -H "Content-Type: application/json" \
  -H "X-HubSpot-Signature-v3: $EXPECTED" \
  -H "X-HubSpot-Request-Timestamp: $TIMESTAMP" \
  -d "$BODY"
```

### Inspect the dead-letter queue

```bash
# View all entries in the DLQ for contact.propertyChange
redis-cli LRANGE hubspot:dlq:contact.propertyChange 0 -1 | python3 -m json.tool

# Count DLQ depth per event type
redis-cli KEYS "hubspot:dlq:*" | xargs -I{} sh -c 'echo "{}: $(redis-cli LLEN {})"'

# Replay up to 50 failed contact.deletion events
node -e "
const { replayDeadLetterQueue } = require('./dist/dlq');
replayDeadLetterQueue(redis, 'contact.deletion', 50).then(console.log);
"
```

### Register subscriptions for all CRM object types

```bash
APP_ID="your-app-id"
TOKEN="$HUBSPOT_ACCESS_TOKEN"
BASE="https://api.hubapi.com/webhooks/v3/$APP_ID/subscriptions"

for EVENT_TYPE in contact.creation contact.deletion contact.propertyChange \
                  contact.merge company.creation deal.creation deal.propertyChange; do
  curl -s -X POST "$BASE" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"eventType\": \"$EVENT_TYPE\", \"active\": true}" | jq '{id, eventType, active}'
done
```

## Output

- Express webhook handler with `express.raw()` body capture and HMAC-SHA256 signature verification
- Redis SET NX deduplication on `eventId` with 24-hour TTL
- Immediate 200 ACK with async BullMQ batch enqueue
- Dead-letter queue with `redis.lpush` for exhausted retries and a replay function
- `occurredAt` ordering guard for `contact.propertyChange` events
- Subscription registration curl commands for all CRM event types
- Middleware ordering that prevents the re-serialization signature mismatch

## Resources

- [HubSpot Webhooks Overview](https://developers.hubspot.com/docs/guides/apps/webhooks/overview)
- [Webhooks v3 API Reference](https://developers.hubspot.com/docs/reference/api/app-management/webhooks)
- [Signature Verification Guide](https://developers.hubspot.com/docs/guides/apps/webhooks/validating-requests)
- [Webhook Event Types](https://developers.hubspot.com/docs/guides/apps/webhooks/event-types)
- [BullMQ Documentation](https://docs.bullmq.io/)
- [ioredis SET NX](https://redis.io/commands/set/)
- [API_REFERENCE.md](references/API_REFERENCE.md) — signature algorithm steps, event payload shapes, subscription endpoint, retry behavior spec
- [implementation-guide.md](references/implementation-guide.md) — complete Express handler, Redis dedup, BullMQ worker, DLQ pattern, ordering guard, Python equivalent
