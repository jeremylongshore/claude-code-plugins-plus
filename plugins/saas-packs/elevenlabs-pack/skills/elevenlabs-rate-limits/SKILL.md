---
name: elevenlabs-rate-limits
description: |
  Implement ElevenLabs rate limiting, concurrency queuing, and backoff patterns.
  Use when handling 429 errors, implementing retry logic,
  or managing concurrent TTS request throughput.
  Trigger: "elevenlabs rate limit", "elevenlabs throttling",
  "elevenlabs 429", "elevenlabs retry", "elevenlabs backoff",
  "elevenlabs concurrent requests".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, rate-limits, reliability]
compatible-with: claude-code
---

# ElevenLabs Rate Limits

## Overview

Handle ElevenLabs rate limits with plan-aware concurrency queuing, exponential backoff, and quota monitoring. ElevenLabs uses two rate limit mechanisms: concurrent request limits (per plan) and system-level throttling.

## Prerequisites

- ElevenLabs SDK installed
- Understanding of your subscription plan's limits
- `p-queue` package (recommended): `npm install p-queue`

## Instructions

### Step 1: Understand the Two 429 Error Types

ElevenLabs returns HTTP 429 for two different reasons:

| 429 Variant | Response Body | Cause | Strategy |
|-------------|--------------|-------|----------|
| `too_many_concurrent_requests` | `{"detail":{"status":"too_many_concurrent_requests"}}` | Exceeded plan concurrency | Queue requests, don't backoff |
| `system_busy` | `{"detail":{"status":"system_busy"}}` | Server overload | Exponential backoff |

### Step 2: Plan Concurrency Limits

| Plan | Max Concurrent Requests | Characters/Month |
|------|------------------------|-------------------|
| Free | 2 | 10,000 |
| Starter | 3 | 30,000 |
| Creator | 5 | 100,000 |
| Pro | 10 | 500,000 |
| Scale | 15 | 2,000,000 |
| Business | 15 | Custom |

### Step 3: Concurrency-Aware Request Queue

```typescript
// src/elevenlabs/rate-limiter.ts
import PQueue from "p-queue";

type ElevenLabsPlan = "free" | "starter" | "creator" | "pro" | "scale" | "business";

const CONCURRENCY_LIMITS: Record<ElevenLabsPlan, number> = {
  free: 2,
  starter: 3,
  creator: 5,
  pro: 10,
  scale: 15,
  business: 15,
};

export function createRequestQueue(plan: ElevenLabsPlan) {
  const concurrency = CONCURRENCY_LIMITS[plan];

  const queue = new PQueue({
    concurrency,
    // Each queued request adds ~50ms to response time
    // so keep queue depth reasonable
    timeout: 120_000,  // 2 minute timeout per request
    throwOnTimeout: true,
  });

  queue.on("error", (error) => {
    console.error("[ElevenLabs Queue] Request failed:", error.message);
  });

  return queue;
}

// Usage
const queue = createRequestQueue("pro"); // 10 concurrent

async function generateWithQueue(voiceId: string, text: string) {
  return queue.add(async () => {
    return client.textToSpeech.convert(voiceId, {
      text,
      model_id: "eleven_flash_v2_5",
    });
  });
}

// All 20 requests run with max 10 concurrent
const results = await Promise.all(
  texts.map(text => generateWithQueue("21m00Tcm4TlvDq8ikWAM", text))
);
```

### Step 4: Exponential Backoff for system_busy

