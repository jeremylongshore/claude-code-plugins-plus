# OpenEvidence Webhooks & Events - Implementation Details

## Webhook Endpoint with Signature Verification
```typescript
function verifySignature(req, res, next) {
  const signature = req.headers['x-openevidence-signature'];
  const parts = signature.split(',').reduce((acc, part) => { const [k, v] = part.split('='); acc[k] = v; return acc; }, {});
  const timestamp = parseInt(parts['t']);
  if (Math.abs(Date.now() / 1000 - timestamp) > 300) return res.status(401).json({ error: 'Timestamp too old' });
  const expectedSig = crypto.createHmac('sha256', WEBHOOK_SECRET).update(`${timestamp}.${JSON.stringify(req.body)}`).digest('hex');
  if (!crypto.timingSafeEqual(Buffer.from(parts['v1']), Buffer.from(expectedSig))) return res.status(401).json({ error: 'Invalid signature' });
  next();
}
```

## Event Handlers
Handlers for: deepconsult.started, deepconsult.progress, deepconsult.completed, deepconsult.failed, rate_limit.warning, api_key.expiring. Includes database updates, user notifications (WebSocket + email), and ops alerting.

## Webhook Registration
```typescript
await client.webhooks.register({
  url: webhookUrl,
  events: ['deepconsult.started', 'deepconsult.progress', 'deepconsult.completed', 'deepconsult.failed', 'rate_limit.warning', 'api_key.expiring'],
  secret: process.env.OPENEVIDENCE_WEBHOOK_SECRET!,
});
```

## Idempotency Handling
```typescript
export async function isProcessed(webhookId: string): Promise<boolean> { /* Check DB */ }
export async function markProcessed(webhookId: string): Promise<void> { /* Store with 24h TTL */ }
```

## Webhook Testing
```typescript
describe('OpenEvidence Webhooks', () => {
  it('should accept valid webhook', async () => {
    const timestamp = Math.floor(Date.now() / 1000);
    const payload = { id: 'webhook-123', event: 'deepconsult.completed', data: { consultId: 'consult-456', report: { executiveSummary: 'Test' } } };
    const response = await request(app)
      .post('/webhooks/openevidence')
      .set('x-openevidence-signature', generateSignature(payload, timestamp))
      .send(payload);
    expect(response.status).toBe(200);
  });
});
```
