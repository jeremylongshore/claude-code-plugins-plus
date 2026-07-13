# API Event Emitter Examples

## Event Schema

```json
{
  "eventId": "evt_a1b2c3d4",
  "eventType": "order.created",
  "version": "1.0",
  "timestamp": "2026-03-10T14:30:00.000Z",
  "source": "order-service",
  "data": {
    "orderId": "ord_xyz789",
    "userId": "usr_abc123",
    "total": 99.99,
    "currency": "USD",
    "items": [{ "productId": "prod_001", "quantity": 2, "price": 49.99 }]
  }
}
```

## Transactional Outbox Pattern

```javascript
// events/emitter.js
async function emitEvent(eventType, data, { tx } = {}) {
  const event = {
    eventId: crypto.randomUUID(),
    eventType, version: '1.0',
    timestamp: new Date().toISOString(),
    source: process.env.SERVICE_NAME, data,
  };
  const query = tx || db;
  await query('INSERT INTO outbox (event_id, event_type, payload) VALUES ($1, $2, $3)',
    [event.eventId, event.eventType, JSON.stringify(event)]);
  return event;
}

app.post('/orders', async (req, res) => {
  const result = await db.transaction(async (tx) => {
    const order = await tx('INSERT INTO orders ... RETURNING *', [...]);
    await emitEvent('order.created', { orderId: order.id, total: order.total }, { tx });
    return order;
  });
  res.status(201).json(result);
});
```

## Outbox Poller (Kafka)

```javascript
const { Kafka } = require('kafkajs');
const producer = new Kafka({ brokers: [process.env.KAFKA_BROKER] }).producer();

async function pollOutbox() {
  const events = await db.query(
    'SELECT * FROM outbox WHERE published = false ORDER BY created_at LIMIT 100'
  );
  for (const event of events.rows) {
    await producer.send({
      topic: event.event_type.replace('.', '-'),
      messages: [{ key: event.event_id, value: event.payload }],
    });
    await db.query('UPDATE outbox SET published = true WHERE event_id = $1', [event.event_id]);
  }
}
setInterval(pollOutbox, 100);
```

## Webhook Subscription API

```javascript
app.post('/webhooks', authenticateToken, async (req, res) => {
  const { url, events } = req.body;
  try {
    await fetch(url, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
  } catch {
    return res.status(400).json({ detail: 'Webhook URL not reachable' });
  }
  const secret = crypto.randomBytes(32).toString('hex');
  const webhook = await db.webhooks.create({
    userId: req.user.id, url, events, secret, active: true,
  });
  res.status(201).json({ id: webhook.id, url, events, secret });
});

app.get('/webhooks', authenticateToken, async (req, res) => {
  const hooks = await db.webhooks.findByUser(req.user.id);
  res.json(hooks.map(w => ({ id: w.id, url: w.url, events: w.events, active: w.active })));
});

app.delete('/webhooks/:id', authenticateToken, async (req, res) => {
  await db.webhooks.delete(req.params.id, req.user.id);
  res.status(204).end();
});
```

## Webhook Delivery with HMAC Signing

```javascript
async function deliverWebhook(webhook, event) {
  const payload = JSON.stringify(event);
  const signature = crypto.createHmac('sha256', webhook.secret).update(payload).digest('hex');
  const backoff = [60000, 300000, 1800000, 7200000, 86400000];

  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      const resp = await fetch(webhook.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Webhook-Signature': `sha256=${signature}`,
          'X-Webhook-ID': event.eventId,
        },
        body: payload,
        signal: AbortSignal.timeout(10000),
      });
      if (resp.ok) return;
      if (resp.status < 500 && resp.status !== 429) return;
    } catch {}
    await new Promise(r => setTimeout(r, backoff[attempt]));
  }
  await deadLetterQueue.add({ webhookId: webhook.id, event });
}
```

## Server-Sent Events Endpoint

```javascript
app.get('/events/stream', authenticateToken, (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  });

  const types = req.query.types?.split(',') || ['*'];
  const subscriber = redis.duplicate();
  subscriber.subscribe('api-events');
  subscriber.on('message', (ch, msg) => {
    const event = JSON.parse(msg);
    if (types.includes('*') || types.includes(event.eventType)) {
      res.write(`id: ${event.eventId}\nevent: ${event.eventType}\ndata: ${JSON.stringify(event.data)}\n\n`);
    }
  });

  const heartbeat = setInterval(() => res.write(':keepalive\n\n'), 15000);
  req.on('close', () => { clearInterval(heartbeat); subscriber.quit(); });
});
```

## SSE Client (Browser)

```javascript
const es = new EventSource('/events/stream?types=order.created,order.shipped');
es.addEventListener('order.created', (e) => {
  const order = JSON.parse(e.data);
  console.log(`New order: ${order.orderId} - $${order.total}`);
});
es.addEventListener('order.shipped', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Shipped: ${data.orderId}, tracking: ${data.trackingNumber}`);
});
es.onerror = () => console.log('SSE reconnecting...');
```

## curl: Webhooks and SSE

```bash
# Register webhook
curl -X POST http://localhost:3000/webhooks \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"url":"https://hook.example.com/events","events":["order.created"]}'
# {"id":"wh_123","secret":"abc..."}

# SSE stream
curl -N http://localhost:3000/events/stream?types=order.created \
  -H "Authorization: Bearer $TOKEN"
# id: evt_a1b2c3d4
# event: order.created
# data: {"orderId":"ord_xyz789","total":99.99}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
