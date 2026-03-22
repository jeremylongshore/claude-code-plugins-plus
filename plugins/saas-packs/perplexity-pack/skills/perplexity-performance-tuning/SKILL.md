---
name: perplexity-performance-tuning
description: |
  Optimize Perplexity Sonar API performance with caching, streaming, model routing, and batching.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Perplexity integrations.
  Trigger with phrases like "perplexity performance", "optimize perplexity",
  "perplexity latency", "perplexity caching", "perplexity slow".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, api, performance]

---
# Perplexity Performance Tuning

## Overview
Optimize Perplexity Sonar API for latency, throughput, and cost. Key insight: every Perplexity call performs a live web search, so response times are inherently variable. Typical latencies: sonar 1-3s, sonar-pro 3-8s, sonar-deep-research 10-60s.

## Latency Benchmarks

| Model | Typical Latency | Max Tokens | Best For |
|-------|----------------|------------|----------|
| `sonar` | 1-3s | 4096 | Quick answers, simple facts |
| `sonar-pro` | 3-8s | 8192 | Deep research, many citations |
| `sonar-reasoning-pro` | 5-15s | 8192 | Multi-step analysis |
| `sonar-deep-research` | 10-60s | 8192 | Comprehensive reports |

## Prerequisites
- Perplexity API key configured
- Understanding of search-augmented generation latency patterns
- Cache infrastructure (Redis or in-memory LRU)

## Instructions

### Step 1: Smart Model Routing
```typescript
import OpenAI from "openai";

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: "https://api.perplexity.ai",
});

type QueryComplexity = "simple" | "standard" | "deep";

function classifyQuery(query: string): QueryComplexity {
  const words = query.split(/\s+/).length;
  const simplePatterns = [/^what is/i, /^who is/i, /^when did/i, /^define/i, /^how many/i];
  const deepPatterns = [/compare.*vs/i, /analysis of/i, /comprehensive/i, /pros and cons/i, /in-depth/i];

  if (simplePatterns.some((p) => p.test(query)) && words < 15) return "simple";
  if (deepPatterns.some((p) => p.test(query)) || words > 30) return "deep";
  return "standard";
}

function selectModel(complexity: QueryComplexity): { model: string; maxTokens: number } {
  switch (complexity) {
    case "simple":  return { model: "sonar",     maxTokens: 256 };
    case "standard": return { model: "sonar",     maxTokens: 1024 };
    case "deep":    return { model: "sonar-pro", maxTokens: 4096 };
  }
}

async function smartSearch(query: string) {
  const complexity = classifyQuery(query);
  const { model, maxTokens } = selectModel(complexity);

  return perplexity.chat.completions.create({
    model,
    messages: [{ role: "user", content: query }],
    max_tokens: maxTokens,
  });
}
```

### Step 2: Query Hash Caching
```typescript
import { LRUCache } from "lru-cache";
import { createHash } from "crypto";

const CACHE_TTL = {
  news: 30 * 60 * 1000,      // 30 min for current events
  research: 4 * 60 * 60 * 1000,  // 4 hours for research
  factual: 24 * 60 * 60 * 1000,  // 24 hours for stable facts
};

const searchCache = new LRUCache<string, any>({
  max: 1000,
  ttl: CACHE_TTL.research,  // default TTL
});

function cacheKey(query: string, model: string): string {
  return createHash("sha256")
    .update(`${model}:${query.toLowerCase().trim()}`)
    .digest("hex");
}

function detectTTL(query: string): number {
  if (/\b(latest|today|breaking|current price|this week)\b/i.test(query))
    return CACHE_TTL.news;
  if (/\b(what is|define|how does|who is)\b/i.test(query))
    return CACHE_TTL.factual;
  return CACHE_TTL.research;
}

async function cachedSearch(query: string, model = "sonar") {
  const key = cacheKey(query, model);
  const cached = searchCache.get(key);
  if (cached) return { ...cached, cached: true };

  const result = await perplexity.chat.completions.create({
    model,
    messages: [{ role: "user", content: query }],
  });

  searchCache.set(key, result, { ttl: detectTTL(query) });
  return { ...result, cached: false };
}
```

### Step 3: Streaming for Perceived Performance
```typescript
async function streamSearch(
  query: string,
  onChunk: (text: string) => void,
  onCitations: (urls: string[]) => void
) {
  const stream = await perplexity.chat.completions.create({
    model: "sonar-pro",
    messages: [{ role: "user", content: query }],
    stream: true,
    max_tokens: 4096,
  });

  let fullText = "";
  for await (const chunk of stream) {
    const text = chunk.choices[0]?.delta?.content || "";
    fullText += text;
    onChunk(text);

    if ((chunk as any).citations) {
      onCitations((chunk as any).citations);
    }
  }
  return fullText;
}
```

### Step 4: Parallel Research with Rate Limiting
```typescript
import PQueue from "p-queue";

const queue = new PQueue({ concurrency: 3, interval: 1500, intervalCap: 1 });

async function parallelResearch(queries: string[]): Promise<Map<string, any>> {
  const results = new Map<string, any>();

  await Promise.all(
    queries.map((q) =>
      queue.add(async () => {
        const result = await cachedSearch(q, "sonar");
        results.set(q, result);
      })
    )
  );

  return results;
}
```

### Step 5: Response Size Optimization
```typescript
// Limit tokens to what you actually need
async function optimizedSearch(query: string, detail: "brief" | "full" = "brief") {
  return perplexity.chat.completions.create({
    model: "sonar",
    messages: [
      {
        role: "system",
        content: detail === "brief"
          ? "Answer in 2-3 sentences maximum."
          : "Provide a thorough answer with examples.",
      },
      { role: "user", content: query },
    ],
    max_tokens: detail === "brief" ? 150 : 2048,
  });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Latency >10s on sonar | Complex query triggering deep search | Add `max_tokens: 512` to limit response |
| Cache hit rate <20% | Queries too unique | Normalize queries (lowercase, trim) |
| Burst 429 errors | Parallel requests too aggressive | Use PQueue with intervalCap |
| Stale cached results | TTL too long for news | Use query-type-aware TTL |

## Output
- Smart model routing by query complexity
- Query-aware caching with appropriate TTLs
- Streaming for reduced perceived latency
- Rate-limited parallel research

## Resources
- [Perplexity Model Cards](https://docs.perplexity.ai/getting-started/models)
- [Perplexity Pricing](https://docs.perplexity.ai/docs/getting-started/pricing)

## Next Steps
For cost optimization, see `perplexity-cost-tuning`.
