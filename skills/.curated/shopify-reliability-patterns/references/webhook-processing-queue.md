# Webhook Processing Queue

BullMQ-based async webhook processing with HMAC verification, exponential backoff, and idempotency.

```typescript
import { Queue, Worker } from "bullmq";

const webhookQueue = new Queue("shopify-webhooks", {
  connection: { host: "localhost", port: 6379 },
  defaultJobOptions: {
    attempts: 5,
    backoff: { type: "exponential", delay: 5000 },
    removeOnComplete: 1000,
    removeOnFail: 5000,
  },
});

// Enqueue webhook for processing
app.post("/webhooks", rawBodyParser, (req, res) => {
  // Verify HMAC first
  if (!verifyHmac(req.body, req.headers["x-shopify-hmac-sha256"]!)) {
    return res.status(401).send();
  }

  // Respond immediately
  res.status(200).send("OK");

  // Queue for async processing
  webhookQueue.add(req.headers["x-shopify-topic"] as string, {
    topic: req.headers["x-shopify-topic"],
    shop: req.headers["x-shopify-shop-domain"],
    webhookId: req.headers["x-shopify-webhook-id"],
    payload: req.body.toString(),
  });
});

// Worker processes queued webhooks
const worker = new Worker("shopify-webhooks", async (job) => {
  const { topic, shop, webhookId, payload } = job.data;

  await processWebhookIdempotently(webhookId, topic, async () => {
    await handleWebhookEvent(topic, JSON.parse(payload));
  });
}, {
  connection: { host: "localhost", port: 6379 },
  concurrency: 10,
});
```
