# Webhook HMAC Verification

Complete Express middleware for verifying Shopify webhook signatures using HMAC-SHA256 with timing-safe comparison.

```typescript
import crypto from "crypto";
import express from "express";

function verifyShopifyWebhook(
  rawBody: Buffer,
  hmacHeader: string,
  secret: string
): boolean {
  const computed = crypto
    .createHmac("sha256", secret)
    .update(rawBody)
    .digest("base64");

  // Timing-safe comparison prevents timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(computed),
    Buffer.from(hmacHeader)
  );
}

// Express middleware — MUST use raw body parser
app.post(
  "/webhooks",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const hmac = req.headers["x-shopify-hmac-sha256"] as string;
    const topic = req.headers["x-shopify-topic"] as string;
    const shop = req.headers["x-shopify-shop-domain"] as string;

    if (!verifyShopifyWebhook(req.body, hmac, process.env.SHOPIFY_API_SECRET!)) {
      console.warn(`Invalid webhook HMAC from ${shop}, topic: ${topic}`);
      return res.status(401).send("HMAC validation failed");
    }

    const payload = JSON.parse(req.body.toString());
    console.log(`Verified webhook: ${topic} from ${shop}`);

    // Process asynchronously — respond 200 within 5 seconds
    processWebhookAsync(topic, shop, payload);
    res.status(200).send("OK");
  }
);
```
