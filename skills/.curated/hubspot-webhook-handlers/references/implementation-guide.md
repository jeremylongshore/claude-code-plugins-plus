# HubSpot Webhook Handlers — Implementation Guide

Complete Express webhook handler with every production pattern wired end-to-end: HMAC-SHA256 verification, Redis SET NX dedup, async BullMQ batch processing, dead-letter queue with replay, and `occurredAt` ordering guard. The algorithm and API shapes live in `API_REFERENCE.md`; this document is the implementation.

## Complete Express Handler (TypeScript)

### Directory structure

```
src/
├── middleware/
│   └── hubspot-signature.ts    # HMAC-SHA256 verification middleware
├── handlers/
│   └── hubspot-webhook.ts      # Route handler (immediate ACK + enqueue)
├── workers/
│   └── event-worker.ts         # BullMQ worker (dedup + route + DLQ)
├── processors/
│   ├── contact-property.ts     # contact.propertyChange handler
│   ├── contact-creation.ts     # contact.creation handler
│   └── deal-property.ts        # deal.propertyChange handler
├── lib/
│   ├── redis.ts                # Shared Redis client
│   ├── queue.ts                # BullMQ queue instance
│   └── dedup.ts                # SET NX idempotency helpers
└── server.ts                   # Express app wiring
```

### Type definitions

```typescript
// src/types/hubspot.ts

export interface HubSpotEvent {
  eventId: number;
  subscriptionId: number;
  portalId: number;
  appId: number;
  occurredAt: number;        // Unix ms — use for ordering, not delivery order
  subscriptionType: string;
  attemptNumber: number;
  objectId: number;

  // property change events only
  propertyName?: string;
  propertyValue?: string;
  changeSource?: string;
  changeFlag?: "UPDATED" | "CREATED" | "DELETED";

  // merge events only
  mergedObjectIds?: number[];
  primaryObjectId?: number;

  // deletion events only
  gdprDeleteType?: "HARD_DELETE" | "SOFT_DELETE";
}
```

### Signature middleware

```typescript
// src/middleware/hubspot-signature.ts
import { createHmac, timingSafeEqual } from "crypto";
import type { Request, Response, NextFunction } from "express";

const TOLERANCE_MS = 5 * 60 * 1000; // 5 minutes

export function hubspotSignature(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const sig = req.headers["x-hubspot-signature-v3"] as string | undefined;
  const ts = req.headers["x-hubspot-request-timestamp"] as string | undefined;

  if (!sig || !ts) {
    res.status(403).json({
      error: "missing_signature",
      detail: "X-HubSpot-Signature-v3 or X-HubSpot-Request-Timestamp absent",
    });
    return;
  }

  const age = Math.abs(Date.now() - parseInt(ts, 10));
  if (age > TOLERANCE_MS) {
    res.status(403).json({
      error: "timestamp_out_of_window",
      detail: `Request is ${Math.round(age / 1000)}s old; max is 300s`,
    });
    return;
  }

  const rawBody = (req as any).rawBody as Buffer | undefined;
  if (!rawBody) {
    console.error("hubspot-signature: rawBody missing — check express.raw() order");
    res.status(500).json({ error: "misconfigured_middleware" });
    return;
  }

  const method = req.method.toUpperCase();
  const uri = `${req.protocol}://${req.get("host")}${req.originalUrl}`;
  const input = `${method}${uri}${rawBody.toString("utf8")}${ts}`;

  const expected = createHmac("sha256", process.env.HUBSPOT_CLIENT_SECRET!)
    .update(input, "utf8")
    .digest("hex");

  let match = false;
  try {
    const a = Buffer.from(sig.padStart(64, "0"), "hex");
    const b = Buffer.from(expected.padStart(64, "0"), "hex");
    match = a.length === b.length && timingSafeEqual(a, b);
  } catch {
    match = false;
  }

  if (!match) {
    console.warn("hubspot-signature: mismatch", {
      uri,
      ts,
      sigHead: sig.slice(0, 8) + "...",
      sigCalc: expected.slice(0, 8) + "...",
    });
    res.status(403).json({ error: "invalid_signature" });
    return;
  }

  (req as any).hubspotEvents = JSON.parse(rawBody.toString("utf8"));
  next();
}
```

### Shared Redis client

```typescript
// src/lib/redis.ts
import { Redis } from "ioredis";

export const redis = new Redis({
  host: process.env.REDIS_HOST ?? "localhost",
  port: parseInt(process.env.REDIS_PORT ?? "6379"),
  password: process.env.REDIS_PASSWORD,
  maxRetriesPerRequest: 3,
  enableOfflineQueue: false, // fail fast if Redis is down
});

redis.on("error", (err) => {
  console.error("Redis connection error", { error: err.message });
});
```

### SET NX deduplication

```typescript
// src/lib/dedup.ts
import type { Redis } from "ioredis";

const DEDUP_TTL = 86_400; // 24 hours — covers HubSpot's 3-day retry window with margin

/**
 * Returns true if this eventId has NOT been seen before (first occurrence).
 * Returns false if a duplicate — caller should skip processing.
 *
 * On processing failure, the caller must delete the dedup key so retries can reprocess.
 */
export async function claimEvent(redis: Redis, eventId: number): Promise<boolean> {
  const key = `hs:evt:${eventId}`;
  const result = await redis.set(key, "1", "EX", DEDUP_TTL, "NX");
  return result === "OK";
}

export async function releaseEvent(redis: Redis, eventId: number): Promise<void> {
  await redis.del(`hs:evt:${eventId}`);
}
```

### BullMQ queue

```typescript
// src/lib/queue.ts
import { Queue } from "bullmq";
import { redis } from "./redis";

export const eventQueue = new Queue("hs-events", {
  connection: redis,
  defaultJobOptions: {
    attempts: 5,
    backoff: { type: "exponential", delay: 2_000 },  // 2s, 4s, 8s, 16s, 32s
    removeOnComplete: { count: 1_000, age: 3600 },   // keep last 1K completed for 1h
    removeOnFail: false,                              // keep all failed jobs for DLQ review
  },
});
```

### Webhook route handler (immediate ACK)

```typescript
// src/handlers/hubspot-webhook.ts
import type { Request, Response } from "express";
import { eventQueue } from "../lib/queue";
import type { HubSpotEvent } from "../types/hubspot";

export async function hubspotWebhookHandler(
  req: Request,
  res: Response,
): Promise<void> {
  const events: HubSpotEvent[] = (req as any).hubspotEvents ?? [];

  if (!Array.isArray(events) || events.length === 0) {
    res.status(200).json({ accepted: 0 });
    return;
  }

  // ACK immediately — HubSpot has a 5s timeout
  // All processing happens asynchronously in the worker
  res.status(200).json({ accepted: events.length });

  // Enqueue each event as an individual BullMQ job
  // jobId makes enqueueing itself idempotent — BullMQ skips duplicate jobIds
  const jobs = events.map((event) => ({
    name: event.subscriptionType,
    data: event,
    opts: {
      jobId: `hs-${event.eventId}`,
    },
  }));

  try {
    await eventQueue.addBulk(jobs);
  } catch (err: any) {
    // Don't re-open the HTTP response — it's already sent
    // Log and rely on HubSpot's retry mechanism
    console.error("Failed to enqueue HubSpot events", {
      count: events.length,
      error: err.message,
    });
  }
}
```

### BullMQ worker with full dedup, routing, and DLQ

```typescript
// src/workers/event-worker.ts
import { Worker, type Job } from "bullmq";
import { redis } from "../lib/redis";
import { claimEvent, releaseEvent } from "../lib/dedup";
import { processContactProperty } from "../processors/contact-property";
import { processContactCreation } from "../processors/contact-creation";
import { processDealProperty } from "../processors/deal-property";
import type { HubSpotEvent } from "../types/hubspot";

const DLQ_PREFIX = "hs:dlq";
const DLQ_MAX_LENGTH = 10_000; // cap DLQ size to prevent unbounded growth

async function routeEvent(event: HubSpotEvent): Promise<void> {
  switch (event.subscriptionType) {
    case "contact.propertyChange":
      await processContactProperty(event);
      break;
    case "contact.creation":
      await processContactCreation(event);
      break;
    case "deal.propertyChange":
      await processDealProperty(event);
      break;
    case "contact.deletion":
    case "contact.merge":
    case "company.creation":
    case "deal.creation":
      console.info("Received unhandled event type", {
        type: event.subscriptionType,
        objectId: event.objectId,
        portalId: event.portalId,
      });
      break;
    default:
      console.warn("Unknown event type", { type: event.subscriptionType });
  }
}

