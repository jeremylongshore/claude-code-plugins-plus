---
name: exa-migration-deep-dive
description: |
  Migrate from other search APIs (Google, Bing, Tavily, Serper) to Exa neural search.
  Use when switching to Exa from another search provider, migrating search pipelines,
  or evaluating Exa as a replacement for traditional search APIs.
  Trigger with phrases like "migrate to exa", "switch to exa", "replace google search with exa",
  "exa vs tavily", "exa migration", "move to exa".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, migration]

---
# Exa Migration Deep Dive

## Current State
!`npm list exa-js 2>/dev/null | grep exa-js || echo 'exa-js not installed'`
!`npm list 2>/dev/null | grep -E '(google|bing|tavily|serper|serpapi)' || echo 'No competing search SDK found'`

## Overview
Migrate from traditional search APIs (Google Custom Search, Bing Web Search, Tavily, Serper) to Exa's neural search API. Key differences: Exa uses semantic/neural search instead of keyword matching, returns content (text/highlights/summary) in a single API call, and supports similarity search from a seed URL.

## API Comparison

| Feature | Google/Bing | Tavily | Exa |
|---------|-------------|--------|-----|
| Search model | Keyword | AI-enhanced | Neural embeddings |
| Content in results | Snippets only | Full text | Text + highlights + summary |
| Similarity search | No | No | `findSimilar()` by URL |
| AI answer | No | Yes | `answer()` + `streamAnswer()` |
| Categories | No | No | company, news, research paper, tweet, people |
| Date filtering | Limited | Yes | `startPublishedDate` / `endPublishedDate` |
| Domain filtering | Yes | Yes | `includeDomains` / `excludeDomains` (up to 1200) |

## Instructions

### Step 1: Install Exa SDK
```bash
set -euo pipefail
npm install exa-js
# Remove old SDK if replacing
# npm uninstall google-search-api tavily serpapi
```

### Step 2: Create Adapter Layer
```typescript
// src/search/adapter.ts
import Exa from "exa-js";

// Define a provider-agnostic search interface
interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  score?: number;
  publishedDate?: string;
}

interface SearchResponse {
  results: SearchResult[];
  query: string;
}

// Exa implementation
class ExaSearchAdapter {
  private exa: Exa;

  constructor(apiKey: string) {
    this.exa = new Exa(apiKey);
  }

  async search(query: string, numResults = 10): Promise<SearchResponse> {
    const response = await this.exa.searchAndContents(query, {
      type: "auto",
      numResults,
      text: { maxCharacters: 500 },
      highlights: { maxCharacters: 300, query },
    });

    return {
      query,
      results: response.results.map(r => ({
        title: r.title || "Untitled",
        url: r.url,
        snippet: r.highlights?.join(" ") || r.text?.substring(0, 300) || "",
        score: r.score,
        publishedDate: r.publishedDate || undefined,
      })),
    };
  }

  // Exa-only: similarity search (no equivalent in Google/Bing)
  async findSimilar(url: string, numResults = 5): Promise<SearchResponse> {
    const response = await this.exa.findSimilarAndContents(url, {
      numResults,
      text: { maxCharacters: 500 },
      excludeSourceDomain: true,
    });

    return {
      query: url,
      results: response.results.map(r => ({
        title: r.title || "Untitled",
        url: r.url,
        snippet: r.text?.substring(0, 300) || "",
        score: r.score,
      })),
    };
  }
}
```

### Step 3: Feature Flag Traffic Shift
```typescript
// src/search/router.ts
function getSearchProvider(): "legacy" | "exa" {
  const exaPercentage = Number(process.env.EXA_TRAFFIC_PERCENTAGE || "0");
  return Math.random() * 100 < exaPercentage ? "exa" : "legacy";
}

async function search(query: string, numResults = 10): Promise<SearchResponse> {
  const provider = getSearchProvider();

  if (provider === "exa") {
    return exaAdapter.search(query, numResults);
  }
  return legacyAdapter.search(query, numResults);
}

// Gradually increase: 0% → 10% → 50% → 100%
// EXA_TRAFFIC_PERCENTAGE=10
```

### Step 4: Query Translation
```typescript
// Exa neural search works best with natural language, not keyword syntax
function translateQuery(legacyQuery: string): string {
  return legacyQuery
    // Remove boolean operators (Exa doesn't use them)
    .replace(/\b(AND|OR|NOT)\b/gi, " ")
    // Remove quotes (Exa uses semantic matching, not exact)
    .replace(/"/g, "")
    // Remove site: operator (use includeDomains instead)
    .replace(/site:\S+/gi, "")
    // Clean up extra whitespace
    .replace(/\s+/g, " ")
    .trim();
}

// Extract domain filters from legacy query
function extractDomainFilter(query: string): string[] {
  const domains: string[] = [];
  const siteMatches = query.matchAll(/site:(\S+)/gi);
  for (const match of siteMatches) {
    domains.push(match[1]);
  }
  return domains;
}
```

### Step 5: Validation and Comparison
```typescript
async function compareResults(query: string) {
  const [legacyResults, exaResults] = await Promise.all([
    legacyAdapter.search(query, 5),
    exaAdapter.search(query, 5),
  ]);

  // Compare URL overlap
  const legacyUrls = new Set(legacyResults.results.map(r => new URL(r.url).hostname));
  const exaUrls = new Set(exaResults.results.map(r => new URL(r.url).hostname));
  const overlap = [...legacyUrls].filter(u => exaUrls.has(u));

  console.log(`Legacy results: ${legacyResults.results.length}`);
  console.log(`Exa results: ${exaResults.results.length}`);
  console.log(`Domain overlap: ${overlap.length}/${legacyUrls.size}`);

  return { legacyResults, exaResults, overlapRate: overlap.length / legacyUrls.size };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Lower result count | Exa filters more aggressively | Increase `numResults` |
| Different ranking | Neural vs keyword ranking | Expected — evaluate by relevance |
| Boolean queries fail | Exa doesn't support AND/OR | Translate to natural language |
| Missing `site:` filter | Different API parameter | Use `includeDomains` parameter |

## Resources
- [Exa vs Tavily Comparison](https://exa.ai/versus/tavily)
- [Exa Search Reference](https://docs.exa.ai/reference/search)
- [exa-js SDK](https://github.com/exa-labs/exa-js)

## Next Steps
For advanced troubleshooting, see `exa-advanced-troubleshooting`.
