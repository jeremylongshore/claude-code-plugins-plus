# Architecture Code Examples

## Single Webhook Server (Simple)

**Best for:** Prototyping, < 10 concurrent calls, single agent.

```
Retell Platform -> WebSocket -> Your Webhook Server -> LLM API
                                       |
                                  Local State (memory)
```

```typescript
import express from 'express';
const app = express();
const callState = new Map();

app.post('/retell-webhook', async (req, res) => {
  const { call_id, transcript } = req.body;
  const state = callState.get(call_id) || { history: [] };
  state.history.push(transcript);
  const response = await generateResponse(state);
  callState.set(call_id, state);
  res.json({ response });  // Must respond < 1 second
});
```

## Distributed Webhook with Shared State (Production)

**Best for:** 10-100 concurrent calls, multiple agents, production.

```
Retell Platform -> Load Balancer -> Webhook Server 1
                                 -> Webhook Server 2
                                 -> Webhook Server 3
                                         |
                                    Redis (shared state)
                                         |
                                    LLM API (cached)
```

```typescript
class DistributedCallHandler {
  constructor(private redis: Redis, private llm: LLMClient) {}

  async handleTurn(callId: string, transcript: string) {
    const state = await this.redis.get(`call:${callId}`);
    const context = JSON.parse(state || '{"history":[]}');
    context.history.push(transcript);

    // Cache common responses for < 100ms latency
    const cacheKey = `response:${this.hash(transcript)}`;
    let response = await this.redis.get(cacheKey);
    if (!response) {
      response = await this.llm.generate(context);
      await this.redis.setex(cacheKey, 3600, response);
    }
    await this.redis.setex(`call:${callId}`, 3600, JSON.stringify(context));
    return response;
  }
}
```

## Event-Driven Voice Pipeline (Scale)

**Best for:** 100+ concurrent calls, complex flows, analytics.

```
Retell Platform -> API Gateway -> Webhook Service -> Redis (state)
                                                  -> Event Bus (Kafka)
                                                         |
                                          +--------------+------------+
                                          |              |            |
                                    Analytics      Transcription   Escalation
                                     Service        Archive       Handler
```

```typescript
class VoicePipeline {
  async handleCall(event: RetellEvent) {
    // Fast response path (< 500ms budget)
    const response = await this.generateFast(event);
    // Async: emit events for downstream processing
    await this.eventBus.emit('call.turn', {
      callId: event.call_id,
      transcript: event.transcript,
      response: response
    });
    return response;
  }
}
```