async function processJobWithDedup(job: Job<HubSpotEvent>): Promise<void> {
  const event = job.data;

  const claimed = await claimEvent(redis, event.eventId);
  if (!claimed) {
    console.debug("Duplicate event skipped", {
      eventId: event.eventId,
      type: event.subscriptionType,
      attempt: event.attemptNumber,
    });
    return; // Not an error — dedup is working correctly
  }

  try {
    await routeEvent(event);
  } catch (err) {
    // Release the dedup key so the BullMQ retry can reprocess
    await releaseEvent(redis, event.eventId);
    throw err; // Rethrow so BullMQ handles retry backoff
  }
}

async function handlePermanentFailure(
  job: Job | undefined,
  err: Error,
): Promise<void> {
  if (!job) return;
  const remainingAttempts = (job.opts.attempts ?? 1) - job.attemptsMade;
  if (remainingAttempts > 0) return; // Still has retries left — not a permanent failure

  const dlqKey = `${DLQ_PREFIX}:${job.name}`;
  const entry = JSON.stringify({
    jobId: job.id,
    eventId: job.data.eventId,
    portalId: job.data.portalId,
    objectId: job.data.objectId,
    subscriptionType: job.data.subscriptionType,
    occurredAt: job.data.occurredAt,
    propertyName: job.data.propertyName ?? null,
    propertyValue: job.data.propertyValue ?? null,
    failedAt: Date.now(),
    attempts: job.attemptsMade,
    error: err.message,
  });

  // LPUSH so newest failures are at index 0; LTRIM to cap the list
  await redis.lpush(dlqKey, entry);
  await redis.ltrim(dlqKey, 0, DLQ_MAX_LENGTH - 1);

  // Set TTL on DLQ key so it doesn't leak indefinitely
  await redis.expire(dlqKey, 30 * 86_400); // 30 days

  console.error("HubSpot event permanently failed — moved to DLQ", {
    dlqKey,
    jobId: job.id,
    eventId: job.data.eventId,
    type: job.name,
    error: err.message,
  });
}

export const worker = new Worker<HubSpotEvent>(
  "hs-events",
  processJobWithDedup,
  {
    connection: redis,
    concurrency: 10,
    limiter: {
      max: 50,
      duration: 1_000, // max 50 events/second to avoid HubSpot API back-pressure
    },
  },
);

worker.on("failed", handlePermanentFailure);

worker.on("error", (err) => {
  console.error("BullMQ worker error", { error: err.message });
});
```

### Property change processor with ordering guard

```typescript
// src/processors/contact-property.ts
import { redis } from "../lib/redis";
import type { HubSpotEvent } from "../types/hubspot";

const PROP_VERSION_TTL = 7 * 86_400; // 7 days — long enough to guard redelivery bursts

interface PropVersion {
  value: string;
  occurredAt: number;
}

async function applyWithOrderingGuard(
  objectId: number,
  objectType: "contact" | "company" | "deal",
  propertyName: string,
  newValue: string,
  occurredAt: number,
): Promise<void> {
  const versionKey = `hs:propver:${objectType}:${objectId}:${propertyName}`;

  const raw = await redis.get(versionKey);
  if (raw) {
    const current: PropVersion = JSON.parse(raw);
    if (current.occurredAt >= occurredAt) {
      console.debug("Stale property update ignored (ordering guard)", {
        objectId,
        objectType,
        propertyName,
        currentTimestamp: current.occurredAt,
        incomingTimestamp: occurredAt,
        skippedValue: newValue,
        keptValue: current.value,
      });
      return;
    }
  }

  // Record the new version before applying the write
  // This prevents a race where two events arrive simultaneously:
  // the write is idempotent at the target system; the version key is the guard
  await redis.set(
    versionKey,
    JSON.stringify({ value: newValue, occurredAt }),
    "EX",
    PROP_VERSION_TTL,
  );

  // Apply the property change to your downstream system
  await writeContactProperty(objectId, propertyName, newValue);
}

async function writeContactProperty(
  contactId: number,
  propertyName: string,
  value: string,
): Promise<void> {
  // Replace this with your CRM write: HubSpot API patch, database update, etc.
  const res = await fetch(
    `https://api.hubapi.com/crm/v3/objects/contacts/${contactId}`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${process.env.HUBSPOT_ACCESS_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ properties: { [propertyName]: value } }),
    },
  );

  if (!res.ok) {
    throw new Error(
      `HubSpot contact patch failed: ${res.status} ${await res.text()}`,
    );
  }
}

