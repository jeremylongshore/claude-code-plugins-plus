---
name: exa-reference-architecture
description: |
  Implement Exa reference architecture for search pipelines, RAG, and content discovery.
  Use when designing new Exa integrations, reviewing project structure,
  or establishing architecture standards for neural search applications.
  Trigger with phrases like "exa architecture", "exa project structure",
  "exa RAG pipeline", "exa reference design", "exa search pipeline".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, architecture, rag]

---
# Exa Reference Architecture

## Overview
Production architecture for Exa neural search integration. Covers search service design, content extraction pipeline, RAG integration, domain-scoped search profiles, and caching strategy.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                  Application Layer                        │
│   RAG Pipeline  |  Research Agent  |  Content Discovery   │
└──────────┬──────────────┬───────────────┬────────────────┘
           │              │               │
           ▼              ▼               ▼
┌──────────────────────────────────────────────────────────┐
│                Exa Search Service Layer                    │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐    │
│  │ search()   │  │ findSimilar│  │ getContents()    │    │
│  │ neural/    │  │ (URL seed) │  │ (known URLs)     │    │
│  │ keyword/   │  └────────────┘  └──────────────────┘    │
│  │ auto/fast  │                                           │
│  └────────────┘                  ┌──────────────────┐    │
│                                  │ answer() /       │    │
│  Content Options:                │ streamAnswer()   │    │
│  text | highlights | summary     └──────────────────┘    │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Result Cache (LRU + Redis)             │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│  api.exa.ai — Exa Neural Search API                      │
│  Auth: x-api-key header | Rate: 10 QPS default           │
└──────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Search Service Layer
```typescript
// src/exa/service.ts
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

interface SearchRequest {
  query: string;
  type?: "auto" | "neural" | "keyword" | "fast" | "instant";
  numResults?: number;
  startDate?: string;
  endDate?: string;
  includeDomains?: string[];
  excludeDomains?: string[];
  category?: "company" | "research paper" | "news" | "tweet" | "people";
}

interface ContentOptions {
  text?: boolean | { maxCharacters?: number };
  highlights?: boolean | { maxCharacters?: number; query?: string };
  summary?: boolean | { query?: string };
}

export async function searchWithContents(
  req: SearchRequest,
  content: ContentOptions = { text: { maxCharacters: 2000 } }
) {
  return exa.searchAndContents(req.query, {
    type: req.type || "auto",
    numResults: req.numResults || 10,
    startPublishedDate: req.startDate,
    endPublishedDate: req.endDate,
    includeDomains: req.includeDomains,
    excludeDomains: req.excludeDomains,
    category: req.category,
    ...content,
  });
}

export async function findRelated(url: string, numResults = 5) {
  return exa.findSimilarAndContents(url, {
    numResults,
    text: { maxCharacters: 1000 },
    excludeSourceDomain: true,
  });
}
```

### Step 2: Research Pipeline
```typescript
// src/exa/research.ts
export async function researchTopic(topic: string) {
  // Phase 1: Broad neural search
  const sources = await exa.searchAndContents(topic, {
    type: "neural",
    numResults: 15,
    text: { maxCharacters: 2000 },
    highlights: { maxCharacters: 500, query: topic },
    startPublishedDate: "2024-01-01T00:00:00.000Z",
  });

  // Phase 2: Find similar to best result
  const topUrl = sources.results[0]?.url;
  const similar = topUrl
    ? await exa.findSimilarAndContents(topUrl, {
        numResults: 5,
        text: { maxCharacters: 1500 },
        excludeSourceDomain: true,
      })
    : { results: [] };

  // Phase 3: Get AI answer with citations
  const answer = await exa.answer(
    `Based on recent research, summarize: ${topic}`,
    { text: true }
  );

  return {
    primary: sources.results,
    related: similar.results,
    aiSummary: answer.answer,
    sources: answer.results.map(r => ({ title: r.title, url: r.url })),
  };
}
```

### Step 3: RAG Integration Pattern
```typescript
// src/exa/rag.ts
export async function ragSearch(userQuery: string, contextWindow = 5) {
  const results = await exa.searchAndContents(userQuery, {
    type: "neural",
    numResults: contextWindow,
    text: { maxCharacters: 2000 },
    highlights: { maxCharacters: 500, query: userQuery },
  });

  // Format for LLM context injection
  const context = results.results
    .map((r, i) =>
      `[Source ${i + 1}] ${r.title}\n` +
      `URL: ${r.url}\n` +
      `Content: ${r.text}\n` +
      `Key points: ${r.highlights?.join(" | ")}`
    )
    .join("\n\n---\n\n");

  return {
    context,
    sources: results.results.map(r => ({
      title: r.title,
      url: r.url,
      score: r.score,
    })),
  };
}
```

### Step 4: Domain-Specific Search Profiles
```typescript
const SEARCH_PROFILES = {
  technical: {
    includeDomains: [
      "github.com", "stackoverflow.com", "arxiv.org",
      "developer.mozilla.org", "docs.python.org",
    ],
  },
  news: {
    category: "news" as const,
    includeDomains: ["techcrunch.com", "theverge.com", "arstechnica.com"],
  },
  research: {
    category: "research paper" as const,
    includeDomains: ["arxiv.org", "nature.com", "science.org"],
  },
  companies: {
    category: "company" as const,
  },
};

export async function profiledSearch(
  query: string,
  profile: keyof typeof SEARCH_PROFILES
) {
  const config = SEARCH_PROFILES[profile];
  return searchWithContents({ query, ...config, numResults: 10 });
}
```

### Step 5: Competitor Discovery
```typescript
export async function discoverCompetitors(companyUrl: string) {
  const similar = await exa.findSimilarAndContents(companyUrl, {
    numResults: 10,
    excludeSourceDomain: true,
    text: { maxCharacters: 500 },
    summary: { query: "What does this company do?" },
  });

  return similar.results.map(r => ({
    name: r.title,
    url: r.url,
    description: r.summary || r.text?.substring(0, 200),
    score: r.score,
  }));
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No results | Query too specific | Broaden query, switch to neural search |
| Low relevance | Wrong search type | Use `auto` type for hybrid results |
| Empty text/highlights | Site blocks scraping | Use `livecrawl: "preferred"` or try `summary` |
| Rate limit | Too many concurrent requests | Add request queue with 8-10 concurrency |

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa Search Types](https://docs.exa.ai/reference/search)
- [Exa Contents Retrieval](https://docs.exa.ai/reference/contents-retrieval)

## Next Steps
For architecture variants at different scales, see `exa-architecture-variants`.
