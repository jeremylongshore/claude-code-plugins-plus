# Webhook Observability

Express middleware for tracking webhook HMAC validation, processing success/failure, and duration metrics.

```typescript
app.post("/webhooks", express.raw({ type: "application/json" }), (req, res) => {
  const topic = req.headers["x-shopify-topic"] as string;
  const shop = req.headers["x-shopify-shop-domain"] as string;

  // Track HMAC validation
  if (!verifyHmac(req.body, req.headers["x-shopify-hmac-sha256"]!)) {
    webhookCounter.inc({ topic, status: "invalid_hmac" });
    return res.status(401).send();
  }

  res.status(200).send("OK");

  // Track processing
  const start = Date.now();
  processWebhook(topic, shop, JSON.parse(req.body.toString()))
    .then(() => {
      webhookCounter.inc({ topic, status: "success" });
      apiDuration.observe(
        { operation: `webhook:${topic}`, status: "success", api_type: "webhook" },
        (Date.now() - start) / 1000
      );
    })
    .catch((err) => {
      webhookCounter.inc({ topic, status: "error" });
      console.error(`Webhook ${topic} failed:`, err.message);
    });
});
```