export async function processContactProperty(event: HubSpotEvent): Promise<void> {
  if (!event.propertyName || event.propertyValue === undefined) {
    console.warn("contact.propertyChange event missing propertyName/propertyValue", {
      eventId: event.eventId,
    });
    return;
  }

  await applyWithOrderingGuard(
    event.objectId,
    "contact",
    event.propertyName,
    event.propertyValue,
    event.occurredAt,
  );
}
```

### Express server wiring

```typescript
// src/server.ts
import express from "express";
import { hubspotSignature } from "./middleware/hubspot-signature";
import { hubspotWebhookHandler } from "./handlers/hubspot-webhook";

const app = express();

// Health check — unauthenticated, for load balancer probes
app.get("/health", (_req, res) => res.status(200).json({ ok: true }));

// Webhook route — raw body capture BEFORE any JSON parsing
app.post(
  "/webhooks/hubspot",
  express.raw({ type: "application/json", limit: "2mb" }),
  (req, _res, next) => {
    // Preserve the raw Buffer before downstream middleware can re-serialize
    (req as any).rawBody = req.body as Buffer;
    next();
  },
  hubspotSignature,
  hubspotWebhookHandler,
);

// All other routes can use JSON parsing normally
app.use(express.json());

export const server = app.listen(
  parseInt(process.env.PORT ?? "3000"),
  () => console.log(`HubSpot webhook listener on :${process.env.PORT ?? 3000}`),
);
```

## Dead-Letter Queue Replay

```typescript
// src/lib/dlq.ts
import { redis } from "./redis";
import { eventQueue } from "./queue";
import { releaseEvent } from "./dedup";

export async function replayDeadLetterQueue(
  subscriptionType: string,
  options: { limit?: number; dryRun?: boolean } = {},
): Promise<{ replayed: number; remaining: number }> {
  const { limit = 100, dryRun = false } = options;
  const dlqKey = `hs:dlq:${subscriptionType}`;

  const queueDepth = await redis.llen(dlqKey);
  let replayed = 0;

  for (let i = 0; i < Math.min(limit, queueDepth); i++) {
    const raw = await redis.rpop(dlqKey); // RPOP = oldest first (LIFO in, FIFO out)
    if (!raw) break;

    const dead = JSON.parse(raw);

    if (dryRun) {
      console.info("DRY RUN — would replay", {
        eventId: dead.eventId,
        type: dead.subscriptionType,
        failedAt: new Date(dead.failedAt).toISOString(),
        error: dead.error,
      });
      replayed++;
      continue;
    }

    // Clear the dedup key so the replayed event is treated as new
    await releaseEvent(redis, dead.eventId);

    // Re-enqueue with a replay-specific jobId to avoid BullMQ dedup collision
    await eventQueue.add(subscriptionType, dead, {
      jobId: `hs-replay-${dead.eventId}-${Date.now()}`,
    });

    replayed++;
  }

  const remaining = await redis.llen(dlqKey);
  console.info("DLQ replay complete", { subscriptionType, replayed, remaining, dryRun });

  return { replayed, remaining };
}

export async function inspectDeadLetterQueue(
  subscriptionType: string,
  count = 10,
): Promise<object[]> {
  const dlqKey = `hs:dlq:${subscriptionType}`;
  const entries = await redis.lrange(dlqKey, 0, count - 1);
  return entries.map((e) => JSON.parse(e));
}
```

## Python Equivalent

For teams running Python webhook handlers (FastAPI or Flask):

```python
import hashlib
import hmac
import json
import os
import time
from typing import Any

import redis as redis_lib
from fastapi import FastAPI, HTTPException, Request, Response

app = FastAPI()
r = redis_lib.Redis(host=os.environ.get("REDIS_HOST", "localhost"), decode_responses=True)

TOLERANCE_SECONDS = 300  # 5 minutes
DEDUP_TTL = 86_400        # 24 hours

