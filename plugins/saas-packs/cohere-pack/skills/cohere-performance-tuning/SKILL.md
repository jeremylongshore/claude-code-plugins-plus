---
name: cohere-performance-tuning
description: |
  Optimize Cohere API performance with caching, batching, model selection, and streaming.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Cohere Chat, Embed, and Rerank.
  Trigger with phrases like "cohere performance", "optimize cohere",
  "cohere latency", "cohere caching", "cohere slow", "cohere batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Performance Tuning

## Overview
Optimize Cohere API v2 performance through model selection, embedding batches, rerank pipelines, caching, and streaming for time-to-first-token.

## Prerequisites
- `cohere-ai` SDK installed
- Understanding of Cohere endpoints (Chat, Embed, Rerank)
- Redis or in-memory cache (optional)

## Latency Benchmarks (Typical)

| Operation | Model | P50 | P95 |
|-----------|-------|-----|-----|
| Chat (short) | `command-r7b-12-2024` | 500ms | 1.5s |
| Chat (short) | `command-a-03-2025` | 800ms | 2.5s |
| Chat (stream TTFT) | `command-a-03-2025` | 200ms | 600ms |
| Embed (96 texts) | `embed-v4.0` | 150ms | 400ms |
| Rerank (100 docs) | `rerank-v3.5` | 100ms | 300ms |
| Classify (96 inputs) | `embed-english-v3.0` | 200ms | 500ms |

## Instructions

### Strategy 1: Model Selection by Latency Budget

```typescript
// Use smaller models for latency-sensitive paths
function selectModel(latencyBudgetMs: number): string {
  if (latencyBudgetMs < 1000) return 'command-r7b-12-2024';   // 7B, fastest
  if (latencyBudgetMs < 3000) return 'command-r-08-2024';      // Mid-tier
  return 'command-a-03-2025';                                    // Best quality
}

// Pair with maxTokens to control output length
await cohere.chat({
  model: selectModel(1500),
  messages: [{ role: 'user', content: query }],
  maxTokens: 200,  // Shorter output = lower latency
});
```

### Strategy 2: Streaming for Time-to-First-Token

```typescript
// Non-streaming: user waits for entire response (800ms-5s)
// Streaming: first token arrives in ~200ms

async function streamForUI(message: string): Promise<string> {
  const stream = await cohere.chatStream({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: message }],
  });

  let fullText = '';
  for await (const event of stream) {
    if (event.type === 'content-delta') {
      const text = event.delta?.message?.content?.text ?? '';
      fullText += text;
      // Emit to frontend immediately — perceived latency drops to ~200ms
    }
  }
  return fullText;
}
```

### Strategy 3: Batch Embeddings (96 per Call)

```typescript
// BAD: 1000 texts = 1000 API calls
for (const text of texts) {
  await cohere.embed({ model: 'embed-v4.0', texts: [text], ... });
}

// GOOD: 1000 texts = 11 API calls (96 per batch)
async function batchEmbed(texts: string[]): Promise<number[][]> {
  const BATCH = 96; // Cohere max per request
  const results: number[][] = [];

  const batches = [];
  for (let i = 0; i < texts.length; i += BATCH) {
    batches.push(texts.slice(i, i + BATCH));
  }

  // Parallel batches (respect rate limits)
  const responses = await Promise.all(
    batches.map(batch =>
      cohere.embed({
        model: 'embed-v4.0',
        texts: batch,
        inputType: 'search_document',
        embeddingTypes: ['float'],
      })
    )
  );

  for (const resp of responses) {
    results.push(...resp.embeddings.float);
  }
  return results;
}
```

### Strategy 4: Compressed Embeddings

```typescript
// float: 1024 dims * 4 bytes = 4KB per vector
// int8:  1024 dims * 1 byte  = 1KB per vector (75% smaller)
// binary: 1024 dims / 8      = 128 bytes per vector (97% smaller)

const response = await cohere.embed({
  model: 'embed-v4.0',
  texts: documents,
  inputType: 'search_document',
  embeddingTypes: ['int8'],   // or ['binary'] for maximum compression
});

// Use int8 for storage, float for final scoring
const storageVectors = response.embeddings.int8;   // Store these
```

