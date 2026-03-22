---
name: groq-reference-architecture
description: |
  Implement Groq reference architecture with model routing, streaming pipelines, and fallbacks.
  Use when designing new Groq integrations, reviewing project structure,
  or establishing architecture standards for Groq applications.
  Trigger with phrases like "groq architecture", "groq best practices",
  "groq project structure", "how to organize groq", "groq design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, groq-reference]

---
# Groq Reference Architecture

## Overview
Production architecture for applications built on Groq's LPU inference API. Covers model routing by latency requirements, streaming pipelines, multi-provider fallback, and the middleware layer that ties it together.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     Application Layer                         │
│  Chat UI  │  API Backend  │  Batch Processor  │  Agent       │
└─────┬─────┴──────┬────────┴────────┬──────────┴──────┬───────┘
      │            │                 │                 │
      ▼            ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────┐
│                    Groq Service Layer                         │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────────────┐   │
│  │ Model Router │  │ Middleware │  │ Fallback Chain      │   │
│  │             │  │            │  │                     │   │
│  │ speed →     │  │ Cache      │  │ Groq (primary)      │   │
│  │   8b-instant│  │ Rate Guard │  │   ↓ 429/5xx         │   │
│  │ quality →   │  │ Metrics    │  │ Groq (fallback model)│  │
│  │   70b-versa.│  │ Logging    │  │   ↓ still failing    │   │
│  │ vision →    │  │ Retry      │  │ OpenAI (backup)     │   │
│  │   llama-4   │  │            │  │   ↓ also failing     │   │
│  │ audio →     │  │            │  │ Graceful degrade    │   │
│  │   whisper   │  │            │  │                     │   │
│  └─────────────┘  └────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Project Structure
```
src/
├── groq/
│   ├── client.ts            # Singleton Groq client
│   ├── models.ts            # Model constants and capabilities
│   ├── router.ts            # Model selection logic
│   ├── middleware.ts         # Cache, rate limit, metrics
│   ├── fallback.ts          # Multi-provider fallback chain
│   └── types.ts             # Shared types
├── services/
│   ├── chat.ts              # Chat completion service
│   ├── transcription.ts     # Audio transcription (Whisper)
│   ├── extraction.ts        # Structured data extraction
│   └── batch.ts             # Batch processing service
└── api/
    ├── chat.ts              # HTTP endpoint
    ├── transcribe.ts        # Audio endpoint
    └── health.ts            # Health check
```

## Instructions

### Step 1: Model Registry
```typescript
// src/groq/models.ts
export interface ModelSpec {
  id: string;
  tier: "speed" | "quality" | "vision" | "audio";
  contextWindow: number;
  maxOutput: number;
  speedTokPerSec: number;
  inputCostPer1M: number;
  outputCostPer1M: number;
  capabilities: ("text" | "tools" | "json" | "vision" | "audio")[];
}

export const MODELS: Record<string, ModelSpec> = {
  "llama-3.1-8b-instant": {
    id: "llama-3.1-8b-instant",
    tier: "speed",
    contextWindow: 131_072,
    maxOutput: 8_192,
    speedTokPerSec: 560,
    inputCostPer1M: 0.05,
    outputCostPer1M: 0.08,
    capabilities: ["text", "tools", "json"],
  },
  "llama-3.3-70b-versatile": {
    id: "llama-3.3-70b-versatile",
    tier: "quality",
    contextWindow: 131_072,
    maxOutput: 32_768,
    speedTokPerSec: 280,
    inputCostPer1M: 0.59,
    outputCostPer1M: 0.79,
    capabilities: ["text", "tools", "json"],
  },
  "meta-llama/llama-4-scout-17b-16e-instruct": {
    id: "meta-llama/llama-4-scout-17b-16e-instruct",
    tier: "vision",
    contextWindow: 131_072,
    maxOutput: 8_192,
    speedTokPerSec: 460,
    inputCostPer1M: 0.11,
    outputCostPer1M: 0.34,
    capabilities: ["text", "tools", "json", "vision"],
  },
  "whisper-large-v3-turbo": {
    id: "whisper-large-v3-turbo",
    tier: "audio",
    contextWindow: 0,
    maxOutput: 0,
    speedTokPerSec: 0,
    inputCostPer1M: 0,
    outputCostPer1M: 0,
    capabilities: ["audio"],
  },
};
```

### Step 2: Model Router
```typescript
// src/groq/router.ts
import { MODELS, ModelSpec } from "./models";

interface RoutingRequest {
  maxLatencyMs?: number;
  needsVision?: boolean;
  needsTools?: boolean;
  needsJSON?: boolean;
  contextLength?: number;
  costSensitive?: boolean;
}

export function selectModel(req: RoutingRequest): ModelSpec {
  if (req.needsVision) return MODELS["meta-llama/llama-4-scout-17b-16e-instruct"];

  if (req.costSensitive || (req.maxLatencyMs && req.maxLatencyMs < 100)) {
    return MODELS["llama-3.1-8b-instant"];
  }

  if (req.needsTools || req.needsJSON) {
    return MODELS["llama-3.3-70b-versatile"];
  }

  // Default: speed tier
  return MODELS["llama-3.1-8b-instant"];
}
```

