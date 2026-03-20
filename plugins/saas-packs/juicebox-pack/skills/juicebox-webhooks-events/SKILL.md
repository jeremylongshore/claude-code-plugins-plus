---
name: juicebox-webhooks-events
description: |
  Implement Juicebox webhook handling.
  Use when setting up event notifications, processing webhooks,
  or integrating real-time updates from Juicebox.
  Trigger with phrases like "juicebox webhooks", "juicebox events",
  "juicebox notifications", "juicebox real-time".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Webhooks & Events

## Overview

Register and handle webhooks from Juicebox's PeopleGPT platform. Juicebox fires events when candidate searches complete, profiles are enriched, AI recruiting agents find matches, and bulk exports finish. Your endpoint must verify HMAC-SHA256 signatures, respond 200 immediately, and process events asynchronously with idempotent delivery-ID tracking.

## Prerequisites

- Juicebox account with API access (token-based auth: `Authorization: token {username}:{api_token}`)
- HTTPS endpoint accessible from the internet (or ngrok for local dev)
- Node.js 18+ with Express
- Redis for delivery-ID deduplication (optional but recommended)

## Event Types

| Event | Trigger | Payload Fields |
|-------|---------|----------------|
| `candidate.enriched` | Profile enrichment completes | `profileId`, `fields[]`, `source` |
| `search.completed` | PeopleGPT search finishes | `searchId`, `resultCount`, `query` |
| `agent.match` | AI recruiting agent finds a candidate match | `agentId`, `candidateId`, `matchScore`, `jobId` |
| `export.ready` | Bulk export file is available | `exportId`, `downloadUrl`, `recordCount`, `expiresAt` |

## Instructions

### Step 1: Register Webhook Endpoint via API

```bash
curl -X POST https://api.juicebox.ai/v1/webhooks \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/juicebox",
    "events": ["candidate.enriched", "search.completed", "agent.match", "export.ready"],
    "secret": "whsec_your_signing_secret_here"
  }'
```

Save the returned `webhook_id` and store `whsec_your_signing_secret_here` in your environment as `JUICEBOX_WEBHOOK_SECRET`.

### Step 2: Implement Signature Verification

```typescript
// lib/juicebox-webhook.ts
import crypto from "crypto";

export function verifyJuiceboxSignature(
  rawBody: Buffer,
  signatureHeader: string,
  secret: string
): boolean {
  const expected = crypto
    .createHmac("sha256", secret)
    .update(rawBody)
    .digest("hex");

  const provided = signatureHeader.replace("sha256=", "");

  return crypto.timingSafeEqual(
    Buffer.from(expected, "hex"),
    Buffer.from(provided, "hex")
  );
}
```

### Step 3: Build Event Router with Typed Handlers

```typescript
// routes/juicebox-webhooks.ts
import { Router, raw } from "express";
import { verifyJuiceboxSignature } from "../lib/juicebox-webhook";

interface JuiceboxEvent {
  id: string;           // delivery ID for idempotency
  type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

type EventHandler = (data: Record<string, unknown>) => Promise<void>;

const handlers: Record<string, EventHandler> = {
  "candidate.enriched": async (data) => {
    const { profileId, fields } = data as { profileId: string; fields: string[] };
    await db.candidates.update({
      where: { juiceboxProfileId: profileId },
      data: { enrichedFields: fields, enrichedAt: new Date() },
    });
  },

  "search.completed": async (data) => {
    const { searchId, resultCount, query } = data as {
      searchId: string; resultCount: number; query: string;
    };
    await notifySlack(
      `PeopleGPT search finished: "${query}" returned ${resultCount} candidates`
    );
  },

  "agent.match": async (data) => {
    const { agentId, candidateId, matchScore, jobId } = data as {
      agentId: string; candidateId: string; matchScore: number; jobId: string;
    };
    if (matchScore >= 0.85) {
      await ats.createCandidate({ jobId, candidateId, source: "juicebox-agent" });
    }
  },

  "export.ready": async (data) => {
    const { exportId, downloadUrl, recordCount } = data as {
      exportId: string; downloadUrl: string; recordCount: number;
    };
    await emailService.send({
      template: "export-ready",
      context: { exportId, downloadUrl, recordCount },
    });
  },
};

const router = Router();

router.post(
  "/webhooks/juicebox",
  raw({ type: "application/json" }),
  async (req, res) => {
    const signature = req.headers["x-juicebox-signature"] as string;

    if (!verifyJuiceboxSignature(req.body, signature, process.env.JUICEBOX_WEBHOOK_SECRET!)) {
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event: JuiceboxEvent = JSON.parse(req.body.toString());

    // Respond immediately — process async
    res.status(200).json({ received: true });

    // Idempotency check
    const alreadyProcessed = await redis.sismember("jb:delivered", event.id);
    if (alreadyProcessed) return;

    const handler = handlers[event.type];
    if (handler) {
      await handler(event.data);
      await redis.sadd("jb:delivered", event.id);
      // Expire delivery IDs after 72 hours
      await redis.expire("jb:delivered", 259200);
    } else {
      console.warn(`Unhandled Juicebox event type: ${event.type}`);
    }
  }
);

export default router;
```

