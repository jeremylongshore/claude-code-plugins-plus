---
name: together-rate-limits
description: 'Together AI rate limits for inference, fine-tuning, and model deployment.

  Use when working with Together AI''s OpenAI-compatible API.

  Trigger: "together rate limits".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- ai
- inference
- together
compatibility: Designed for Claude Code
---
# Together AI Rate Limits

## Overview

Together AI's OpenAI-compatible inference API enforces per-key rate limits that vary by model tier and operation type. Chat completions and embeddings share a global request quota, while fine-tuning jobs and batch inference have separate concurrency caps. High-throughput workloads like embedding entire document corpora or running evaluations across 100+ prompts require client-side token bucket limiting. Together's batch inference endpoint offers 50% cost savings but has its own queue depth limits that differ from real-time inference.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Chat completions | 600 req | 1 minute | Per API key |
| Embeddings | 300 req | 1 minute | Per API key |
| Image generation (FLUX) | 60 req | 1 minute | Per API key |
| Fine-tune jobs (concurrent) | 3 jobs | Rolling | Per API key |
| Batch inference | 100 req/batch, 10 batches | Rolling | Per API key |

## Rate Limiter Implementation

```typescript
class TogetherRateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly max: number;
  private readonly refillRate: number;
  private queue: Array<{ resolve: () => void }> = [];

  constructor(maxPerMinute: number) {
    this.max = maxPerMinute;
    this.tokens = maxPerMinute;
    this.lastRefill = Date.now();
    this.refillRate = maxPerMinute / 60_000;
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens >= 1) { this.tokens -= 1; return; }
    return new Promise(resolve => this.queue.push({ resolve }));
  }

  private refill() {
    const now = Date.now();
    this.tokens = Math.min(this.max, this.tokens + (now - this.lastRefill) * this.refillRate);
    this.lastRefill = now;
    while (this.tokens >= 1 && this.queue.length) {
      this.tokens -= 1;
      this.queue.shift()!.resolve();
    }
  }
}

const chatLimiter = new TogetherRateLimiter(500);  // buffer under 600
const embedLimiter = new TogetherRateLimiter(250);
```

## Retry Strategy

```typescript
async function togetherRetry<T>(
  limiter: TogetherRateLimiter, fn: () => Promise<Response>, maxRetries = 4
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await limiter.acquire();
    const res = await fn();
    if (res.ok) return res.json();
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "5", 10);
      const jitter = Math.random() * 2000;
      await new Promise(r => setTimeout(r, retryAfter * 1000 + jitter));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
      continue;
    }
    throw new Error(`Together API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchEmbedDocuments(texts: string[], model: string, batchSize = 20) {
  const results: any[] = [];
  for (let i = 0; i < texts.length; i += batchSize) {
    const batch = texts.slice(i, i + batchSize);
    const result = await togetherRetry(embedLimiter, () =>
      fetch("https://api.together.xyz/v1/embeddings", {
        method: "POST", headers,
        body: JSON.stringify({ model, input: batch }),
      })
    );
    results.push(result);
    if (i + batchSize < texts.length) await new Promise(r => setTimeout(r, 3000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on chat completions | Exceeded 600 req/min key limit | Use token bucket, avoid burst patterns |
| 429 on embeddings | Embedding limit is half of chat | Batch inputs (up to 20 texts per request) |
| Model not found | Wrong model ID string | Verify with `GET /v1/models` endpoint |
| 503 model overloaded | Popular model at peak demand | Retry with backoff, or use fallback model |
| Fine-tune 409 | 3 concurrent job limit reached | Wait for running job to complete first |

## Resources

- [Together AI Documentation](https://docs.together.ai/)
- [API Reference](https://docs.together.ai/reference/chat-completions-1)
- [Model List](https://docs.together.ai/docs/inference-models)

## Next Steps

See `together-performance-tuning`.
