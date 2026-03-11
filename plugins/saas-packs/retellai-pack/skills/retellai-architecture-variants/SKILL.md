---
name: retellai-architecture-variants
description: |
  Choose and implement Retell AI validated architecture blueprints for different scales.
  Use when designing new Retell AI integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths for Retell AI applications.
  Trigger with phrases like "retellai architecture", "retellai blueprint",
  "how to structure retellai", "retellai project layout", "retellai microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Retell AI Architecture Variants

## Overview
Deployment architectures for Retell AI voice agents at different scales. Voice AI systems require real-time processing with strict latency budgets -- architecture choices directly impact call quality.

## Prerequisites
- Retell AI account with agent configured
- Understanding of WebSocket real-time communication
- Infrastructure for voice processing latency requirements

## Instructions

### Step 1: Single Webhook Server (Simple)

**Best for:** Prototyping, < 10 concurrent calls, single agent.

```
set -euo pipefail
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

### Step 2: Distributed Webhook with Shared State (Production)

**Best for:** 10-100 concurrent calls, multiple agents, production.

```
set -euo pipefail
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
      await this.redis.setex(cacheKey, 3600, response);  # 3600: timeout: 1 hour
    }
    await this.redis.setex(`call:${callId}`, 3600, JSON.stringify(context));  # timeout: 1 hour
    return response;
  }
}
```

### Step 3: Event-Driven Voice Pipeline (Scale)

**Best for:** 100+ concurrent calls, complex flows, analytics.

```
set -euo pipefail
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

## Decision Matrix

| Factor | Single Server | Distributed | Event-Driven |
|--------|--------------|-------------|--------------|
| Concurrent Calls | < 10 | 10-100 | 100+ |
| Latency Budget | 800ms | 500ms | 300ms |
| State | In-memory | Redis | Redis + Events |
| Scaling | Vertical | Horizontal | Auto-scaling |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Calls drop under load | Single server bottleneck | Scale to distributed architecture |
| Lost call state | Server restart | Move state to Redis |
| High latency | LLM response too slow | Pre-cache common responses |

## Resources
- [Retell AI Architecture](https://docs.retellai.com/guide/architecture)
- [Retell AI Docs](https://docs.retellai.com)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Examples

**Basic usage**: Apply retellai architecture variants to a standard project setup with default configuration options.

**Advanced scenario**: Customize retellai architecture variants for production environments with multiple constraints and team-specific requirements.