### Step 4: Idempotent Processing with Delivery IDs

Every Juicebox webhook payload includes an `id` field (the delivery ID). Track processed IDs in Redis to prevent duplicate processing during retries:

```typescript
// lib/idempotency.ts
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);
const DELIVERY_KEY = "jb:webhook:delivered";
const TTL_SECONDS = 72 * 60 * 60; // 72 hours

export async function isAlreadyProcessed(deliveryId: string): Promise<boolean> {
  return (await redis.sismember(DELIVERY_KEY, deliveryId)) === 1;
}

export async function markProcessed(deliveryId: string): Promise<void> {
  await redis.sadd(DELIVERY_KEY, deliveryId);
  await redis.expire(DELIVERY_KEY, TTL_SECONDS);
}
```

### Step 5: Local Development with ngrok

```bash
# Terminal 1: Start your app
npm run dev

# Terminal 2: Expose localhost via ngrok
ngrok http 3000

# Terminal 3: Register the ngrok URL as a webhook
curl -X POST https://api.juicebox.ai/v1/webhooks \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://abc123.ngrok-free.app/webhooks/juicebox",
    "events": ["search.completed"],
    "secret": "whsec_dev_test_secret"
  }'

# Trigger a test search to fire the webhook
curl -X POST https://api.juicebox.ai/v1/search \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"query": "senior engineer at Google in San Francisco", "limit": 5}'
```

## Output

- `lib/juicebox-webhook.ts` -- HMAC-SHA256 signature verification function
- `routes/juicebox-webhooks.ts` -- Express route with typed event handlers
- `lib/idempotency.ts` -- Redis-backed delivery-ID deduplication
- Registered webhook endpoint in Juicebox dashboard

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Invalid signature` | Webhook secret mismatch between app and Juicebox | Verify `JUICEBOX_WEBHOOK_SECRET` matches the value registered via API |
| Duplicate `agent.match` events | Juicebox retries on non-200 response | Check delivery ID with `redis.sismember` before processing |
| `ECONNREFUSED` on local dev | ngrok tunnel expired or not running | Restart ngrok and re-register the webhook URL |
| Handler throws but 200 already sent | Async processing failure | Add dead-letter queue; log failures for retry with BullMQ |
| Missing event fields | API version mismatch | Pin webhook API version in registration; validate payload shape |

## Examples

**Register and verify a webhook endpoint:**

```typescript
import express from "express";
import webhookRouter from "./routes/juicebox-webhooks";

const app = express();
app.use(webhookRouter);
app.listen(3000, () => console.log("Webhook server listening on :3000"));
```

**Test signature verification locally:**

```typescript
import { verifyJuiceboxSignature } from "./lib/juicebox-webhook";
import crypto from "crypto";

const secret = "whsec_test_secret";
const body = Buffer.from(JSON.stringify({ id: "evt_123", type: "search.completed", data: {} }));
const sig = "sha256=" + crypto.createHmac("sha256", secret).update(body).digest("hex");

console.log(verifyJuiceboxSignature(body, sig, secret)); // true
```

## Resources

- [Juicebox API Documentation](https://juicebox.ai/docs/api)
- [Juicebox PeopleGPT](https://juicebox.ai/peoplegpt)
- [ngrok Quick Start](https://ngrok.com/docs/getting-started/)

## Next Steps

After webhooks are live, see `juicebox-rate-limits` for throttling high-volume event flows, or `juicebox-observability` for monitoring webhook delivery health.
