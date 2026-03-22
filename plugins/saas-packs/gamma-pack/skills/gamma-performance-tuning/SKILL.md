---
name: gamma-performance-tuning
description: |
  Optimize Gamma API performance and reduce latency.
  Use when experiencing slow response times, optimizing throughput,
  or improving user experience with Gamma integrations.
  Trigger with phrases like "gamma performance", "gamma slow",
  "gamma latency", "gamma optimization", "gamma speed".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, api, performance]

---
# Gamma Performance Tuning

## Overview

Optimize Gamma API integration performance. Gamma's generate-poll-retrieve pattern means most latency is in generation time (10-60s), not API call overhead. Optimize by: reducing poll overhead, parallelizing batch operations, caching results, and choosing the right generation parameters.

## Prerequisites

- Working Gamma integration (see `gamma-sdk-patterns`)
- Understanding of async patterns
- Redis or in-memory cache (recommended)

## Performance Characteristics

| Operation | Typical Latency | Notes |
|-----------|----------------|-------|
| POST `/generations` | 200-500ms | Just starts the generation |
| GET `/generations/{id}` (poll) | 100-300ms | Per poll request |
| Full generation (poll to completion) | 10-60s | Depends on content + cards |
| GET `/themes` | 100-200ms | Cacheable |
| GET `/folders` | 100-200ms | Cacheable |

## Instructions

### Step 1: Optimize Poll Strategy

```typescript
// src/gamma/smart-poll.ts
// Adaptive polling: start fast, slow down over time

export async function smartPoll(
  gamma: GammaClient,
  generationId: string,
  opts = { maxTimeMs: 180000 }
): Promise<GenerateResult> {
  const deadline = Date.now() + opts.maxTimeMs;
  let interval = 2000; // Start at 2s

  while (Date.now() < deadline) {
    const result = await gamma.poll(generationId);

    if (result.status === "completed") return result;
    if (result.status === "failed") throw new Error("Generation failed");

    // Adaptive backoff: poll faster early, slower later
    await new Promise((r) => setTimeout(r, interval));
    interval = Math.min(interval * 1.5, 10000); // Max 10s between polls
  }

  throw new Error(`Poll timeout after ${opts.maxTimeMs}ms`);
}
```

### Step 2: Cache Static Data

```typescript
// src/gamma/cache.ts
import NodeCache from "node-cache";

const cache = new NodeCache({ stdTTL: 3600 }); // 1 hour for static data

export async function getCachedThemes(gamma: GammaClient) {
  const key = "gamma:themes";
  const cached = cache.get(key);
  if (cached) return cached;

  const themes = await gamma.listThemes();
  cache.set(key, themes);
  return themes;
}

export async function getCachedFolders(gamma: GammaClient) {
  const key = "gamma:folders";
  const cached = cache.get(key);
  if (cached) return cached;

  const folders = await gamma.listFolders();
  cache.set(key, folders);
  return folders;
}

// Cache generation results (useful for showing status)
export async function cacheGenerationResult(
  generationId: string,
  result: GenerateResult
) {
  cache.set(`gamma:gen:${generationId}`, result, 86400); // 24 hours
}
```

### Step 3: Parallel Batch Generation

```typescript
// src/gamma/batch.ts
import pLimit from "p-limit";

const limit = pLimit(3); // Max 3 concurrent generations

export async function batchGenerate(
  gamma: GammaClient,
  requests: Array<{ content: string; exportAs?: string }>
): Promise<Array<{ index: number; result?: GenerateResult; error?: string }>> {
  const results = await Promise.allSettled(
    requests.map((req, index) =>
      limit(async () => {
        const { generationId } = await gamma.generate({
          content: req.content,
          outputFormat: "presentation",
          exportAs: req.exportAs,
        });
        const result = await smartPoll(gamma, generationId);
        return { index, result };
      })
    )
  );

  return results.map((r, i) => {
    if (r.status === "fulfilled") return r.value;
    return { index: i, error: (r.reason as Error).message };
  });
}
```

### Step 4: Reduce Generation Time

```typescript
// Shorter content = faster generation
// "brief" text = fewer AI-generated words per card = faster

// SLOWER: extensive text on many cards
await gamma.generate({
  content: "Comprehensive 20-card guide to machine learning...",
  outputFormat: "presentation",
  textAmount: "extensive",  // More text per card = slower
});

// FASTER: brief text, fewer implied cards
await gamma.generate({
  content: "5-card overview of ML basics: supervised, unsupervised, reinforcement, deep learning, applications",
  outputFormat: "presentation",
  textAmount: "brief",      // Less text per card = faster
});

// FASTEST: preserve mode (no AI text generation)
await gamma.generate({
  content: "Your pre-written slide content here...",
  outputFormat: "presentation",
  textMode: "preserve",     // Uses your text as-is, no AI rewriting
});
```

### Step 5: Preload Data at Startup

```typescript
// src/gamma/preload.ts
// Fetch themes and folders at app startup, not per-request

let preloaded = false;

export async function preloadGammaData(gamma: GammaClient) {
  if (preloaded) return;

  const [themes, folders] = await Promise.all([
    gamma.listThemes(),
    gamma.listFolders(),
  ]);

  // Cache for the session
  cache.set("gamma:themes", themes, 0);   // No TTL (until restart)
  cache.set("gamma:folders", folders, 0);

  preloaded = true;
  console.log(`Preloaded ${themes.length} themes, ${folders.length} folders`);
}
```

### Step 6: Connection Keep-Alive

```typescript
// src/gamma/optimized-client.ts
import http from "node:http";
import https from "node:https";

// Reuse TCP connections
const agent = new https.Agent({
  keepAlive: true,
  maxSockets: 10,
  keepAliveMsecs: 60000,
});

export function createOptimizedClient(apiKey: string) {
  const base = "https://public-api.gamma.app/v1.0";
  const headers = { "X-API-KEY": apiKey, "Content-Type": "application/json" };

  async function request(method: string, path: string, body?: unknown) {
    const res = await fetch(`${base}${path}`, {
      method, headers,
      body: body ? JSON.stringify(body) : undefined,
      // @ts-ignore — agent support in Node.js
      agent,
    });
    if (!res.ok) throw new Error(`Gamma ${res.status}`);
    return res.json();
  }

  return {
    generate: (body: any) => request("POST", "/generations", body),
    poll: (id: string) => request("GET", `/generations/${id}`),
    listThemes: () => request("GET", "/themes"),
    listFolders: () => request("GET", "/folders"),
  };
}
```

## Performance Targets

| Operation | Target | Action if Exceeded |
|-----------|--------|-------------------|
| Theme/folder lookup | < 50ms (cached) | Verify cache hit |
| Generation start | < 500ms | Check network latency |
| Full generation (5 cards) | < 30s | Use `textAmount: "brief"` |
| Full generation (10+ cards) | < 60s | Split into smaller decks |
| Batch of 10 presentations | < 3 min | Use concurrency limit of 3 |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High latency on first request | Cold TCP connection | Use keep-alive agent |
| Cache miss storm | Cache expired simultaneously | Stagger TTLs |
| Batch rate limiting | Too many concurrent requests | Reduce `p-limit` concurrency |
| Poll timeout | Complex generation | Increase timeout, simplify content |

## Resources

- [Gamma API Parameters](https://developers.gamma.app/guides/generate-api-parameters-explained)
- [p-limit Documentation](https://github.com/sindresorhus/p-limit)
- [node-cache](https://github.com/node-cache/node-cache)

## Next Steps

Proceed to `gamma-cost-tuning` for credit optimization.
