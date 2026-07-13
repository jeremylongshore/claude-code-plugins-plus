# Resilience Code Patterns

## WebSocket Connection Resilience

```typescript
class ResilientRetellConnection {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnects = 3;

  async connect(callId: string) {
    this.ws = new WebSocket(`wss://api.retellai.com/llm/${callId}`);

    this.ws.on('close', async (code) => {
      if (code !== 1000 && this.reconnectAttempts < this.maxReconnects) {
        this.reconnectAttempts++;
        await new Promise(r => setTimeout(r, 500 * this.reconnectAttempts));
        await this.connect(callId);
      }
    });

    this.ws.on('error', (err) => {
      console.error(`WebSocket error for call ${callId}:`, err.message);
    });
  }
}
```

## Response Latency Budget

Voice agents must respond in under 1 second. Budget webhook processing time accordingly.

```typescript
const LATENCY_BUDGET_MS = 800;  // leave 200ms for network

app.post('/retell-webhook', async (req, res) => {
  const start = Date.now();

  // Fast path: check cache first
  const cached = await redis.get(`response:${req.body.transcript_hash}`);
  if (cached) {
    return res.json(JSON.parse(cached));
  }

  // Generate response with timeout
  const response = await Promise.race([
    generateResponse(req.body),
    timeout(LATENCY_BUDGET_MS).then(() => getFallbackResponse(req.body))
  ]);

  const elapsed = Date.now() - start;
  metrics.record('webhook_latency', elapsed);
  if (elapsed > 500) metrics.record('slow_webhook', 1);

  res.json(response);
});
```

## Call State Recovery

If the webhook server restarts mid-call, restore conversation context from Redis.

```typescript
class CallStateManager {
  private store: Redis;

  async saveState(callId: string, state: any) {
    await this.store.setex(
      `call:${callId}`,
      3600,  // 1 hour TTL
      JSON.stringify(state)
    );
  }

  async recoverState(callId: string): Promise<any | null> {
    const raw = await this.store.get(`call:${callId}`);
    return raw ? JSON.parse(raw) : null;
  }

  async endCall(callId: string) {
    const state = await this.recoverState(callId);
    if (state) {
      await this.archiveCall(callId, state);
      await this.store.del(`call:${callId}`);
    }
  }
}
```

## Concurrent Call Management

```typescript
class CallCapacityManager {
  private active = new Set<string>();
  private maxConcurrent: number;

  constructor(maxConcurrent = 10) {
    this.maxConcurrent = maxConcurrent;
  }

  canAcceptCall(): boolean {
    return this.active.size < this.maxConcurrent;
  }

  startCall(callId: string) { this.active.add(callId); }
  endCall(callId: string) { this.active.delete(callId); }

  getHealth() {
    return {
      active: this.active.size,
      capacity: this.maxConcurrent,
      utilization: this.active.size / this.maxConcurrent
    };
  }
}
```

## Latency Dashboard

```typescript
const dashboard = {
  p50_latency: metrics.percentile('webhook_latency', 50),
  p99_latency: metrics.percentile('webhook_latency', 99),
  active_calls: capacity.active.size,
  slow_webhooks_pct: metrics.rate('slow_webhook')
};
```
