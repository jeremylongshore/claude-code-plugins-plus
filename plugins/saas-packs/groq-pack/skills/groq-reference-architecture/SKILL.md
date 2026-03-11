---
name: groq-reference-architecture
description: |
  Implement Groq reference architecture with best-practice project layout.
  Use when designing new Groq integrations, reviewing project structure,
  or establishing architecture standards for Groq applications.
  Trigger with phrases like "groq architecture", "groq best practices",
  "groq project structure", "how to organize groq", "groq layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Groq Reference Architecture

## Overview
Production architecture for ultra-fast LLM inference with Groq LPU. Covers model routing by latency requirements, streaming pipelines, fallback strategies, and integration patterns for real-time AI applications.

## Prerequisites
- Groq API key
- `groq-sdk` npm package
- Understanding of model capabilities (Llama, Mixtral)
- Monitoring for latency and token usage

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                Application Layer                     │
│  Chat UI │ API Backend │ Batch Processor │ Agent    │
└──────────┬──────────────┬───────────────┬───────────┘
           │              │               │
           ▼              ▼               ▼
┌─────────────────────────────────────────────────────┐
│              Model Router                            │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Speed Tier    │  │ Quality Tier │  │ Long Ctx  │ │
│  │ llama-3.1-8b  │  │ llama-3.3-70b│  │ mixtral   │ │
│  │ (80ms TTFT)   │  │ (200ms TTFT) │  │ (32k ctx) │ │
│  └───────────────┘  └──────────────┘  └───────────┘ │
├─────────────────────────────────────────────────────┤
│              Middleware                               │
│  Prompt Cache │ Rate Limiter │ Token Counter │ Log  │
├─────────────────────────────────────────────────────┤
│              Fallback Layer                          │
│  Groq Primary → OpenAI Fallback → Local Model      │
└─────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Model Router Pattern
```typescript
import Groq from 'groq-sdk';

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

type ModelTier = 'speed' | 'quality' | 'long-context';

const MODEL_MAP: Record<ModelTier, string> = {
  speed: 'llama-3.1-8b-instant',
  quality: 'llama-3.3-70b-versatile',
  'long-context': 'mixtral-8x7b-32768',
};

function selectModel(options: {
  maxLatencyMs?: number;
  contextLength?: number;
  needsReasoning?: boolean;
}): string {
  if (options.contextLength && options.contextLength > 8192)
    return MODEL_MAP['long-context'];
  if (options.maxLatencyMs && options.maxLatencyMs < 150)
    return MODEL_MAP.speed;
  if (options.needsReasoning) return MODEL_MAP.quality;
  return MODEL_MAP.speed;
}
```

### Step 2: Completion Service with Middleware
```typescript
interface CompletionOptions {
  messages: any[];
  tier?: ModelTier;
  stream?: boolean;
  maxTokens?: number;
  temperature?: number;
}

async function complete(options: CompletionOptions) {
  const model = MODEL_MAP[options.tier || 'speed'];
  const start = performance.now();

  const response = await groq.chat.completions.create({
    model,
    messages: options.messages,
    stream: options.stream || false,
    max_tokens: options.maxTokens || 1024,
    temperature: options.temperature ?? 0.7,
  });

  const latency = performance.now() - start;
  logMetrics({ model, latency, tokens: response.usage });

  return response;
}
```

### Step 3: Streaming Pipeline
```typescript
async function* streamCompletion(messages: any[], tier: ModelTier = 'quality') {
  const model = MODEL_MAP[tier];

  const stream = await groq.chat.completions.create({
    model,
    messages,
    stream: true,
    max_tokens: 2048,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content;
    if (content) yield content;
  }
}

// Usage with Express SSE
app.get('/api/chat', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');

  for await (const token of streamCompletion(messages, 'quality')) {
    res.write(`data: ${JSON.stringify({ token })}\n\n`);
  }

  res.write('data: [DONE]\n\n');
  res.end();
});
```

### Step 4: Fallback Chain
```typescript
async function completionWithFallback(messages: any[]) {
  try {
    return await complete({ messages, tier: 'quality' });
  } catch (error: any) {
    if (error.status === 429 || error.status >= 500) {
      console.warn('Groq unavailable, falling back to OpenAI');
      return openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages,
      });
    }
    throw error;
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 rate limit | RPM/TPM exceeded | Implement queue with backoff |
| Model not available | Temporary outage | Use fallback chain to OpenAI |
| Context overflow | Input too long | Route to mixtral for 32k context |
| High latency | Wrong model tier | Use 8b-instant for latency-sensitive |

## Examples

### Multi-Model Pipeline
```typescript
async function analyzeDocument(doc: string) {
  // Fast extraction with speed tier
  const summary = await complete({
    messages: [{ role: 'user', content: `Summarize: ${doc}` }],
    tier: 'speed',
  });

  // Deep analysis with quality tier
  const analysis = await complete({
    messages: [{ role: 'user', content: `Analyze in detail: ${summary}` }],
    tier: 'quality',
  });

  return { summary, analysis };
}
```

## Resources
- [Groq API Documentation](https://console.groq.com/docs)
- [Groq Model Cards](https://console.groq.com/docs/models)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
