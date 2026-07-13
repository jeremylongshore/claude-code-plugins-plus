# Webhook Idempotency

Redis-backed idempotency handler using `X-Shopify-Webhook-Id` for deduplication.

```typescript
import { Redis } from "ioredis";
const redis = new Redis(process.env.REDIS_URL!);

async function processWebhookIdempotently(
  webhookId: string, // X-Shopify-Webhook-Id header
  topic: string,
  handler: () => Promise<void>
): Promise<{ processed: boolean; duplicate: boolean }> {
  const key = `shopify:webhook:${webhookId}`;

  // Check if already processed
  const exists = await redis.exists(key);
  if (exists) {
    console.log(`Duplicate webhook ${webhookId} for ${topic} — skipping`);
    return { processed: false, duplicate: true };
  }

  // Mark as processing (with TTL to auto-expire)
  await redis.set(key, "processing", "EX", 7 * 86400, "NX"); // 7 day TTL

  try {
    await handler();
    await redis.set(key, "completed", "EX", 7 * 86400);
    return { processed: true, duplicate: false };
  } catch (error) {
    // Remove the key so Shopify's retry can re-process
    await redis.del(key);
    throw error;
  }
}

// Usage in webhook handler
app.post("/webhooks", rawBodyParser, async (req, res) => {
  const webhookId = req.headers["x-shopify-webhook-id"] as string;
  const topic = req.headers["x-shopify-topic"] as string;

  // ALWAYS respond 200 within 5 seconds
  res.status(200).send("OK");

  // Process asynchronously with idempotency
  await processWebhookIdempotently(webhookId, topic, async () => {
    const payload = JSON.parse(req.body.toString());
    await handleWebhookEvent(topic, payload);
  });
});
```
