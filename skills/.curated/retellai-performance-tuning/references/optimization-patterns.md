# Optimization Patterns

## Agent LLM Configuration for Low Latency

```typescript
import Retell from 'retell-sdk';

const retell = new Retell({ apiKey: process.env.RETELL_API_KEY! });

// Configure agent for low latency
async function createOptimizedAgent() {
  return retell.agent.create({
    agent_name: 'fast-responder',
    response_engine: {
      type: 'retell-llm',
      llm_id: process.env.RETELL_LLM_ID!,
    },
    voice_id: 'eleven_labs_rachel', // Pre-cached voice
    language: 'en-US',
    interruption_sensitivity: 0.8, // Higher = faster interrupt detection
    ambient_sound: null,           // Disable for lower latency
    responsiveness: 0.9,           // Higher = responds faster
    voice_speed: 1.1,              // Slightly faster speech
    voice_temperature: 0.3,        // Lower = more deterministic
    enable_backchannel: true,      // "uh-huh" for natural flow
    boosted_keywords: ['appointment', 'schedule', 'callback'],
  });
}
```

## Optimized LLM Prompt

```typescript
async function createOptimizedLLM() {
  return retell.llm.create({
    general_prompt: `You are a fast, helpful phone agent.
Rules for speed:
- Keep responses under 2 sentences
- Never use filler words
- Ask one question at a time
- Confirm details immediately
- Use short acknowledgments`,
    begin_message: 'Hi, what can we do for you today?',
    model: 'gpt-4o-mini',     // Faster than gpt-4o
    general_tools: [
      {
        type: 'end_call',
        name: 'end_call',
        description: 'End the call when conversation is complete',
      },
      {
        type: 'custom',
        name: 'book_appointment',
        description: 'Book an appointment for the caller',
        parameters: {
          type: 'object',
          properties: {
            date: { type: 'string' },
            time: { type: 'string' },
            name: { type: 'string' },
          },
          required: ['date', 'time', 'name'],
        },
        url: process.env.BOOKING_WEBHOOK_URL!,
      },
    ],
  });
}
```

## WebSocket Connection Pooling

```typescript
import WebSocket from 'ws';

const connectionPool: Map<string, WebSocket> = new Map();

async function getWebSocketConnection(callId: string): Promise<WebSocket> {
  const existing = connectionPool.get(callId);
  if (existing?.readyState === WebSocket.OPEN) return existing;

  const ws = new WebSocket(
    `wss://api.retellai.com/audio-websocket/${callId}`,
    { headers: { Authorization: `Bearer ${process.env.RETELL_API_KEY}` } }
  );

  return new Promise((resolve, reject) => {
    ws.on('open', () => {
      connectionPool.set(callId, ws);
      resolve(ws);
    });
    ws.on('error', reject);
    ws.on('close', () => connectionPool.delete(callId));
  });
}
```

## Call Analytics Caching

```typescript
import { LRUCache } from 'lru-cache';

const callCache = new LRUCache<string, any>({
  max: 500,
  ttl: 1000 * 60 * 15, // 15 min - completed calls are immutable
});

async function getCallDetails(callId: string) {
  const cached = callCache.get(callId);
  if (cached) return cached;

  const call = await retell.call.retrieve(callId);
  if (call.call_status === 'ended') {
    callCache.set(callId, call); // Only cache completed calls
  }
  return call;
}

async function getCallMetrics(callIds: string[]) {
  const calls = await Promise.all(callIds.map(getCallDetails));
  return {
    avgDuration: calls.reduce((s, c) => s + (c.end_timestamp - c.start_timestamp), 0) / calls.length,
    avgLatency: calls.reduce((s, c) => s + (c.latency_p50 || 0), 0) / calls.length,
    successRate: calls.filter(c => c.disconnection_reason === 'agent_goodbye').length / calls.length,
  };
}
```

## Latency Monitoring

```typescript
retell.on('call_analyzed', (event) => {
  const latency = event.call_analysis?.latency_p95;
  if (latency && latency > 1500) {
    console.warn(`High latency call ${event.call_id}: ${latency}ms p95`);
  }
});
```
