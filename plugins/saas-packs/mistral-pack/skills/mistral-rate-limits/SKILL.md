---
name: mistral-rate-limits
description: |
  Implement Mistral AI rate limiting, backoff, and request management.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Mistral AI.
  Trigger with phrases like "mistral rate limit", "mistral throttling",
  "mistral 429", "mistral retry", "mistral backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, api]

---
# Mistral Rate Limits

## Overview
Rate limit management for Mistral AI API. Mistral enforces per-workspace RPM (requests/minute) and TPM (tokens/minute) limits that vary by usage tier (Experiment free tier vs Scale pay-as-you-go). View your workspace limits at [admin.mistral.ai/plateforme/limits](https://admin.mistral.ai/plateforme/limits).

## Prerequisites
- Mistral API key configured
- Understanding of workspace tier (Experiment vs Scale)
- Application with retry infrastructure

## Mistral Rate Limit Architecture

Limits are set at the **workspace** level, not per key. All API keys in a workspace share the same RPM/TPM budget.

| Endpoint | What's limited |
|----------|---------------|
| `/v1/chat/completions` | RPM + TPM (input + output) |
| `/v1/embeddings` | RPM + TPM (input only) |
| `/v1/fim/completions` | RPM + TPM |
| `/v1/moderations` | RPM |

**Headers returned on every response:**
- `x-ratelimit-limit-requests` — your RPM cap
- `x-ratelimit-remaining-requests` — remaining RPM
- `x-ratelimit-limit-tokens` — your TPM cap
- `x-ratelimit-remaining-tokens` — remaining TPM
- `Retry-After` — seconds to wait (on 429 only)

## Instructions

### Step 1: Token-Aware Rate Limiter

```typescript
class MistralRateLimiter {
  private requestTimes: number[] = [];
  private tokenBuckets: Array<{ time: number; tokens: number }> = [];
  private readonly rpm: number;
  private readonly tpm: number;

  constructor(rpm: number, tpm: number) {
    this.rpm = rpm;
    this.tpm = tpm;
  }

  async waitIfNeeded(estimatedTokens: number): Promise<void> {
    const now = Date.now();
    const windowStart = now - 60_000;

    // Prune old entries
    this.requestTimes = this.requestTimes.filter(t => t > windowStart);
    this.tokenBuckets = this.tokenBuckets.filter(b => b.time > windowStart);

    // Check RPM
    if (this.requestTimes.length >= this.rpm) {
      const waitMs = this.requestTimes[0] - windowStart + 100;
      console.warn(`RPM limit (${this.rpm}), waiting ${waitMs}ms`);
      await new Promise(r => setTimeout(r, waitMs));
    }

    // Check TPM
    const currentTPM = this.tokenBuckets.reduce((sum, b) => sum + b.tokens, 0);
    if (currentTPM + estimatedTokens > this.tpm) {
      const waitMs = this.tokenBuckets[0].time - windowStart + 100;
      console.warn(`TPM limit (${this.tpm}), waiting ${waitMs}ms`);
      await new Promise(r => setTimeout(r, waitMs));
    }

    this.requestTimes.push(Date.now());
  }

  recordUsage(tokens: number): void {
    this.tokenBuckets.push({ time: Date.now(), tokens });
  }
}
```

### Step 2: Retry with Retry-After Header

```typescript
import { Mistral } from '@mistralai/mistralai';

async function chatWithRetry(
  client: Mistral,
  params: { model: string; messages: any[] },
  maxRetries = 5,
): Promise<any> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await client.chat.complete(params);
    } catch (error: any) {
      if (error.status !== 429 || attempt === maxRetries) throw error;

      // Respect Retry-After header from Mistral
      const retryAfter = error.headers?.get?.('retry-after');
      const waitSec = retryAfter ? parseInt(retryAfter) : Math.min(2 ** attempt, 60);
      console.warn(`429 — retrying in ${waitSec}s (attempt ${attempt + 1}/${maxRetries})`);
      await new Promise(r => setTimeout(r, waitSec * 1000));
    }
  }
}
```

### Step 3: Rate-Limited Client Wrapper

```typescript
const limiter = new MistralRateLimiter(100, 500_000);
const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

async function rateLimitedChat(messages: any[], model = 'mistral-small-latest') {
  const estimatedTokens = messages.reduce(
    (sum, m) => sum + Math.ceil((m.content?.length ?? 0) / 4), 0
  );

  await limiter.waitIfNeeded(estimatedTokens);
  const response = await client.chat.complete({ model, messages });

  if (response.usage) {
    limiter.recordUsage(
      (response.usage.promptTokens ?? 0) + (response.usage.completionTokens ?? 0)
    );
  }
  return response;
}
```

### Step 4: Model Fallback for Throughput

```typescript
class ModelRouter {
  private limiters: Record<string, MistralRateLimiter>;

  constructor() {
    this.limiters = {
      'mistral-large-latest': new MistralRateLimiter(30, 200_000),
      'mistral-small-latest': new MistralRateLimiter(120, 500_000),
    };
  }

  async chat(messages: any[], preferred = 'mistral-large-latest') {
    try {
      return await rateLimitedChat(messages, preferred);
    } catch (error: any) {
      if (error.status === 429 && preferred !== 'mistral-small-latest') {
        console.warn(`Falling back to mistral-small-latest`);
        return rateLimitedChat(messages, 'mistral-small-latest');
      }
      throw error;
    }
  }
}
```

### Step 5: Batch Embedding with Rate Awareness

```python
import time
from mistralai import Mistral

def batch_embed(client: Mistral, texts: list[str], batch_size: int = 32) -> list:
    """Batch embed with automatic rate limiting."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            response = client.embeddings.create(
                model="mistral-embed", inputs=batch
            )
            all_embeddings.extend([d.embedding for d in response.data])
        except Exception as e:
            if hasattr(e, "status_code") and e.status_code == 429:
                time.sleep(10)
                response = client.embeddings.create(
                    model="mistral-embed", inputs=batch
                )
                all_embeddings.extend([d.embedding for d in response.data])
            else:
                raise
    return all_embeddings
```

### Step 6: Usage Dashboard

```typescript
function rateLimitStatus(limiter: MistralRateLimiter) {
  const now = Date.now();
  const windowStart = now - 60_000;
  const activeRequests = limiter['requestTimes'].filter(t => t > windowStart).length;
  const activeTokens = limiter['tokenBuckets']
    .filter(b => b.time > windowStart)
    .reduce((sum, b) => sum + b.tokens, 0);

  return {
    rpm: { used: activeRequests, limit: limiter['rpm'], pct: (activeRequests / limiter['rpm'] * 100).toFixed(1) },
    tpm: { used: activeTokens, limit: limiter['tpm'], pct: (activeTokens / limiter['tpm'] * 100).toFixed(1) },
  };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429` errors | Exceeded RPM or TPM | Use rate limiter + exponential backoff |
| Inconsistent limits | All keys share workspace budget | Coordinate across services |
| Batch failures | Too many tokens per batch | Reduce batch size for embeddings |
| Spike traffic blocked | No request smoothing | Queue requests, spread over window |

## Resources
- [Rate Limits & Usage Tiers](https://docs.mistral.ai/deployment/ai-studio/tier/)
- [Pricing](https://docs.mistral.ai/deployment/laplateforme/pricing/)
- [Batch Inference](https://docs.mistral.ai/capabilities/batch/) — 50% cheaper, no rate limits

## Output
- Token-aware rate limiter with RPM + TPM tracking
- Retry logic respecting Retry-After headers
- Model fallback routing for throughput
- Rate limit dashboard for monitoring
