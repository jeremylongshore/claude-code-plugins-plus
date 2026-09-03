---
name: perplexity-reliability-patterns
description: 'Implement reliability patterns for Perplexity Sonar API: circuit breaker,
  model fallback,

  streaming timeout, and citation validation.

  Use when production search needs bounded retries, tenant-safe cache fallback,

  stream cancellation, or untrusted citation handling.

  Trigger with phrases like "perplexity reliability", "perplexity circuit breaker",

  "perplexity fallback", "perplexity resilience", "perplexity timeout".

  '
allowed-tools: Read, Write, Edit
version: 1.12.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- perplexity
- perplexity-reliability
compatibility: Designed for Claude Code
---
# Perplexity Reliability Patterns

## Overview

Production reliability patterns for Perplexity Sonar API. Perplexity performs live web searches per request, making response times inherently variable. The key reliability challenges: search can stall, citations can break, and model tiers have different availability.

## Prerequisites

- Perplexity API key configured
- Cache layer (Redis or in-memory)
- Understanding of search latency variability

## Instructions

Use `Read` to map the existing request path, then use `Write` or `Edit` only for the selected bounded pattern. Preserve the application's authorization, tenant, data-classification, and observability boundaries while applying the steps below.

### Step 1: Model Tier Fallback

Add the status, SDK transport, and bounded `Retry-After` helpers from [the reliability verification matrix](references/reliability-test-matrix.md) in the same module before applying this fallback.

```typescript
import OpenAI from "openai";

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY!,
  baseURL: "https://api.perplexity.ai",
});

async function resilientSearch(
  query: string,
  preferredModel: string = "sonar-pro",
  options: {
    maxElapsedMs?: number;
    maxRateLimitRetriesPerModel?: number;
    sleep?: (delayMs: number) => Promise<void>;
    now?: () => number;
  } = {},
) {
  const fallbackChain = [...new Set([preferredModel, "sonar"])];
  const requestedElapsedMs = options.maxElapsedMs ?? 15_000;
  const requestedRateLimitRetries = options.maxRateLimitRetriesPerModel ?? 1;
  const maxElapsedMs = Number.isFinite(requestedElapsedMs)
    ? Math.min(30_000, Math.max(1, Math.trunc(requestedElapsedMs)))
    : 15_000;
  const maxRateLimitRetries = Number.isFinite(requestedRateLimitRetries)
    ? Math.min(2, Math.max(0, Math.trunc(requestedRateLimitRetries)))
    : 1;
  const sleep = options.sleep ?? ((delayMs) => new Promise((resolve) => setTimeout(resolve, delayMs)));
  const now = options.now ?? Date.now;
  const startedAt = now();
  let lastError: unknown;

  for (const model of fallbackChain) {
    let rateLimitRetries = 0;
    while (true) {
      if (lastError !== undefined && now() - startedAt >= maxElapsedMs) throw lastError;
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
      } catch (error: unknown) {
        lastError = error;
        if (!isRetryablePerplexityError(error)) throw error;

        if (perplexityStatus(error) === 429 && rateLimitRetries < maxRateLimitRetries) {
          const delayMs = boundedRetryAfterMs(error);
          if (now() - startedAt + delayMs > maxElapsedMs) throw error;
          rateLimitRetries++;
          try {
            await sleep(delayMs);
          } catch {
            throw error;
          }
          continue;
        }

        console.warn(`[Reliability] ${model} had a retryable failure; trying the bounded fallback.`);
        break;
      }
    }
  }

  throw lastError ?? new Error("All models failed");
}
```

### Step 2: Circuit Breaker

Trip the breaker only for `isRetryablePerplexityError(error)`. Terminal authentication, billing, validation, policy, and unknown failures must bypass the breaker and its fallback so the original error reaches the caller. Read the circuit-breaker implementation in [the reliability verification matrix](references/reliability-test-matrix.md); it contains the reusable class and the half-open concurrency contract.

### Step 3: Streaming with Timeout Protection