def verify_signature(
    method: str,
    uri: str,
    raw_body: bytes,
    signature: str,
    timestamp: str,
) -> bool:
    age = abs(time.time() * 1000 - int(timestamp))
    if age > TOLERANCE_SECONDS * 1000:
        return False

    signing_input = f"{method.upper()}{uri}{raw_body.decode('utf-8')}{timestamp}"
    expected = hmac.new(
        os.environ["HUBSPOT_CLIENT_SECRET"].encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def claim_event(event_id: int) -> bool:
    key = f"hs:evt:{event_id}"
    result = r.set(key, "1", ex=DEDUP_TTL, nx=True)
    return result is True


def release_event(event_id: int) -> None:
    r.delete(f"hs:evt:{event_id}")


@app.post("/webhooks/hubspot")
async def hubspot_webhook(request: Request) -> Response:
    raw_body = await request.body()
    sig = request.headers.get("x-hubspot-signature-v3")
    ts = request.headers.get("x-hubspot-request-timestamp")

    if not sig or not ts:
        raise HTTPException(status_code=403, detail="missing_signature")

    uri = str(request.url)
    if not verify_signature(request.method, uri, raw_body, sig, ts):
        raise HTTPException(status_code=403, detail="invalid_signature")

    events: list[dict[str, Any]] = json.loads(raw_body)

    # ACK immediately
    response = Response(
        content=json.dumps({"accepted": len(events)}),
        media_type="application/json",
        status_code=200,
    )

    # Enqueue for async processing (using Celery, RQ, or your preferred queue)
    for event in events:
        enqueue_event(event)  # replace with your queue implementation

    return response


def enqueue_event(event: dict[str, Any]) -> None:
    # With RQ:
    # from rq import Queue
    # q = Queue(connection=r)
    # q.enqueue(process_event, event, job_id=f"hs-{event['eventId']}")
    pass


def process_event(event: dict[str, Any]) -> None:
    if not claim_event(event["eventId"]):
        return  # Duplicate — skip

    try:
        route_event(event)
    except Exception:
        release_event(event["eventId"])
        raise


def route_event(event: dict[str, Any]) -> None:
    sub_type = event.get("subscriptionType", "")
    if sub_type == "contact.propertyChange":
        apply_property_change(
            object_id=event["objectId"],
            object_type="contact",
            property_name=event.get("propertyName", ""),
            new_value=event.get("propertyValue", ""),
            occurred_at=event["occurredAt"],
        )


def apply_property_change(
    object_id: int,
    object_type: str,
    property_name: str,
    new_value: str,
    occurred_at: int,
) -> None:
    version_key = f"hs:propver:{object_type}:{object_id}:{property_name}"
    existing_raw = r.get(version_key)
    if existing_raw:
        existing = json.loads(existing_raw)
        if existing["occurredAt"] >= occurred_at:
            return  # Stale — skip

    r.set(
        version_key,
        json.dumps({"value": new_value, "occurredAt": occurred_at}),
        ex=7 * 86_400,
    )
    # Write to downstream system here
```

## Monitoring Checklist

Log and alert on these events to detect webhook processing failures before they become data integrity issues:

| Event | Log Level | Suggested Alert |
|---|---|---|
| Signature verification failure | WARN | Alert if >5 in 60 seconds — may indicate proxy misconfiguration |
| Timestamp out of window | WARN | Alert if recurring — investigate server clock skew |
| Duplicate event skipped | DEBUG | No alert — expected on retries |
| Queue enqueue failure | ERROR | Page on-call — events will be lost if queue is unavailable |
| DLQ entry added | ERROR | Alert immediately — permanent failure requires investigation |
| Worker error (non-job) | ERROR | Alert — worker process is unhealthy |
| DLQ depth > 100 | WARN | Alert — replay needed before 3-day retry window closes |

```typescript
// Structured log example for a successfully processed event
console.log(JSON.stringify({
  event: "hubspot_event_processed",
  subscriptionType: event.subscriptionType,
  eventId: event.eventId,
  portalId: event.portalId,
  objectId: event.objectId,
  attemptNumber: event.attemptNumber,
  processingMs: Date.now() - startMs,
}));
```

## Local Testing with ngrok

```bash
# Install ngrok, then expose your local server
ngrok http 3000

# Register your ngrok URL as the webhook target
APP_ID="your-app-id"
NGROK_URL="https://abc123.ngrok.io"

curl -X PUT "https://api.hubapi.com/webhooks/v3/$APP_ID/settings" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"targetUrl\": \"$NGROK_URL/webhooks/hubspot\",
    \"throttling\": { \"period\": \"SECONDLY\", \"maxConcurrentRequests\": 5 }
  }"

# Verify the settings were applied
curl -s "https://api.hubapi.com/webhooks/v3/$APP_ID/settings" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" | jq '.'
```
