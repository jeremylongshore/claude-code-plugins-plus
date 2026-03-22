---
name: groq-performance-tuning
description: |
  Optimize Groq API performance with model selection, caching, streaming, and parallel requests.
  Use when experiencing slow responses, implementing caching strategies,
  or optimizing request throughput for Groq integrations.
  Trigger with phrases like "groq performance", "optimize groq",
  "groq latency", "groq caching", "groq slow", "groq speed".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, api, performance]

---
# Groq Performance Tuning

## Overview
Maximize Groq's LPU inference speed advantage. Groq already delivers extreme throughput (280-560 tok/s) and low latency (<200ms TTFT), but client-side optimization -- model selection, prompt size, streaming, caching, and parallelism -- determines whether your application fully exploits that speed.

## Groq Speed Benchmarks

| Model | TTFT | Throughput | Context |
|-------|------|-----------|---------|
| `llama-3.1-8b-instant` | ~50ms | ~560 tok/s | 128K |
| `llama-3.3-70b-versatile` | ~150ms | ~280 tok/s | 128K |
| `llama-3.3-70b-specdec` | ~100ms | ~400 tok/s | 128K |
| `meta-llama/llama-4-scout-17b-16e-instruct` | ~80ms | ~460 tok/s | 128K |

TTFT = Time to First Token. Actual values depend on prompt size and server load.

## Instructions

### Step 1: Choose the Right Model for Speed
```typescript
import Groq from "groq-sdk";

const groq = new Groq();

// Speed tiers for different use cases
const SPEED_MAP = {
  // Under 100ms TTFT -- use for latency-critical paths
  instant: "llama-3.1-8b-instant",
  // Under 200ms TTFT -- use for quality-sensitive paths
  balanced: "llama-3.3-70b-versatile",
  // Speculative decoding -- same quality as 70b, faster throughput
  fast70b: "llama-3.3-70b-specdec",
} as const;

type SpeedTier = keyof typeof SPEED_MAP;

async function tieredCompletion(prompt: string, tier: SpeedTier = "instant") {
  return groq.chat.completions.create({
    model: SPEED_MAP[tier],
    messages: [{ role: "user", content: prompt }],
    temperature: 0,        // Deterministic = cacheable
    max_tokens: 256,       // Only request what you need
  });
}
```

### Step 2: Minimize Token Count
```typescript
// Groq charges per token AND rate limits on TPM
// Smaller prompts = faster responses + less quota usage

// BAD: verbose system prompt (200+ tokens)
const verbosePrompt = "You are an AI assistant that classifies text. Given a piece of text, analyze it carefully and determine whether the sentiment is positive, negative, or neutral. Consider the tone, word choice, and overall message...";

// GOOD: concise system prompt (15 tokens)
const concisePrompt = "Classify as positive/negative/neutral. One word only.";

// BAD: high max_tokens for short expected output
const wasteful = { max_tokens: 4096 }; // for a one-word response

// GOOD: match max_tokens to expected output
const efficient = { max_tokens: 5 };   // "positive" is 1 token
```

### Step 3: Streaming for Perceived Performance
```typescript
async function streamWithMetrics(
  messages: any[],
  onToken: (token: string) => void
): Promise<{ content: string; ttftMs: number; totalMs: number; tokPerSec: number }> {
  const start = performance.now();
  let ttft = 0;
  let content = "";
  let tokenCount = 0;

  const stream = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages,
    stream: true,
    max_tokens: 1024,
  });

  for await (const chunk of stream) {
    const token = chunk.choices[0]?.delta?.content || "";
    if (token) {
      if (!ttft) ttft = performance.now() - start;
      content += token;
      tokenCount++;
      onToken(token);
    }
  }

  const totalMs = performance.now() - start;
  return {
    content,
    ttftMs: Math.round(ttft),
    totalMs: Math.round(totalMs),
    tokPerSec: Math.round(tokenCount / (totalMs / 1000)),
  };
}
```

### Step 4: Semantic Prompt Cache
```typescript
import { LRUCache } from "lru-cache";
import { createHash } from "crypto";

const promptCache = new LRUCache<string, string>({
  max: 1000,
  ttl: 10 * 60_000,  // 10 min TTL for deterministic responses
});

function hashRequest(messages: any[], model: string): string {
  return createHash("sha256")
    .update(JSON.stringify({ messages, model }))
    .digest("hex");
}

async function cachedCompletion(
  messages: any[],
  model = "llama-3.1-8b-instant"
): Promise<string> {
  const key = hashRequest(messages, model);
  const cached = promptCache.get(key);
  if (cached) return cached;

  const response = await groq.chat.completions.create({
    model,
    messages,
    temperature: 0,  // Cache only works with deterministic output
  });

  const result = response.choices[0].message.content!;
  promptCache.set(key, result);
  return result;
}
```

### Step 5: Parallel Request Orchestration
```typescript
import PQueue from "p-queue";

// Respect RPM limits while maximizing throughput
const queue = new PQueue({
  concurrency: 10,
  intervalCap: 25,
  interval: 60_000,
});

async function parallelCompletions(
  prompts: string[],
  model = "llama-3.1-8b-instant"
): Promise<string[]> {
  const results = await Promise.all(
    prompts.map((prompt) =>
      queue.add(() =>
        cachedCompletion(
          [{ role: "user", content: prompt }],
          model
        )
      )
    )
  );
  return results as string[];
}
```

### Step 6: Latency Benchmarking
```typescript
async function benchmarkModels(prompt: string, iterations = 3) {
  const models = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "llama-3.3-70b-specdec",
  ];

  for (const model of models) {
    const latencies: number[] = [];
    const speeds: number[] = [];

    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const result = await groq.chat.completions.create({
        model,
        messages: [{ role: "user", content: prompt }],
        max_tokens: 100,
      });
      const elapsed = performance.now() - start;
      latencies.push(elapsed);
      const tps = result.usage!.completion_tokens /
        ((result.usage as any).completion_time || elapsed / 1000);
      speeds.push(tps);
    }

    const avgLatency = latencies.reduce((a, b) => a + b) / latencies.length;
    const avgSpeed = speeds.reduce((a, b) => a + b) / speeds.length;
    console.log(
      `${model.padEnd(45)} | ${avgLatency.toFixed(0)}ms avg | ${avgSpeed.toFixed(0)} tok/s avg`
    );
  }
}
```

## Performance Decision Matrix

| Scenario | Model | max_tokens | stream | cache |
|----------|-------|-----------|--------|-------|
| Classification | 8b-instant | 5 | No | Yes |
| Chat response | 70b-versatile | 1024 | Yes | No |
| Data extraction | 8b-instant | 200 | No | Yes |
| Code generation | 70b-versatile | 2048 | Yes | No |
| Bulk processing | 8b-instant | 256 | No | Yes |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High TTFT | Using 70b for simple tasks | Switch to `llama-3.1-8b-instant` |
| Rate limit (429) | Over RPM or TPM | Use queue with interval limiting |
| Stream disconnect | Network timeout | Implement reconnection with partial content |
| Token overflow | max_tokens too high | Set to expected output size |
| Cache miss rate high | Unique prompts | Normalize prompts, use template patterns |

## Resources
- [Groq Models & Speed](https://console.groq.com/docs/models)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [lru-cache on npm](https://www.npmjs.com/package/lru-cache)

## Next Steps
For cost optimization, see `groq-cost-tuning`.
