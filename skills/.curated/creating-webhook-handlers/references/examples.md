# Webhook Handler Examples

## HMAC Signature Verification

```javascript
// webhooks/verify.js
const crypto = require('crypto');

function verifySignature(rawBody, secret, signatureHeader) {
  const expected = crypto.createHmac('sha256', secret).update(rawBody).digest('hex');
  const received = signatureHeader.replace('sha256=', '');
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(received));
}

// Provider-specific verifiers
const verifiers = {
  stripe: (rawBody, headers, secret) => {
    const sig = headers['stripe-signature'];
    const parts = Object.fromEntries(sig.split(',').map(p => p.split('=')));
    const payload = `${parts.t}.${rawBody}`;
    const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');
    return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(parts.v1));
  },
  github: (rawBody, headers, secret) => {
    return verifySignature(rawBody, secret, headers['x-hub-signature-256']);
  },
  generic: (rawBody, headers, secret) => {
    return verifySignature(rawBody, secret, headers['x-webhook-signature']);
  },
};
```

## Webhook Receiver Endpoint

```javascript
// routes/webhooks.js
app.post('/webhooks/:provider',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const { provider } = req.params;
    const rawBody = req.body.toString();

    // 1. Verify signature
    const secret = process.env[`WEBHOOK_SECRET_${provider.toUpperCase()}`];
    const verifier = verifiers[provider] || verifiers.generic;

    if (!verifier(rawBody, req.headers, secret)) {
      logger.warn({ provider }, 'Webhook signature verification failed');
      return res.status(401).json({ detail: 'Invalid signature' });
    }

    const event = JSON.parse(rawBody);

    // 2. Idempotency check
    const eventId = event.id || event.eventId || req.headers['x-webhook-id'];
    const isDuplicate = await redis.get(`webhook:processed:${eventId}`);
    if (isDuplicate) {
      return res.status(200).json({ detail: 'Already processed' });
    }

    // 3. Acknowledge immediately
    res.status(200).json({ received: true });

    // 4. Process asynchronously
    await webhookQueue.add({ provider, event, eventId });
    await redis.setex(`webhook:processed:${eventId}`, 86400 * 7, 'true');
  }
);
```

## Event Dispatcher

```javascript
// webhooks/dispatcher.js
const handlers = {
  'payment_intent.succeeded': async (event) => {
    const { amount, currency, metadata } = event.data.object;
    await fulfillOrder(metadata.orderId, { amount, currency });
    await sendReceipt(metadata.customerId, amount);
  },

  'charge.refunded': async (event) => {
    const { id, amount_refunded } = event.data.object;
    await processRefund(id, amount_refunded);
  },

  'customer.subscription.deleted': async (event) => {
    const { customer } = event.data.object;
    await deactivateAccount(customer);
  },

  // GitHub
  'push': async (event) => {
    const { ref, commits, repository } = event;
    if (ref === 'refs/heads/main') {
      await triggerDeployment(repository.full_name, commits);
    }
  },
};

async function dispatch(provider, event) {
  const eventType = event.type || event.action || event.event;
  const handler = handlers[eventType];

  if (!handler) {
    logger.info({ provider, eventType }, 'No handler for event type');
    return;
  }

  try {
    await handler(event);
    logger.info({ provider, eventType }, 'Webhook processed');
  } catch (err) {
    logger.error({ provider, eventType, err }, 'Webhook handler failed');
    throw err; // Let queue retry
  }
}
```

## Queue Worker with Retries

```javascript
// queues/webhook-processor.js
const { Worker } = require('bullmq');

const worker = new Worker('webhooks', async (job) => {
  const { provider, event, eventId } = job.data;
  await dispatch(provider, event);
}, {
  connection: redis,
  attempts: 5,
  backoff: { type: 'exponential', delay: 60000 }, // 1m, 2m, 4m, 8m, 16m
});

worker.on('failed', async (job, err) => {
  if (job.attemptsMade >= job.opts.attempts) {
    logger.error({ eventId: job.data.eventId }, 'Webhook exhausted all retries, sending to DLQ');
    await deadLetterQueue.add(job.data);
  }
});
```

## Stripe Webhook (Complete Example)

```javascript
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

app.post('/webhooks/stripe',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    let event;
    try {
      event = stripe.webhooks.constructEvent(
        req.body,
        req.headers['stripe-signature'],
        process.env.STRIPE_WEBHOOK_SECRET
      );
    } catch (err) {
      return res.status(400).json({ detail: `Signature verification failed: ${err.message}` });
    }

    // Idempotency
    if (await redis.get(`stripe:${event.id}`)) {
      return res.json({ received: true, duplicate: true });
    }

    res.json({ received: true });
    await redis.setex(`stripe:${event.id}`, 604800, '1');
    await webhookQueue.add({ provider: 'stripe', event, eventId: event.id });
  }
);
```

## GitHub Webhook

```javascript
app.post('/webhooks/github',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['x-hub-signature-256'];
    if (!verifiers.github(req.body.toString(), req.headers, process.env.GITHUB_WEBHOOK_SECRET)) {
      return res.status(401).json({ detail: 'Invalid signature' });
    }

    const event = JSON.parse(req.body);
    const eventType = req.headers['x-github-event'];
    const deliveryId = req.headers['x-github-delivery'];

    res.json({ received: true });
    await webhookQueue.add({ provider: 'github', event: { ...event, action: eventType }, eventId: deliveryId });
  }
);
```

## Local Development with ngrok

```bash
# Start ngrok tunnel
ngrok http 3000

# Register webhook with provider
curl -X POST https://api.stripe.com/v1/webhook_endpoints \
  -u sk_test_...: \
  -d "url=https://abc123.ngrok.io/webhooks/stripe" \
  -d "enabled_events[]=payment_intent.succeeded" \
  -d "enabled_events[]=charge.refunded"
```

## Replay Tests

```javascript
describe('Webhook Handlers', () => {
  const stripePayload = require('./fixtures/stripe-payment-intent-succeeded.json');

  it('accepts valid Stripe signature', async () => {
    const body = JSON.stringify(stripePayload);
    const timestamp = Math.floor(Date.now() / 1000);
    const sig = crypto.createHmac('sha256', process.env.STRIPE_WEBHOOK_SECRET)
      .update(`${timestamp}.${body}`).digest('hex');

    const res = await request(app)
      .post('/webhooks/stripe')
      .set('Content-Type', 'application/json')
      .set('Stripe-Signature', `t=${timestamp},v1=${sig}`)
      .send(body);
    expect(res.status).toBe(200);
  });

  it('rejects tampered payload', async () => {
    const res = await request(app)
      .post('/webhooks/stripe')
      .set('Stripe-Signature', 't=123,v1=invalid')
      .send('{}');
    expect(res.status).toBe(400);
  });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