```typescript
// src/elevenlabs/backoff.ts
export async function withBackoff<T>(
  operation: () => Promise<T>,
  config = {
    maxRetries: 5,
    baseDelayMs: 1000,
    maxDelayMs: 32_000,
    jitterMs: 500,
  }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const status = error.statusCode || error.status;
      const errorType = error.body?.detail?.status;

      // Don't retry non-retryable errors
      if (status === 401 || status === 400 || status === 404) throw error;

      // For concurrent limit, retry immediately (queue handles spacing)
      if (errorType === "too_many_concurrent_requests") {
        if (attempt === config.maxRetries) throw error;
        // Short pause — the queue is managing concurrency
        await new Promise(r => setTimeout(r, 50 * (attempt + 1)));
        continue;
      }

      // For system_busy or 5xx, exponential backoff with jitter
      if (attempt === config.maxRetries) throw error;

      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.jitterMs;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      console.warn(`[ElevenLabs] ${errorType || status}. Retry ${attempt + 1}/${config.maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 5: Quota Monitor

```typescript
// src/elevenlabs/quota-monitor.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

export class QuotaMonitor {
  private characterCount = 0;
  private characterLimit = 0;
  private lastCheck = 0;

  constructor(
    private client: ElevenLabsClient,
    private warningThresholdPct = 80,
    private checkIntervalMs = 60_000
  ) {}

  async check(): Promise<{
    used: number;
    limit: number;
    remaining: number;
    pctUsed: number;
    warning: boolean;
  }> {
    const now = Date.now();
    if (now - this.lastCheck > this.checkIntervalMs) {
      const user = await this.client.user.get();
      this.characterCount = user.subscription.character_count;
      this.characterLimit = user.subscription.character_limit;
      this.lastCheck = now;
    }

    const remaining = this.characterLimit - this.characterCount;
    const pctUsed = (this.characterCount / this.characterLimit) * 100;

    return {
      used: this.characterCount,
      limit: this.characterLimit,
      remaining,
      pctUsed: Math.round(pctUsed * 10) / 10,
      warning: pctUsed >= this.warningThresholdPct,
    };
  }

  async guardRequest(textLength: number): Promise<void> {
    const quota = await this.check();
    if (textLength > quota.remaining) {
      throw new Error(
        `Insufficient quota: need ${textLength} chars, have ${quota.remaining} remaining (${quota.pctUsed}% used)`
      );
    }
    if (quota.warning) {
      console.warn(`[ElevenLabs] Quota warning: ${quota.pctUsed}% used (${quota.remaining} chars remaining)`);
    }
  }
}
```

### Step 6: Combined Rate-Limited Client

```typescript
// src/elevenlabs/resilient-client.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createRequestQueue } from "./rate-limiter";
import { withBackoff } from "./backoff";
import { QuotaMonitor } from "./quota-monitor";

export function createResilientClient(plan: "free" | "starter" | "creator" | "pro" | "scale" = "pro") {
  const client = new ElevenLabsClient({ maxRetries: 0 }); // We handle retries
  const queue = createRequestQueue(plan);
  const quota = new QuotaMonitor(client);

  return {
    async generateSpeech(voiceId: string, text: string, modelId = "eleven_multilingual_v2") {
      await quota.guardRequest(text.length);

      return queue.add(() =>
        withBackoff(() =>
          client.textToSpeech.convert(voiceId, {
            text,
            model_id: modelId,
          })
        )
      );
    },

    getQueueStats() {
      return {
        pending: queue.pending,
        size: queue.size,
      };
    },

    checkQuota: () => quota.check(),
  };
}
```

## Model Cost Impact on Quota

| Model | Credits per Character | 10,000 Chars Cost |
|-------|-----------------------|-------------------|
| `eleven_v3` | 1.0 | 10,000 credits |
| `eleven_multilingual_v2` | 1.0 | 10,000 credits |
| `eleven_flash_v2_5` | 0.5 | 5,000 credits |
| `eleven_turbo_v2_5` | 0.5 | 5,000 credits |

Use Flash/Turbo models during development to conserve quota.

## Error Handling

| Scenario | Detection | Response |
|----------|-----------|----------|
| Concurrent limit hit | 429 + `too_many_concurrent_requests` | Queue; retry after ~50ms per queued request |
| System busy | 429 + `system_busy` | Exponential backoff (1s, 2s, 4s, 8s...) |
| Quota exhausted | 401 + `quota_exceeded` | Stop requests; alert; wait for reset |
| Server error | 500-599 | Exponential backoff; max 5 retries |

## Resources

- [ElevenLabs Rate Limits Help](https://help.elevenlabs.io/hc/en-us/articles/19571824571921)
- [ElevenLabs Pricing](https://elevenlabs.io/pricing)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `elevenlabs-security-basics`.
