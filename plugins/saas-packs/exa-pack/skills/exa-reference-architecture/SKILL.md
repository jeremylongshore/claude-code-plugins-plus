---
name: exa-reference-architecture
description: |
  Implement Exa reference architecture with best-practice project layout.
  Use when designing new Exa integrations, reviewing project structure,
  or establishing architecture standards for Exa applications.
  Trigger with phrases like "exa architecture", "exa best practices",
  "exa project structure", "how to organize exa", "exa layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Exa Reference Architecture

## Overview
Production architecture for Exa neural search integration. Covers search pipeline design, content extraction patterns, embedding-based retrieval, and caching strategies for semantic search applications.

## Prerequisites
- Exa API key
- Understanding of neural vs keyword search
- TypeScript project with async support
- Cache layer for search result deduplication

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                Application Layer                     │
│   RAG Pipeline │ Research Agent │ Content Discovery  │
└───────────┬─────────────┬────────────┬──────────────┘
            │             │            │
            ▼             ▼            ▼
┌─────────────────────────────────────────────────────┐
│              Exa Search Service                      │
│  ┌───────────┐  ┌───────────┐  ┌────────────────┐   │
│  │ Neural    │  │ Keyword   │  │ Auto (hybrid)  │   │
│  │ Search    │  │ Search    │  │ Search         │   │
│  └─────┬─────┘  └─────┬─────┘  └──────┬─────────┘   │
│        │              │               │              │
│        ▼              ▼               ▼              │
│  ┌──────────────────────────────────────────────┐    │
│  │           Content Extraction                  │    │
│  │   Text │ Highlights │ Full HTML │ Summary    │    │
│  └──────────────────────┬───────────────────────┘    │
│                         │                            │
│  ┌──────────────────────┴───────────────────────┐    │
│  │           Result Cache (LRU + Redis)          │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Exa Client Service Layer
```typescript
import Exa from 'exa-js';

const exa = new Exa(process.env.EXA_API_KEY!);

interface SearchOptions {
  query: string;
  type?: 'neural' | 'keyword' | 'auto';
  numResults?: number;
  startDate?: string;
  endDate?: string;
  includeDomains?: string[];
  excludeDomains?: string[];
  category?: string;
}

async function searchWithContents(options: SearchOptions) {
  return exa.searchAndContents(options.query, {
    type: options.type || 'auto',
    numResults: options.numResults || 10,
    text: { maxCharacters: 3000 },
    highlights: { numSentences: 3 },
    startPublishedDate: options.startDate,
    endPublishedDate: options.endDate,
    includeDomains: options.includeDomains,
    excludeDomains: options.excludeDomains,
    category: options.category,
  });
}
```

### Step 2: Search Pipeline with Content Extraction
```typescript
async function researchTopic(topic: string) {
  // Step 1: Broad neural search for relevant sources
  const sources = await exa.searchAndContents(topic, {
    type: 'neural',
    numResults: 20,
    text: true,
    highlights: { numSentences: 5 },
    startPublishedDate: '2024-01-01',
    category: 'research paper',
  });

  // Step 2: Find similar content to top results
  const topUrl = sources.results[0]?.url;
  const similar = topUrl
    ? await exa.findSimilarAndContents(topUrl, {
        numResults: 5,
        text: { maxCharacters: 2000 },
      })
    : { results: [] };

  return {
    primary: sources.results,
    similar: similar.results,
    totalSources: sources.results.length + similar.results.length,
  };
}
```

### Step 3: RAG Integration Pattern
```typescript
async function ragSearch(
  userQuery: string,
  contextWindow = 5
) {
  const results = await exa.searchAndContents(userQuery, {
    type: 'neural',
    numResults: contextWindow,
    text: { maxCharacters: 2000 },
    highlights: { numSentences: 3 },
  });

  // Format for LLM context injection
  const context = results.results.map((r, i) => (
    `[Source ${i + 1}] ${r.title}\n` +
    `URL: ${r.url}\n` +
    `Content: ${r.text}\n` +
    `Key highlights: ${r.highlights?.join(' | ')}\n`
  )).join('\n---\n');

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

### Step 4: Domain-Specific Search Configuration
```typescript
const SEARCH_PROFILES = {
  technical: {
    includeDomains: ['github.com', 'stackoverflow.com', 'arxiv.org', 'docs.python.org'],
    category: 'github repo' as const,
  },
  news: {
    includeDomains: ['techcrunch.com', 'theverge.com', 'arstechnica.com'],
    category: 'news' as const,
  },
  research: {
    includeDomains: ['arxiv.org', 'scholar.google.com', 'nature.com'],
    category: 'research paper' as const,
  },
};

async function profiledSearch(query: string, profile: keyof typeof SEARCH_PROFILES) {
  const config = SEARCH_PROFILES[profile];
  return searchWithContents({ query, ...config, numResults: 10 });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No results | Query too specific | Broaden query, switch to neural search |
| Low relevance | Wrong search type | Use `auto` type for hybrid results |
| Content extraction empty | Site blocks scraping | Use highlights instead of full text |
| Rate limit | Too many concurrent requests | Add request queue with delays |

## Examples

### Content Discovery Pipeline
```typescript
async function discoverCompetitors(companyUrl: string) {
  const similar = await exa.findSimilar(companyUrl, {
    numResults: 10,
    excludeDomains: [new URL(companyUrl).hostname],
  });
  return similar.results.map(r => ({ title: r.title, url: r.url }));
}
```

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa Search Types](https://docs.exa.ai/reference/search)
- [Exa Content Extraction](https://docs.exa.ai/reference/contents)
