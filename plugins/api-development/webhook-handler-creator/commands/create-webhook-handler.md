---
description: Create secure webhook endpoints with validation
shortcut: webhook
---

# Create Webhook Handler

Build secure webhook endpoints with signature verification, idempotency, and retry handling.

## What You Do

1. **Generate webhook endpoint:**
   - POST endpoint for webhook delivery
   - Signature verification (HMAC-SHA256)
   - Request validation
   - Idempotency key handling

2. **Implement security:**
   - Verify webhook signatures
   - Check timestamp freshness
   - Rate limiting per source
   - IP allowlist (optional)

3. **Add reliability:**
   - Idempotent processing
   - Retry mechanism with exponential backoff
   - Dead letter queue for failures
   - Webhook event logging

4. **Create event handlers:**
   - Event type routing
   - Async processing with queues
   - Error handling and alerts
   - Webhook health monitoring

## Example Structure

```javascript
// Webhook endpoint
POST /webhooks/stripe

// Verify signature
const signature = req.headers['stripe-signature'];
const isValid = verifySignature(payload, signature, secret);

// Handle idempotency
const eventId = req.body.id;
if (alreadyProcessed(eventId)) return 200;

// Route by event type
switch (req.body.type) {
  case 'payment.succeeded':
    await handlePayment(req.body.data);
    break;
  case 'subscription.canceled':
    await handleCancellation(req.body.data);
    break;
}
```

Generate production-ready webhook handlers with enterprise security.
