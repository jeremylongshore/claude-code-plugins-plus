---
name: speak-webhooks-events
description: |
  Implement Speak webhook signature validation and event handling for language learning.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Speak event notifications for lessons and progress.
  Trigger with phrases like "speak webhook", "speak events",
  "speak webhook signature", "handle speak events", "speak notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Webhooks Events

## Overview
Securely handle Speak webhooks with signature validation for language learning event notifications.

## Prerequisites
- Speak webhook secret configured
- HTTPS endpoint accessible from internet
- Understanding of cryptographic signatures
- Redis or database for idempotency (optional)

## Instructions
1. **Speak Event Types**
2. **Webhook Endpoint Setup**
3. **Signature Verification**
4. **Event Handler Pattern**
5. **Idempotency Handling**
6. **Webhook Testing**
7. **Local Development with ngrok**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Secure webhook endpoint
- Signature validation enabled
- Event handlers implemented
- Replay attack protection active
- Idempotency for duplicate prevention

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify webhook secret |
| Timestamp rejected | Clock drift | Check server time sync |
| Duplicate events | Missing idempotency | Implement event ID tracking |
| Handler timeout | Slow processing | Use async queue |
| Event not recognized | New event type | Add handler or log |

## Resources
- [Speak Webhooks Guide](https://developer.speak.com/docs/webhooks)
- [Webhook Security Best Practices](https://developer.speak.com/docs/webhooks/security)
- [Event Reference](https://developer.speak.com/docs/events)

## Next Steps
For performance optimization, see `speak-performance-tuning`.

## Examples

### Basic: Webhook Endpoint with Signature Verification
```typescript
import express from "express";
import crypto from "crypto";

const app = express();
app.use("/webhooks/speak", express.raw({ type: "application/json" }));

function verifySignature(payload: Buffer, signature: string, secret: string): boolean {
  const expected = crypto.createHmac("sha256", secret).update(payload).digest("hex");
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

app.post("/webhooks/speak", (req, res) => {
  const sig = req.headers["x-speak-signature"] as string;
  if (!verifySignature(req.body, sig, process.env.SPEAK_WEBHOOK_SECRET!)) {
    return res.status(401).send("Invalid signature");
  }

  const event = JSON.parse(req.body.toString());
  console.log(`Received event: ${event.type}`, event.data);
  res.status(200).send("ok");
});
```

### Advanced: Event Router with Idempotency and Async Processing
```typescript
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
await redis.connect();

type EventHandler = (data: any) => Promise<void>;

const handlers: Record<string, EventHandler> = {
  "lesson.completed": async (data) => {
    await db.updateStudentProgress(data.userId, data.lessonId, data.score);
    if (data.score >= 80) await unlockNextLesson(data.userId);
  },
  "pronunciation.assessed": async (data) => {
    await db.savePronunciationResult(data.userId, data.assessment);
    if (data.assessment.score < 50) await scheduleRemedialDrill(data.userId, data.assessment.weakPhonemes);
  },
  "subscription.changed": async (data) => {
    await db.updateUserTier(data.userId, data.newTier);
  },
};

app.post("/webhooks/speak", async (req, res) => {
  const sig = req.headers["x-speak-signature"] as string;
  if (!verifySignature(req.body, sig, process.env.SPEAK_WEBHOOK_SECRET!)) {
    return res.status(401).send("Invalid signature");
  }

  const event = JSON.parse(req.body.toString());

  // Idempotency check — skip already-processed events
  const seen = await redis.get(`speak:event:${event.id}`);
  if (seen) return res.status(200).send("already processed");

  const handler = handlers[event.type];
  if (handler) {
    await handler(event.data);
    await redis.set(`speak:event:${event.id}`, "1", { EX: 86400 }); // 24h TTL
  }

  res.status(200).send("ok");
});
```