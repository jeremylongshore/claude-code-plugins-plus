# Groq Reference Architecture — Full Implementation

Complete, copy-ready TypeScript for every layer of the reference architecture.
Each section maps to a file in the `src/groq/` project structure. Implement them
in order — the router depends on the registry, the middleware and fallback depend
on the client, and the streaming pipeline stands alone.

## Project structure

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

## Step 1: Model Registry

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

## Step 2: Model Router

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

## Step 3: Middleware Layer

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

## Step 4: Fallback Chain

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

## Step 5: Streaming Pipeline

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
