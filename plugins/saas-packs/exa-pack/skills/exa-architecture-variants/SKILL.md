---
name: exa-architecture-variants
description: |
  Choose and implement Exa architecture patterns at different scales: direct search, cached search, and RAG pipeline.
  Use when designing Exa integrations, choosing between simple search and full RAG,
  or planning architecture for different traffic volumes.
  Trigger with phrases like "exa architecture", "exa blueprint",
  "how to structure exa", "exa RAG design", "exa at scale".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, architecture, rag, scaling]

---
# Exa Architecture Variants

## Overview
Three deployment architectures for Exa neural search at different scales. Each uses real Exa SDK methods: `search`, `searchAndContents`, `findSimilar`, `getContents`, and `answer`.

## Decision Matrix

| Factor | Direct Search | Cached Search | RAG Pipeline |
|--------|--------------|---------------|--------------|
| Volume | < 1K/day | 1K-50K/day | Any volume |
| Latency | 500-2000ms | ~50ms (cached) | 3-8s total |
| Use Case | Simple search UI | Content aggregation | AI answers with citations |
| Complexity | Low | Medium | High |
| Cache Required | No | Yes (Redis/LRU) | Yes |
| Exa Methods | `searchAndContents` | `searchAndContents` + cache | All methods |

## Instructions

### Variant 1: Direct Search Integration
**Best for:** Adding search to an existing app, < 1K queries/day.

```typescript
import Exa from "exa-js";
import express from "express";

const app = express();
const exa = new Exa(process.env.EXA_API_KEY);

// Simple search endpoint
app.get("/api/search", async (req, res) => {
  const query = req.query.q as string;
  if (!query) return res.status(400).json({ error: "q required" });

  try {
    const results = await exa.searchAndContents(query, {
      type: "auto",
      numResults: 5,
      text: { maxCharacters: 500 },
      highlights: { maxCharacters: 300, query },
    });

    res.json(results.results.map(r => ({
      title: r.title,
      url: r.url,
      snippet: r.highlights?.join(" ") || r.text?.substring(0, 200),
      score: r.score,
    })));
  } catch (err: any) {
    res.status(err.status || 500).json({ error: err.message });
  }
});
```

### Variant 2: Cached Search with Category Profiles
**Best for:** High-traffic search, 1K-50K queries/day, content discovery.

```typescript
import Exa from "exa-js";
import { LRUCache } from "lru-cache";

const exa = new Exa(process.env.EXA_API_KEY);
const cache = new LRUCache<string, any>({ max: 5000, ttl: 3600 * 1000 });

const PROFILES = {
  news: {
    type: "auto" as const,
    category: "news" as const,
    numResults: 10,
    text: { maxCharacters: 500 },
  },
  research: {
    type: "neural" as const,
    category: "research paper" as const,
    numResults: 10,
    text: { maxCharacters: 2000 },
    highlights: { maxCharacters: 500 },
  },
  companies: {
    type: "auto" as const,
    category: "company" as const,
    numResults: 10,
    text: { maxCharacters: 500 },
  },
};

async function cachedProfileSearch(
  query: string,
  profile: keyof typeof PROFILES
) {
  const key = `${query.toLowerCase()}:${profile}`;
  const cached = cache.get(key);
  if (cached) return cached;

  const results = await exa.searchAndContents(query, PROFILES[profile]);
  cache.set(key, results);
  return results;
}
```

### Variant 3: Full RAG Pipeline
**Best for:** AI-powered answers, research agents, 50K+ queries/day.

```typescript
import Exa from "exa-js";
import { LRUCache } from "lru-cache";

const exa = new Exa(process.env.EXA_API_KEY);
const contextCache = new LRUCache<string, any>({ max: 10000, ttl: 7200 * 1000 });

class ExaRAGPipeline {
  // Phase 1: Search for relevant sources
  async gatherContext(question: string, maxSources = 5) {
    const cacheKey = question.toLowerCase().trim();
    const cached = contextCache.get(cacheKey);
    if (cached) return cached;

    const results = await exa.searchAndContents(question, {
      type: "neural",
      numResults: maxSources,
      text: { maxCharacters: 2000 },
      highlights: { maxCharacters: 500, query: question },
    });

    contextCache.set(cacheKey, results);
    return results;
  }

  // Phase 2: Expand with similar content
  async expandContext(topResultUrl: string, numSimilar = 3) {
    return exa.findSimilarAndContents(topResultUrl, {
      numResults: numSimilar,
      text: { maxCharacters: 1500 },
      excludeSourceDomain: true,
    });
  }

  // Phase 3: Format for LLM context injection
  formatForLLM(results: any[]) {
    return results.map((r, i) =>
      `[Source ${i + 1}] ${r.title}\n` +
      `URL: ${r.url}\n` +
      `Content: ${r.text}\n` +
      `Key points: ${r.highlights?.join(" | ") || "N/A"}`
    ).join("\n\n---\n\n");
  }

  // Phase 4: Use Exa's built-in answer endpoint
  async getAnswer(question: string) {
    const answer = await exa.answer(question, { text: true });
    return {
      answer: answer.answer,
      sources: answer.results.map(r => ({
        title: r.title,
        url: r.url,
      })),
    };
  }

  // Full pipeline
  async research(question: string) {
    const context = await this.gatherContext(question, 5);

    // Expand with similar content from top result
    let expanded = { results: [] as any[] };
    if (context.results[0]?.url) {
      expanded = await this.expandContext(context.results[0].url);
    }

    const allResults = [...context.results, ...expanded.results];
    const llmContext = this.formatForLLM(allResults);

    return {
      context: llmContext,
      sourceCount: allResults.length,
      sources: allResults.map(r => ({ title: r.title, url: r.url, score: r.score })),
    };
  }
}
```

## Scaling Notes

| Architecture | 10 QPS Limit Strategy |
|-------------|----------------------|
| Direct | Natural limit: ~864K searches/day at full rate |
| Cached | 50% cache hit = ~1.7M effective searches/day |
| RAG Pipeline | 2-3 API calls per question; cache aggressively |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow search in UI | No caching | Add LRU or Redis cache |
| Stale cached results | Long TTL | Reduce TTL for time-sensitive profiles |
| RAG hallucination | Poor source selection | Use highlights, increase numResults |
| High API costs | No query deduplication | Cache layer deduplicates identical queries |

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa Contents Retrieval](https://docs.exa.ai/reference/contents-retrieval)
- [Exa Find Similar](https://docs.exa.ai/reference/find-similar-links)

## Next Steps
For reference architecture details, see `exa-reference-architecture`.