### Step 3: Middleware Layer
```typescript
// src/groq/middleware.ts
import Groq from "groq-sdk";
import { LRUCache } from "lru-cache";
import { createHash } from "crypto";

const cache = new LRUCache<string, any>({ max: 500, ttl: 10 * 60_000 });

export async function completionWithMiddleware(
  groq: Groq,
  model: string,
  messages: any[],
  options?: { maxTokens?: number; temperature?: number; stream?: boolean }
) {
  const temp = options?.temperature ?? 0.7;

  // Cache check (only for deterministic requests)
  if (temp === 0 && !options?.stream) {
    const key = createHash("sha256").update(JSON.stringify({ model, messages })).digest("hex");
    const cached = cache.get(key);
    if (cached) return cached;
  }

  // Metrics
  const start = performance.now();

  const response = await groq.chat.completions.create({
    model,
    messages,
    max_tokens: options?.maxTokens ?? 1024,
    temperature: temp,
    stream: options?.stream ?? false,
  });

  const latency = performance.now() - start;

  // Emit metrics
  emitMetrics({
    model,
    latencyMs: Math.round(latency),
    tokens: (response as any).usage?.total_tokens ?? 0,
    cached: false,
  });

  // Cache deterministic responses
  if (temp === 0 && !options?.stream) {
    const key = createHash("sha256").update(JSON.stringify({ model, messages })).digest("hex");
    cache.set(key, response);
  }

  return response;
}

function emitMetrics(data: any) {
  // Plug in your metrics system: Prometheus, Datadog, etc.
  console.log(`[groq-metrics] ${JSON.stringify(data)}`);
}
```

### Step 4: Fallback Chain
```typescript
// src/groq/fallback.ts
import Groq from "groq-sdk";

export async function completionWithFallback(
  groq: Groq,
  messages: any[],
  options?: { primaryModel?: string; maxTokens?: number }
) {
  const primary = options?.primaryModel || "llama-3.3-70b-versatile";
  const fallbackModel = "llama-3.1-8b-instant";

  // Attempt 1: Primary model
  try {
    return await groq.chat.completions.create({
      model: primary,
      messages,
      max_tokens: options?.maxTokens ?? 1024,
    });
  } catch (err: any) {
    if (err.status !== 429 && err.status < 500) throw err;
    console.warn(`Primary model ${primary} failed (${err.status}), trying fallback`);
  }

  // Attempt 2: Fallback model (different rate limit pool)
  try {
    return await groq.chat.completions.create({
      model: fallbackModel,
      messages,
      max_tokens: options?.maxTokens ?? 1024,
    });
  } catch (err: any) {
    console.warn(`Groq fallback also failed (${err.status})`);
  }

  // Attempt 3: Graceful degradation
  return {
    choices: [{
      message: {
        role: "assistant" as const,
        content: "Service temporarily unavailable. Please try again in a moment.",
      },
      finish_reason: "stop" as const,
    }],
    model: "fallback",
    usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
  };
}
```

### Step 5: Streaming Pipeline
```typescript
// src/groq/streaming.ts
import Groq from "groq-sdk";

export async function* streamCompletion(
  groq: Groq,
  messages: any[],
  model = "llama-3.3-70b-versatile"
): AsyncGenerator<{ type: "token" | "done" | "error"; content?: string; error?: string }> {
  try {
    const stream = await groq.chat.completions.create({
      model,
      messages,
      stream: true,
      max_tokens: 2048,
    });

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content;
      if (content) yield { type: "token", content };
    }

    yield { type: "done" };
  } catch (err: any) {
    yield { type: "error", error: err.message };
  }
}
```

## Integration Patterns

| Pattern | When to Use | Groq Feature |
|---------|-------------|-------------|
| Direct completion | Simple request/response | `chat.completions.create` |
| Streaming SSE | Real-time chat UI | `stream: true` |
| Tool calling | Agent with function execution | `tools` parameter |
| JSON extraction | Structured data from text | `response_format: json_object` |
| Batch processing | High-volume document processing | Queue + rate limiting |
| Audio transcription | Voice input | `audio.transcriptions.create` |
| Vision analysis | Image understanding | Llama 4 Scout/Maverick |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 on primary model | RPM/TPM exceeded | Fall back to different model |
| High latency | Wrong model tier | Route to `8b-instant` for latency-critical paths |
| Context overflow | Input > 128K tokens | Truncate or chunk input |
| Vision errors | Wrong model for images | Use Llama 4 Scout full model path |

## Resources
- [Groq API Documentation](https://console.groq.com/docs)
- [Groq Models](https://console.groq.com/docs/models)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Pricing](https://groq.com/pricing)

## Next Steps
For multi-environment deployment, see `groq-multi-env-setup`.
