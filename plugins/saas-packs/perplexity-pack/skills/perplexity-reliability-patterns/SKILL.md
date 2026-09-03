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
    } catch (err: unknown) {
      const status = typeof err === "object" && err !== null && "status" in err
        ? Number((err as { status: unknown }).status)
        : 0;
      lastError = err instanceof Error ? err : new Error("Perplexity request failed");

      // Fallback is only for transient/provider failures. Retrying 4xx request,
      // authentication, or billing failures through another model amplifies harm.
      if (status !== 408 && status !== 429 && status < 500) throw lastError;
      console.warn(`[Reliability] ${model} had a retryable failure; trying the bounded fallback.`);
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

  async execute<T>(
    fn: () => Promise<T>,
    fallback: () => Promise<T>,
    isTripFailure: (error: unknown) => boolean,
  ): Promise<T> {
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
    } catch (err: unknown) {
      if (!isTripFailure(err)) throw err;
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
  cachedFallback,
  (error) => {
    const status = typeof error === "object" && error !== null && "status" in error
      ? Number((error as { status: unknown }).status)
      : 0;
    return status === 408 || status === 429 || status >= 500;
  },
);
```

### Step 3: Streaming with Timeout Protection

```typescript
async function* streamWithTimeout(
  query: string,
  model: string = "sonar",
  chunkTimeoutMs: number = 10000
): AsyncGenerator<{ type: "text" | "citations" | "timeout"; data: any }> {
  const controller = new AbortController();
  const stream = await perplexity.chat.completions.create(
    {
      model,
      messages: [{ role: "user", content: query }],
      stream: true,
      max_tokens: 2048,
    },
    { signal: controller.signal },
  );
  const iterator = stream[Symbol.asyncIterator]();

  try {
    while (true) {
      let timer: ReturnType<typeof setTimeout> | undefined;
      const next = iterator.next();
      const timed = new Promise<never>((_, reject) => {
        timer = setTimeout(() => reject(new Error("chunk-timeout")), chunkTimeoutMs);
      });

      try {
        const item = await Promise.race([next, timed]);
        if (item.done) return;
        const text = item.value.choices[0]?.delta?.content || "";
        if (text) yield { type: "text", data: text };
        const citations = (item.value as { citations?: string[] }).citations;
        if (citations) yield { type: "citations", data: citations };
      } catch (error) {
        if (error instanceof Error && error.message === "chunk-timeout") {
          controller.abort();
          yield { type: "timeout", data: "Stream stalled before the next chunk." };
          return;
        }
        throw error;
      } finally {
        if (timer) clearTimeout(timer);
      }
    }
  } finally {
    controller.abort();
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
  } catch {
    // Serve stale cache as last resort
    const cached = cacheable ? reliabilityCache.get(key) : undefined;
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
import { isIP } from "node:net";

function validateCitations(
  citations: string[],
  allowedHosts: ReadonlySet<string>,
): Array<{ url: string; valid: boolean; reason?: string }> {
  return citations.slice(0, 20).map((raw) => {
    try {
      const url = new URL(raw);
      const host = url.hostname.toLowerCase().replace(/\.$/, "");
      const allowed = [...allowedHosts].some(
        (candidate) => host === candidate || host.endsWith(`.${candidate}`),
      );
      if (url.protocol !== "https:") return { url: raw, valid: false, reason: "https-required" };
      if (url.username || url.password) return { url: raw, valid: false, reason: "userinfo-forbidden" };
      if (host === "localhost" || isIP(host) !== 0) return { url: raw, valid: false, reason: "local-or-ip-host" };
      if (!allowed) return { url: raw, valid: false, reason: "host-not-allowlisted" };
      return { url: url.href, valid: true };
    } catch {
      return { url: raw, valid: false, reason: "invalid-url" };
    }
  });
}
```

This validator deliberately performs no server-side fetch. Citation URLs are model-supplied, untrusted input; following them from backend infrastructure creates SSRF, redirect, DNS-rebinding, and tracking risk. If availability checks are required, send normalized allowlisted URLs to an isolated egress-controlled service.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| sonar-pro timeout >15s | Complex multi-source search | Fall back to sonar |
| Stream stalls | Search hanging on source | Per-chunk timeout detection |
| Broken citation links | Source pages moved/deleted | Validate URLs before displaying |
| All models failing | Perplexity outage | Serve stale cache, circuit breaker |

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
