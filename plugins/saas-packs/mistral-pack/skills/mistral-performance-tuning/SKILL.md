---
name: mistral-performance-tuning
description: |
  Optimize Mistral AI performance with caching, batching, and latency reduction.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Mistral AI integrations.
  Trigger with phrases like "mistral performance", "optimize mistral",
  "mistral latency", "mistral caching", "mistral slow".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, api, performance]

---
# Mistral AI Performance Tuning

## Overview
Optimize Mistral AI API response times and throughput. Key levers: model selection (Mistral Small ~200ms TTFT vs Large ~500ms), prompt length (fewer tokens = faster), streaming (perceived speed), caching (zero-latency repeats), and concurrent request management.

## Prerequisites
- Mistral API integration in production
- Understanding of RPM/TPM limits for your tier
- Application architecture supporting streaming

## Instructions

### Step 1: Model Selection by Latency Budget

```typescript
const MODELS_BY_USE_CASE: Record<string, { model: string; ttftMs: string; note: string }> = {
  realtime_chat:     { model: 'mistral-small-latest',  ttftMs: '~200ms',  note: '256k ctx, cheapest' },
  code_completion:   { model: 'codestral-latest',      ttftMs: '~150ms',  note: 'Optimized for code + FIM' },
  code_agents:       { model: 'devstral-latest',       ttftMs: '~300ms',  note: 'Agentic coding tasks' },
  reasoning:         { model: 'mistral-large-latest',  ttftMs: '~500ms',  note: '256k ctx, strongest' },
  vision:            { model: 'pixtral-large-latest',  ttftMs: '~600ms',  note: 'Image + text multimodal' },
  embeddings:        { model: 'mistral-embed',         ttftMs: '~50ms',   note: '1024-dim, batch-friendly' },
  edge_devices:      { model: 'ministral-latest',      ttftMs: '~100ms',  note: '3B-14B, fastest' },
};
```

### Step 2: Streaming for User-Facing Responses

Streaming reduces perceived latency from 1-2s (full response) to ~200ms (first token):

```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

async function* streamChat(messages: any[], model = 'mistral-small-latest') {
  const stream = await client.chat.stream({ model, messages });
  for await (const chunk of stream) {
    const content = chunk.data?.choices?.[0]?.delta?.content;
    if (content) yield content;
  }
}

// Web Response with SSE
function streamToSSE(messages: any[]): Response {
  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      for await (const text of streamChat(messages)) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text })}\n\n`));
      }
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    },
  });
  return new Response(readable, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
  });
}
```

### Step 3: Response Caching

```typescript
import { createHash } from 'crypto';
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, any>({
  max: 5000,
  ttl: 3_600_000, // 1 hour
});

async function cachedChat(
  messages: any[],
  model: string,
  temperature = 0,
): Promise<any> {
  // Only cache deterministic requests
  if (temperature > 0) {
    return client.chat.complete({ model, messages, temperature });
  }

  const key = createHash('sha256')
    .update(JSON.stringify({ model, messages }))
    .digest('hex');

  const cached = cache.get(key);
  if (cached) {
    console.debug('Cache HIT');
    return cached;
  }

  const result = await client.chat.complete({ model, messages, temperature: 0 });
  cache.set(key, result);
  return result;
}
```

### Step 4: Prompt Length Optimization

```typescript
// Shorter prompts = faster TTFT and lower cost
function optimizePrompt(systemPrompt: string, maxChars = 500): string {
  return systemPrompt
    .replace(/\s+/g, ' ')        // Collapse whitespace
    .replace(/\n\s*\n/g, '\n')   // Remove blank lines
    .trim()
    .slice(0, maxChars);
}

// Trim conversation history to last N turns
function trimHistory(messages: any[], maxTurns = 10): any[] {
  const system = messages.filter(m => m.role === 'system');
  const history = messages.filter(m => m.role !== 'system').slice(-maxTurns * 2);
  return [...system, ...history];
}

// Impact: Reducing from 4000 to 500 input tokens saves ~50% TTFT
```

### Step 5: Concurrent Request Queue

```typescript
import PQueue from 'p-queue';

// Match concurrency to your workspace RPM limit
const queue = new PQueue({
  concurrency: 10,
  interval: 60_000,
  intervalCap: 100, // RPM limit
});

async function queuedChat(messages: any[], model = 'mistral-small-latest') {
  return queue.add(() => client.chat.complete({ model, messages }));
}

// Process 100 requests respecting RPM
const prompts = Array.from({ length: 100 }, (_, i) => `Question ${i}`);
const results = await Promise.all(
  prompts.map(p => queuedChat([{ role: 'user', content: p }]))
);
```

### Step 6: Batch API for Non-Realtime Workloads

Use Batch API for 50% cost savings when latency is not critical:

```typescript
// Batch API processes requests asynchronously (minutes to hours)
// Supports: /v1/chat/completions, /v1/embeddings, /v1/fim/completions, /v1/moderations
// See mistral-webhooks-events for full batch implementation
```

### Step 7: FIM (Fill-in-the-Middle) for Code

```typescript
// Codestral supports FIM — faster than full chat for code completion
const response = await client.fim.complete({
  model: 'codestral-latest',
  prompt: 'function fibonacci(n) {\n  if (n <= 1) return n;\n',
  suffix: '\n}\n',
  maxTokens: 100,
});
// Returns just the middle part — minimal tokens, minimal latency
```

## Performance Benchmarks

| Optimization | Typical Impact |
|-------------|----------------|
| mistral-small vs mistral-large | 2-4x faster TTFT |
| Streaming vs non-streaming | 5-10x perceived speed |
| Response caching (temp=0) | 100x faster (cache hit) |
| Prompt trimming (4k to 500 tokens) | 30-50% faster TTFT |
| Batch API | Not faster, but 50% cheaper |
| FIM vs chat for code | 2-3x fewer tokens |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429 rate_limit_exceeded` | RPM/TPM cap hit | Use PQueue with interval cap |
| High TTFT (>1s) | Prompt too long or large model | Trim prompt, use mistral-small |
| Stream disconnected | Network timeout | Implement reconnection |
| Cache thrashing | High cardinality prompts | Increase cache size or reduce TTL |

## Resources
- [Models Overview](https://docs.mistral.ai/getting-started/models/)
- [Batch Inference](https://docs.mistral.ai/capabilities/batch/)
- [FIM/Code Generation](https://docs.mistral.ai/capabilities/code_generation/)
- [Pricing](https://docs.mistral.ai/deployment/laplateforme/pricing/)

## Output
- Model selection optimized for latency requirements
- Streaming endpoints for perceived speed
- LRU response cache for deterministic requests
- Prompt optimization reducing token count
- Concurrent request queue respecting RPM limits
