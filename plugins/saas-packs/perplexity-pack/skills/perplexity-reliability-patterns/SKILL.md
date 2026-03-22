---
name: perplexity-reliability-patterns
description: |
  Implement reliability patterns for Perplexity Sonar API: circuit breaker, model fallback,
  streaming timeout, and citation validation.
  Trigger with phrases like "perplexity reliability", "perplexity circuit breaker",
  "perplexity fallback", "perplexity resilience", "perplexity timeout".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, perplexity-reliability]

---
# Perplexity Reliability Patterns

## Overview
Production reliability patterns for Perplexity Sonar API. Perplexity performs live web searches per request, making response times inherently variable. The key reliability challenges: search can stall, citations can break, and model tiers have different availability.

## Prerequisites
- Perplexity API key configured
- Cache layer (Redis or in-memory)
- Understanding of search latency variability

## Instructions

### Step 1: Model Tier Fallback
```typescript
import OpenAI from "openai";

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY!,
  baseURL: "https://api.perplexity.ai",
});

async function resilientSearch(
  query: string,
  preferredModel: string = "sonar-pro"
) {
  const fallbackChain = [preferredModel, "sonar"];
  let lastError: Error | null = null;

  for (const model of fallbackChain) {
    try {
      const response = await perplexity.chat.completions.create({
        model,
        messages: [{ role: "user", content: query }],
        max_tokens: model === "sonar-pro" ? 2048 : 512,
      });

      if (model !== preferredModel) {
        console.warn(`[Reliability] Fell back from ${preferredModel} to ${model}`);
      }

      return {
        answer: response.choices[0].message.content || "",
        citations: (response as any).citations || [],
        model: response.model,
        fallback: model !== preferredModel,
      };
    } catch (err: any) {
      lastError = err;
      if (err.status === 401 || err.status === 402) throw err; // Don't retry auth/billing
      console.warn(`[Reliability] ${model} failed (${err.status || err.message}), trying next`);
    }
  }

  throw lastError || new Error("All models failed");
}
```

### Step 2: Circuit Breaker
```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: "closed" | "open" | "half-open" = "closed";

  constructor(
    private threshold: number = 5,
    private resetTimeMs: number = 60000
  ) {}

  async execute<T>(fn: () => Promise<T>, fallback: () => Promise<T>): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.lastFailure > this.resetTimeMs) {
        this.state = "half-open";
      } else {
        console.warn("[CircuitBreaker] Open — using fallback");
        return fallback();
      }
    }

    try {
      const result = await fn();
      if (this.state === "half-open") {
        this.state = "closed";
        this.failures = 0;
      }
      return result;
    } catch (err) {
      this.failures++;
      this.lastFailure = Date.now();
      if (this.failures >= this.threshold) {
        this.state = "open";
        console.warn(`[CircuitBreaker] Opened after ${this.failures} failures`);
      }
      return fallback();
    }
  }

  get status() {
    return { state: this.state, failures: this.failures };
  }
}

// Usage
const breaker = new CircuitBreaker(5, 60000);
const cachedFallback = () => getCachedResult(query);

const result = await breaker.execute(
  () => resilientSearch(query, "sonar-pro"),
  cachedFallback
);
```

### Step 3: Streaming with Timeout Protection
```typescript
async function* streamWithTimeout(
  query: string,
  model: string = "sonar",
  chunkTimeoutMs: number = 10000
): AsyncGenerator<{ type: "text" | "citations" | "timeout"; data: any }> {
  const stream = await perplexity.chat.completions.create({
    model,
    messages: [{ role: "user", content: query }],
    stream: true,
    max_tokens: 2048,
  });

  let lastChunkAt = Date.now();

  for await (const chunk of stream) {
    if (Date.now() - lastChunkAt > chunkTimeoutMs) {
      yield { type: "timeout", data: "Stream stalled — no data for 10s" };
      return;
    }

    lastChunkAt = Date.now();
    const text = chunk.choices[0]?.delta?.content || "";
    if (text) yield { type: "text", data: text };

    const citations = (chunk as any).citations;
    if (citations) yield { type: "citations", data: citations };
  }
}

// Usage
for await (const event of streamWithTimeout("explain quantum computing", "sonar-pro")) {
  if (event.type === "text") process.stdout.write(event.data);
  if (event.type === "citations") console.log("\nSources:", event.data);
  if (event.type === "timeout") console.error("\nStream timed out");
}
```

### Step 4: Cache as Reliability Layer
```typescript
import { LRUCache } from "lru-cache";
import { createHash } from "crypto";

const reliabilityCache = new LRUCache<string, any>({
  max: 500,
  ttl: 24 * 3600_000, // 24-hour stale cache for reliability
});

async function searchWithCacheFallback(query: string, model = "sonar") {
  const key = createHash("sha256").update(`${model}:${query}`).digest("hex");

  try {
    const response = await resilientSearch(query, model);
    // Update cache on success
    reliabilityCache.set(key, response);
    return { ...response, source: "live" };
  } catch {
    // Serve stale cache as last resort
    const cached = reliabilityCache.get(key);
    if (cached) {
      console.warn("[Reliability] Serving stale cached result");
      return { ...cached, source: "stale-cache" };
    }
    throw new Error("Perplexity unavailable and no cached result");
  }
}
```

### Step 5: Citation URL Validation
```typescript
async function validateCitations(
  citations: string[],
  timeoutMs: number = 5000
): Promise<Array<{ url: string; status: number; valid: boolean }>> {
  const results = await Promise.allSettled(
    citations.slice(0, 5).map(async (url) => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(url, {
          method: "HEAD",
          signal: controller.signal,
          redirect: "follow",
        });
        return { url, status: response.status, valid: response.status < 400 };
      } catch {
        return { url, status: 0, valid: false };
      } finally {
        clearTimeout(timeout);
      }
    })
  );

  return results.map((r) =>
    r.status === "fulfilled" ? r.value : { url: "", status: 0, valid: false }
  );
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| sonar-pro timeout >15s | Complex multi-source search | Fall back to sonar |
| Stream stalls | Search hanging on source | Per-chunk timeout detection |
| Broken citation links | Source pages moved/deleted | Validate URLs before displaying |
| All models failing | Perplexity outage | Serve stale cache, circuit breaker |

## Output
- Model tier fallback chain
- Circuit breaker preventing cascade failures
- Streaming with stall detection
- Cache as reliability layer (stale > unavailable)
- Citation URL validation

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)

## Next Steps
For policy enforcement, see `perplexity-policy-guardrails`.
