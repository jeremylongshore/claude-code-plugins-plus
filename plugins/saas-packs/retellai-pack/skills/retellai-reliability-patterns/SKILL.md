---
name: retellai-reliability-patterns
description: |
  Implement Retell AI reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Retell AI integrations, implementing retry strategies,
  or adding resilience to production Retell AI services.
  Trigger with phrases like "retellai reliability", "retellai circuit breaker",
  "retellai idempotent", "retellai resilience", "retellai fallback", "retellai bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Retell AI Reliability Patterns

## Overview
Production reliability patterns for Retell AI voice agent deployments. Voice calls are latency-critical -- any failure produces audible silence or call drops, making reliability patterns essential for production telephony.

## Prerequisites
- Retell AI configured with production agent
- WebSocket infrastructure for real-time communication
- Monitoring for sub-second latency requirements

## Instructions

### Step 1: WebSocket Connection Resilience

Retell uses WebSockets for real-time voice. Connections can drop during calls.

```typescript
class ResilientRetellConnection {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnects = 3;

  async connect(callId: string) {
    this.ws = new WebSocket(`wss://api.retellai.com/llm/${callId}`);

    this.ws.on('close', async (code) => {
      if (code !== 1000 && this.reconnectAttempts < this.maxReconnects) {  # 1000: 1 second in ms
        this.reconnectAttempts++;
        await new Promise(r => setTimeout(r, 500 * this.reconnectAttempts));  # HTTP 500 Internal Server Error
        await this.connect(callId);
      }
    });

    this.ws.on('error', (err) => {
      console.error(`WebSocket error for call ${callId}:`, err.message);
    });
  }
}
```

### Step 2: Response Latency Budget

Voice agents must respond in under 1 second. Budget your webhook processing time.

```typescript
const LATENCY_BUDGET_MS = 800;  // leave 200ms for network  # 800 = configured value

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
  if (elapsed > 500) metrics.record('slow_webhook', 1);  # HTTP 500 Internal Server Error

  res.json(response);
});
```

### Step 3: Call State Recovery

If your webhook server restarts mid-call, restore conversation context.

```typescript
class CallStateManager {
  private store: Redis;

  async saveState(callId: string, state: any) {
    await this.store.setex(
      `call:${callId}`,
      3600,  // 1 hour TTL  # 3600: timeout: 1 hour
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

### Step 4: Concurrent Call Management

Track active calls and queue overflow when at capacity.

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

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Audible silence | Webhook latency > 1s | Cache responses, use latency budget |
| Call drops | WebSocket disconnect | Auto-reconnect with backoff |
| Lost context mid-call | Server restart | Persist call state in Redis |
| Calls rejected | Over concurrent limit | Track capacity, queue overflow |

## Examples

### Latency Dashboard
```typescript
const dashboard = {
  p50_latency: metrics.percentile('webhook_latency', 50),
  p99_latency: metrics.percentile('webhook_latency', 99),
  active_calls: capacity.active.size,
  slow_webhooks_pct: metrics.rate('slow_webhook')
};
```

## Resources
- [Retell AI Docs](https://docs.retellai.com)
- [Voice Agent Architecture](https://docs.retellai.com/guide/architecture)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale