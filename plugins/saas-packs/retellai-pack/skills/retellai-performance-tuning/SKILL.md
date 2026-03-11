---
name: retellai-performance-tuning
description: |
  Optimize Retell AI API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Retell AI integrations.
  Trigger with phrases like "retellai performance", "optimize retellai",
  "retellai latency", "retellai caching", "retellai slow", "retellai batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Retell AI Performance Tuning

## Overview
Optimize Retell AI voice agent latency and call quality. Focus on reducing voice-to-voice latency, LLM response time, WebSocket connection management, and agent configuration tuning for natural conversations.

## Prerequisites
- Retell AI account with API key
- `retell-sdk` npm package installed
- WebSocket infrastructure for real-time calls
- Understanding of voice agent architecture

## Instructions

### Step 1: Optimize Agent LLM Configuration
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

### Step 2: Optimize LLM Prompt for Speed
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
    begin_message: 'Hi, how can I help you today?',
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

### Step 3: WebSocket Connection Pooling
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

### Step 4: Call Analytics Caching
```typescript
import { LRUCache } from 'lru-cache';

const callCache = new LRUCache<string, any>({
  max: 500,
  ttl: 1000 * 60 * 15, // 15 min - completed calls don't change
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

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High voice latency | Complex LLM prompt | Shorten prompt, use gpt-4o-mini |
| WebSocket disconnect | Network instability | Implement reconnection logic |
| Unnatural pauses | Low responsiveness setting | Increase responsiveness to 0.8+ |
| Missed interrupts | Low sensitivity | Increase interruption_sensitivity |

## Examples

### Latency Monitoring
```typescript
retell.on('call_analyzed', (event) => {
  const latency = event.call_analysis?.latency_p95;
  if (latency && latency > 1500) {
    console.warn(`High latency call ${event.call_id}: ${latency}ms p95`);
  }
});
```

## Resources
- [Retell AI API Reference](https://docs.retellai.com/api-references)
- [Retell Agent Configuration](https://docs.retellai.com/build-agent)
- [Voice Latency Optimization](https://docs.retellai.com/optimize-latency)