```typescript
async function* streamWithTimeout(
  query: string,
  model: string = "sonar",
  chunkTimeoutMs: number = 10_000,
  establishmentTimeoutMs: number = 10_000,
): AsyncGenerator<{ type: "text" | "citations" | "timeout"; data: any }> {
  const controller = new AbortController();

  try {
    const stream = await withStreamDeadline(
      perplexity.chat.completions.create(
        {
          model,
          messages: [{ role: "user", content: query }],
          stream: true,
          max_tokens: 2048,
        },
        { signal: controller.signal },
      ),
      establishmentTimeoutMs,
      controller,
      "establishment",
    );
    const iterator = stream[Symbol.asyncIterator]();

    while (true) {
      const item = await withStreamDeadline(
        iterator.next(),
        chunkTimeoutMs,
        controller,
        "chunk",
      );
      if (item.done) return;
      const text = item.value.choices[0]?.delta?.content || "";
      if (text) yield { type: "text", data: text };
      const citations = (item.value as { citations?: string[] }).citations;
      if (citations) yield { type: "citations", data: citations };
    }
  } catch (error) {
    if (error instanceof StreamDeadlineError) {
      const message = error.phase === "establishment"
        ? "Stream establishment timed out."
        : "Stream stalled before the next chunk.";
      yield { type: "timeout", data: message };
      return;
    }
    throw error;
  } finally {
    controller.abort();
  }
}

class StreamDeadlineError extends Error {
  constructor(readonly phase: "establishment" | "chunk") {
    super(`${phase}-timeout`);
  }
}

async function withStreamDeadline<T>(
  operation: Promise<T>,
  timeoutMs: number,
  controller: AbortController,
  phase: "establishment" | "chunk",
): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      reject(new StreamDeadlineError(phase));
      controller.abort();
    }, timeoutMs);
  });
  try {
    // Promise.race attaches handlers to both inputs, so a late rejection from
    // the aborted losing operation cannot become an unhandled rejection.
    return await Promise.race([operation, timeout]);
  } finally {
    if (timer) clearTimeout(timer);
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

async function searchWithCacheFallback(
  tenantId: string,
  query: string,
  model = "sonar",
  cacheable = false,
) {
  if (!/^[A-Za-z0-9_-]{1,64}$/.test(tenantId)) throw new Error("invalid tenant id");
  const normalizedQuery = query.normalize("NFKC").trim();
  const key = createHash("sha256")
    .update(`${tenantId}:${model}:${normalizedQuery}`)
    .digest("hex");

  try {
    const response = await resilientSearch(query, model);
    // Cache only data explicitly classified for this tenant and retention window.
    if (cacheable) reliabilityCache.set(key, response);
    return { ...response, source: "live" };
  } catch (error: unknown) {
    // Stale data is a resilience response only to a classified transient
    // provider failure. Preserve terminal auth, billing, validation, policy,
    // and unknown statusless errors so callers retain actionable context.
    if (!isRetryablePerplexityError(error)) throw error;
    const cached = cacheable ? reliabilityCache.get(key) : undefined;
    if (cached) {
      console.warn("[Reliability] Serving stale cached result");
      return { ...cached, source: "stale-cache" };
    }
    throw error;
  }
}
```

### Step 5: Citation URL Validation

Use the citation validator in [the reliability verification matrix](references/reliability-test-matrix.md). It normalizes bracketed IPv6 before IP classification and deliberately performs no server-side fetch. Citation URLs are model-supplied, untrusted input; following them from backend infrastructure creates SSRF, redirect, DNS-rebinding, and tracking risk. If availability checks are required, send normalized allowlisted URLs to an isolated egress-controlled service.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Classified SDK timeout/transport failure | Provider or network path is transiently unavailable | Retry only within the attempt and elapsed-time budget |
| Stream establishment or chunk stalls | Request or source search does not progress | Abort the same request signal at the phase deadline |
| Broken citation links | Source pages moved/deleted | Validate URLs before displaying |
| Terminal 4xx or unknown statusless failure | Auth, billing, validation, policy, or unclassified defect | Preserve the original error; never serve stale cache |

## Examples

### Tenant-safe degraded search

For a tenant whose request is explicitly cacheable, key the cache by tenant, model, and normalized query. On a retryable provider failure, serve only that tenant's retained result and label it stale. For authentication, billing, validation, or policy failures, bypass both model fallback and cached success so the caller sees the actionable error.

### Reject an unsafe citation without fetching it

Pass `https://docs.example.com/research` with `docs.example.com` in the approved host set and retain the normalized URL. Reject `http://example.com`, `https://127.0.0.1/admin`, `https://user:pass@example.com`, and `https://unapproved.example.net`. The application may render valid citations as user-clicked links with normal browser protections; the backend does not probe them.

## Output

- Model tier fallback chain
- Circuit breaker preventing cascade failures
- Streaming with stall detection
- Cache as reliability layer (stale > unavailable)
- Citation URL validation

## Resources

- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Reliability verification matrix](references/reliability-test-matrix.md)

## Next Steps

For policy enforcement, see `perplexity-policy-guardrails`.