### Strategy 5: Rerank as a Pre-filter

```typescript
// Instead of embedding everything, use rerank as a fast pre-filter
async function efficientSearch(query: string, corpus: string[]) {
  // Step 1: Rerank finds top candidates in ~100ms (up to 1000 docs)
  const reranked = await cohere.rerank({
    model: 'rerank-v3.5',
    query,
    documents: corpus,
    topN: 5,
  });

  // Step 2: Only embed the top 5 for fine-grained scoring (optional)
  const topDocs = reranked.results.map(r => ({
    text: corpus[r.index],
    score: r.relevanceScore,
  }));

  return topDocs;
}
```

### Strategy 6: Embedding Cache

```typescript
import { LRUCache } from 'lru-cache';
import crypto from 'crypto';

const embedCache = new LRUCache<string, number[]>({
  max: 10_000,
  ttl: 24 * 60 * 60 * 1000, // 24h — embeddings are deterministic
});

function hashText(text: string): string {
  return crypto.createHash('sha256').update(text).digest('hex').slice(0, 16);
}

async function cachedEmbed(texts: string[]): Promise<number[][]> {
  const results: number[][] = new Array(texts.length);
  const uncached: { index: number; text: string }[] = [];

  // Check cache first
  for (let i = 0; i < texts.length; i++) {
    const key = hashText(texts[i]);
    const cached = embedCache.get(key);
    if (cached) {
      results[i] = cached;
    } else {
      uncached.push({ index: i, text: texts[i] });
    }
  }

  // Embed only uncached texts
  if (uncached.length > 0) {
    const vectors = await batchEmbed(uncached.map(u => u.text));
    for (let j = 0; j < uncached.length; j++) {
      results[uncached[j].index] = vectors[j];
      embedCache.set(hashText(uncached[j].text), vectors[j]);
    }
  }

  return results;
}
```

### Strategy 7: Response Caching for Chat

```typescript
import { LRUCache } from 'lru-cache';

// Cache chat responses for deterministic queries
const chatCache = new LRUCache<string, string>({
  max: 1000,
  ttl: 5 * 60 * 1000, // 5 min TTL — chat responses can vary
});

async function cachedChat(message: string, system?: string): Promise<string> {
  const key = `${system ?? ''}:${message}`;
  const cached = chatCache.get(key);
  if (cached) return cached;

  const response = await cohere.chat({
    model: 'command-a-03-2025',
    messages: [
      ...(system ? [{ role: 'system' as const, content: system }] : []),
      { role: 'user' as const, content: message },
    ],
    temperature: 0, // Deterministic for caching
  });

  const text = response.message?.content?.[0]?.text ?? '';
  chatCache.set(key, text);
  return text;
}
```

## Performance Monitoring

```typescript
async function timedCohereCall<T>(
  endpoint: string,
  fn: () => Promise<T>
): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const ms = performance.now() - start;
    console.log(`[cohere] ${endpoint}: ${ms.toFixed(0)}ms`);
    return result;
  } catch (err) {
    const ms = performance.now() - start;
    console.error(`[cohere] ${endpoint} FAILED: ${ms.toFixed(0)}ms`, err);
    throw err;
  }
}
```

## Output
- Model selection by latency budget
- Streaming for sub-200ms TTFT
- Batch embedding (96x fewer API calls)
- Compressed embeddings (75-97% storage savings)
- Cache layer for deterministic queries
- Rerank as fast pre-filter

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Chat > 5s | Long output + slow model | Use streaming, reduce maxTokens |
| Embed timeout | Too many texts | Batch to 96 per call |
| Cache stale | Long TTL | Reduce TTL for volatile data |
| High costs | No caching | Cache embeddings (deterministic) |

## Resources
- [Cohere Models & Context](https://docs.cohere.com/docs/models)
- [Embed Best Practices](https://docs.cohere.com/docs/cohere-embed)
- [Rerank Best Practices](https://docs.cohere.com/docs/reranking-best-practices)

## Next Steps
For cost optimization, see `cohere-cost-tuning`.
