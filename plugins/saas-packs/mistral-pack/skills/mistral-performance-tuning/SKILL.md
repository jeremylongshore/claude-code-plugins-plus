---
name: mistral-performance-tuning
description: |
  Optimize Mistral AI performance with caching, batching, and latency reduction.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Mistral AI integrations.
  Trigger with phrases like "mistral performance", "optimize mistral",
  "mistral latency", "mistral caching", "mistral slow", "mistral batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Performance Tuning

## Overview
Optimize Mistral AI API response times and throughput for production integrations. Key performance factors include model selection (mistral-small: ~200-500ms, mistral-large: ~500-2000ms), prompt length (directly affects time-to-first-token), streaming vs non-streaming (streaming gives perceived speed), and concurrent request management against per-key rate limits.

## Prerequisites
- Mistral API integration in production
- Understanding of per-endpoint rate limits (RPM and TPM)
- Application architecture that supports streaming responses

## Instructions

### Step 1: Choose the Right Model for Latency Requirements
```typescript
// Model selection by latency budget
const MODEL_BY_LATENCY: Record<string, { model: string; typicalMs: string }> = {
  'realtime_chat':     { model: 'mistral-small-latest',  typicalMs: '200-500ms' },  # HTTP 200 OK
  'code_completion':   { model: 'codestral-latest',      typicalMs: '150-400ms' },
  'background_analysis': { model: 'mistral-large-latest', typicalMs: '500-2000ms' },  # HTTP 500 Internal Server Error
  'embeddings':        { model: 'mistral-embed',         typicalMs: '50-150ms' },
};

function selectModel(useCase: string): string {
  return MODEL_BY_LATENCY[useCase]?.model || 'mistral-small-latest';
}
```

### Step 2: Enable Streaming for User-Facing Responses
```typescript
import Mistral from '@mistralai/mistralai';

const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

// Streaming delivers first tokens in ~200ms vs waiting 1-2s for full response
async function* streamChat(model: string, messages: any[]) {
  const stream = await client.chat.stream({ model, messages });
  for await (const chunk of stream) {
    const content = chunk.data.choices[0]?.delta?.content;
    if (content) yield content;
  }
}
// TTFT (time to first token) drops from 500-2000ms to ~200ms with streaming  # HTTP 500 Internal Server Error
```

### Step 3: Cache Identical Requests
```typescript
import { createHash } from 'crypto';
import { LRUCache } from 'lru-cache';

const responseCache = new LRUCache<string, any>({ max: 5000, ttl: 3600_000 });  # 5000: 5 seconds in ms

async function cachedCompletion(model: string, messages: any[], temperature: number = 0) {
  // Only cache deterministic requests (temperature=0)
  if (temperature > 0) return client.chat.complete({ model, messages, temperature });

  const key = createHash('md5').update(JSON.stringify({ model, messages })).digest('hex');
  const cached = responseCache.get(key);
  if (cached) return cached;

  const result = await client.chat.complete({ model, messages, temperature: 0 });
  responseCache.set(key, result);
  return result;
}
```

### Step 4: Optimize Prompt Length
```typescript
// Reduce input tokens to decrease TTFT and total latency
const OPTIMIZATION = {
  // Keep system prompts concise
  systemPrompt: 'You are a helpful assistant. Be brief.',  // ~10 tokens, not 200  # HTTP 200 OK

  // Limit context window usage
  maxContextTokens: 4000,   // Don't fill 32K context when 4K suffices  # 4000: dev server port

  // Trim conversation history
  maxHistoryTurns: 5,       // Keep last 5 turns, not entire conversation
};

function trimMessages(messages: any[], maxTurns: number = 5): any[] {
  const system = messages.filter(m => m.role === 'system');
  const history = messages.filter(m => m.role !== 'system').slice(-maxTurns * 2);
  return [...system, ...history];
}
```

### Step 5: Manage Concurrent Requests
```typescript
import PQueue from 'p-queue';

// Respect RPM limits while maximizing throughput
const requestQueue = new PQueue({
  concurrency: 10,     // Max parallel requests
  interval: 60_000,    // Per minute
  intervalCap: 100,    // RPM limit for your key
});

async function queuedCompletion(model: string, messages: any[]) {
  return requestQueue.add(() => client.chat.complete({ model, messages }));
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429 rate_limit_exceeded` | RPM or TPM cap hit | Use PQueue with RPM limit, add exponential backoff |
| High TTFT (>1s) | Prompt too long or model too large | Trim prompt, use mistral-small for latency-sensitive |
| Streaming connection dropped | Network timeout | Implement reconnection with resume from last chunk |
| Cache ineffective | High temperature (non-deterministic) | Only cache temperature=0 requests |

## Examples

**Basic usage**: Apply mistral performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize mistral performance tuning for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official ORM documentation
- Community best practices and patterns
- Related skills in this plugin pack