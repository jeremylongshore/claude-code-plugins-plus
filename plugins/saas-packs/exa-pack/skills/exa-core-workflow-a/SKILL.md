---
name: exa-core-workflow-a
description: |
  Execute Exa neural search with contents, date filters, and domain scoping.
  Use when building search features, implementing RAG context retrieval,
  or querying the web with semantic understanding.
  Trigger with phrases like "exa search", "exa neural search",
  "search with exa", "exa searchAndContents", "exa query".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, workflow, neural-search, search]

---
# Exa Core Workflow A — Neural Search

## Overview
Primary workflow for Exa: semantic web search using `search()` and `searchAndContents()`. Exa's neural search understands query meaning rather than matching keywords, making it ideal for research, RAG pipelines, and content discovery. This skill covers search types, content extraction, filtering, and categories.

## Prerequisites
- `exa-js` installed and `EXA_API_KEY` configured
- Understanding of neural vs keyword search tradeoffs

## Search Types

| Type | Latency | Best For |
|------|---------|----------|
| `auto` (default) | 300-1500ms | General queries; Exa picks best approach |
| `neural` | 500-2000ms | Conceptual/semantic queries |
| `keyword` | 200-500ms | Exact terms, names, URLs |
| `fast` | p50 < 425ms | Speed-critical applications |
| `instant` | < 150ms | Real-time autocomplete |
| `deep` | 2-5s | Maximum quality, light deep search |
| `deep-reasoning` | 5-15s | Complex research questions |

## Instructions

### Step 1: Basic Neural Search
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

// Neural search: phrase your query as a statement, not a question
const results = await exa.search(
  "comprehensive guide to building production RAG systems",
  {
    type: "neural",
    numResults: 10,   // max 100 for neural/deep
  }
);

for (const r of results.results) {
  console.log(`[${r.score.toFixed(2)}] ${r.title} — ${r.url}`);
  console.log(`  Published: ${r.publishedDate || "unknown"}`);
}
```

### Step 2: Search with Content Extraction
```typescript
// searchAndContents returns page text, highlights, and/or summaries
const results = await exa.searchAndContents(
  "best practices for vector database selection",
  {
    type: "auto",
    numResults: 5,
    // Text: full page content as markdown
    text: { maxCharacters: 2000 },
    // Highlights: key excerpts relevant to a custom query
    highlights: {
      maxCharacters: 500,
      query: "comparison of vector databases",
    },
    // Summary: LLM-generated summary tailored to a query
    summary: { query: "which vector database should I choose?" },
  }
);

for (const r of results.results) {
  console.log(`## ${r.title}`);
  console.log(`Summary: ${r.summary}`);
  console.log(`Highlights: ${r.highlights?.join(" ... ")}`);
  console.log(`Full text: ${r.text?.substring(0, 300)}...`);
}
```

### Step 3: Date and Domain Filtering
```typescript
// Filter by publication date and restrict to specific domains
const results = await exa.searchAndContents(
  "TypeScript 5.5 new features",
  {
    type: "auto",
    numResults: 10,
    // Date filters use ISO 8601 format
    startPublishedDate: "2024-06-01T00:00:00.000Z",
    endPublishedDate: "2025-01-01T00:00:00.000Z",
    // Domain filters (up to 1200 domains each)
    includeDomains: ["devblogs.microsoft.com", "typescriptlang.org"],
    // Text content filters (1 string, max 5 words each)
    includeText: ["TypeScript"],
    text: true,
  }
);
```

### Step 4: Category-Scoped Search
```typescript
// Categories narrow results to specific content types
// Available: company, research paper, news, tweet, personal site,
//            financial report, people
const papers = await exa.searchAndContents(
  "attention mechanism improvements for long context LLMs",
  {
    type: "neural",
    numResults: 10,
    category: "research paper",
    text: { maxCharacters: 3000 },
    highlights: true,
  }
);

const companies = await exa.search(
  "AI infrastructure startup founded 2024",
  {
    type: "auto",
    numResults: 10,
    category: "company",
    // Note: company and people categories do NOT support date filters
  }
);
```

### Step 5: Content Freshness with LiveCrawl
```typescript
// Control whether Exa fetches fresh content or uses cache
const results = await exa.searchAndContents(
  "latest AI model releases this week",
  {
    numResults: 5,
    text: { maxCharacters: 1500 },
    // maxAgeHours controls freshness (replaces deprecated livecrawl)
    // 0 = always crawl fresh, -1 = never crawl, positive = max cache age
    livecrawl: "preferred",     // try fresh, fall back to cache
    livecrawlTimeout: 10000,    // 10s timeout for live crawling
  }
);
```

## Output
- Ranked search results with URLs, titles, scores, and published dates
- Optional text content, highlights, and summaries per result
- Results filtered by date range, domains, categories, and text content

## Error Handling
| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `INVALID_REQUEST_BODY` | 400 | Invalid parameter types | Check query is string, numResults is integer |
| `INVALID_NUM_RESULTS` | 400 | numResults > 100 with highlights | Reduce numResults or remove highlights |
| Empty results array | 200 | Date filter too narrow | Widen date range or remove filter |
| Low relevance scores | 200 | Keyword-style query | Rephrase as natural language statement |
| `FETCH_DOCUMENT_ERROR` | 422 | URL content unretrievable | Use `livecrawl: "fallback"` or try without text |

## Examples

### RAG Context Retrieval
```typescript
async function getRAGContext(question: string, maxResults = 5) {
  const results = await exa.searchAndContents(question, {
    type: "neural",
    numResults: maxResults,
    text: { maxCharacters: 2000 },
    highlights: { maxCharacters: 500, query: question },
  });

  return results.results.map((r, i) => ({
    source: `[${i + 1}] ${r.title} (${r.url})`,
    content: r.text,
    highlights: r.highlights,
  }));
}
```

## Resources
- [Exa Search Reference](https://docs.exa.ai/reference/search)
- [Exa Contents Retrieval](https://docs.exa.ai/reference/contents-retrieval)
- [Exa Search Types](https://docs.exa.ai/reference/search)

## Next Steps
For similarity search and advanced retrieval, see `exa-core-workflow-b`.
