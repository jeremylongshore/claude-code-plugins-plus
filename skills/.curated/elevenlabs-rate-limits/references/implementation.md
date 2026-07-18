# ElevenLabs Rate Limiting — Full Implementation

Complete, copy-ready implementation of the four building blocks referenced from
`SKILL.md`: a concurrency-aware request queue, exponential backoff for
`system_busy`, a quota monitor, and a combined resilient client that composes all
three.

## Building Block 1: Concurrency-Aware Request Queue

Queue requests so you never exceed your plan's concurrent-request ceiling. This is
the correct response to `too_many_concurrent_requests` — queue, do **not** back off.

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

## Building Block 2: Exponential Backoff for system_busy

Back off with jitter when the server is overloaded (`system_busy` or 5xx). Never
back off for auth/validation errors (401/400/404) — those will never succeed on
retry.

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

## Building Block 3: Quota Monitor

Track character usage against your plan's monthly limit, warn at a configurable
threshold, and guard a request before it burns quota you don't have.

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

## Building Block 4: Combined Rate-Limited Client

Compose the queue, backoff, and quota monitor into one resilient client. Set
`maxRetries: 0` on the SDK so retries are handled by `withBackoff`, not the SDK.

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
