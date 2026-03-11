---
name: perplexity-performance-tuning
description: |
  Optimize Perplexity API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Perplexity integrations.
  Trigger with phrases like "perplexity performance", "optimize perplexity",
  "perplexity latency", "perplexity caching", "perplexity slow", "perplexity batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Performance Tuning

## Overview
Optimize Perplexity Sonar API for research automation and fact-checking workflows. Focus on query caching for repeated searches, citation deduplication, streaming for long research queries, and model selection between speed and depth.

## Prerequisites
- Perplexity API key (sonar access)
- Understanding of Perplexity model tiers
- Cache layer for search result deduplication
- Monitoring for token usage and costs

## Instructions

### Step 1: Model Selection for Speed vs Depth
```typescript
import OpenAI from 'openai';

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: 'https://api.perplexity.ai',
});

// Model tiers:
// sonar:             Fast, basic search (cheapest)
// sonar-pro:         Deeper search, more citations
// sonar-reasoning:   Multi-step reasoning with search

async function quickSearch(query: string) {
  return perplexity.chat.completions.create({
    model: 'sonar',
    messages: [{ role: 'user', content: query }],
    max_tokens: 512,
  });
}

async function deepResearch(query: string) {
  return perplexity.chat.completions.create({
    model: 'sonar-pro',
    messages: [
      { role: 'system', content: 'Provide comprehensive research with citations.' },
      { role: 'user', content: query },
    ],
    max_tokens: 2048,
  });
}
```

### Step 2: Cache Search Results by Query Hash
```typescript
import { LRUCache } from 'lru-cache';
import { createHash } from 'crypto';

const searchCache = new LRUCache<string, any>({
  max: 1000,
  ttl: 1000 * 60 * 60, // 1 hour - search results age
});

function queryHash(query: string, model: string): string {
  return createHash('sha256')
    .update(`${model}:${query.toLowerCase().trim()}`)
    .digest('hex');
}

async function cachedSearch(query: string, model = 'sonar') {
  const key = queryHash(query, model);
  const cached = searchCache.get(key);
  if (cached) return cached;

  const result = await perplexity.chat.completions.create({
    model,
    messages: [{ role: 'user', content: query }],
  });

  searchCache.set(key, result);
  return result;
}
```

### Step 3: Stream Long Research Queries
```typescript
async function streamResearch(
  query: string,
  onChunk: (text: string) => void
) {
  const stream = await perplexity.chat.completions.create({
    model: 'sonar-pro',
    messages: [{ role: 'user', content: query }],
    stream: true,
    max_tokens: 4096,
  });

  let fullText = '';
  for await (const chunk of stream) {
    const text = chunk.choices[0]?.delta?.content || '';
    fullText += text;
    onChunk(text);
  }
  return { text: fullText, citations: extractCitations(fullText) };
}

function extractCitations(text: string): string[] {
  const urlRegex = /https?:\/\/[^\s\]]+/g;
  return [...new Set(text.match(urlRegex) || [])];
}
```

### Step 4: Parallel Research with Deduplication
```typescript
async function parallelResearch(
  queries: string[],
  concurrency = 3
) {
  const results: Map<string, any> = new Map();

  for (let i = 0; i < queries.length; i += concurrency) {
    const batch = queries.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map(q => cachedSearch(q, 'sonar'))
    );

    batch.forEach((q, idx) => results.set(q, batchResults[idx]));

    if (i + concurrency < queries.length) {
      await new Promise(r => setTimeout(r, 500));
    }
  }
  return results;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limit 429 | Exceeding RPM quota | Reduce concurrency, add delays |
| Stale citations | Cache TTL too long | Reduce to 30 min for time-sensitive queries |
| Incomplete citations | Using sonar basic | Upgrade to sonar-pro for more sources |
| High token cost | Using sonar-pro for simple queries | Route simple queries to sonar basic |

## Examples

### Fact-Checking Pipeline
```typescript
async function factCheck(claims: string[]) {
  const results = await parallelResearch(
    claims.map(c => `Verify this claim with sources: ${c}`)
  );

  return claims.map(claim => ({
    claim,
    analysis: results.get(`Verify this claim with sources: ${claim}`),
  }));
}
```

## Resources
- [Perplexity API Docs](https://docs.perplexity.ai/)
- [Perplexity Model Guide](https://docs.perplexity.ai/guides/model-cards)
