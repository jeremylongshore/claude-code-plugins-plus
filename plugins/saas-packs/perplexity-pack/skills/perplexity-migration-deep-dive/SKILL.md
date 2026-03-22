---
name: perplexity-migration-deep-dive
description: |
  Migrate to Perplexity Sonar from other search/LLM APIs using the strangler fig pattern.
  Use when switching from Google Custom Search, Bing API, or other LLMs to Perplexity,
  or migrating from legacy pplx-api models.
  Trigger with phrases like "migrate to perplexity", "switch to perplexity",
  "replace search API with perplexity", "perplexity replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, migration]

---
# Perplexity Migration Deep Dive

## Current State
!`npm list openai 2>/dev/null | grep openai || echo 'N/A'`
!`grep -rn "google.*search\|bing.*api\|serpapi\|pplx-7b\|pplx-70b" --include="*.ts" --include="*.py" . 2>/dev/null | head -5 || echo 'No legacy search APIs found'`

## Overview
Migrate from traditional search APIs (Google Custom Search, Bing, SerpAPI) or legacy LLMs to Perplexity Sonar. Key advantage: Perplexity combines search + LLM summarization in a single API call, replacing a multi-step pipeline.

## Migration Comparison

| Feature | Google CSE / Bing | Perplexity Sonar |
|---------|-------------------|------------------|
| Returns | Raw search results (links + snippets) | Synthesized answer + citations |
| Answer generation | Requires separate LLM call | Built-in |
| Citation handling | Manual extraction | Automatic `citations` array |
| Cost structure | Per-search ($5/1K queries) | Per-token + per-request |
| Recency filter | Date range parameters | `search_recency_filter` |
| Domain filter | Site restriction | `search_domain_filter` |

## Instructions

### Step 1: Assess Current Integration
```bash
set -euo pipefail
# Find existing search API usage
grep -rn "googleapis.*customsearch\|bing.*search\|serpapi\|serper\|tavily" \
  --include="*.ts" --include="*.py" --include="*.js" \
  . 2>/dev/null || echo "No search APIs found"

# Count integration points
grep -rln "search.*api\|customsearch\|bing.*web" \
  --include="*.ts" --include="*.py" --include="*.js" \
  . 2>/dev/null | wc -l
```

### Step 2: Build Adapter Layer
```typescript
// src/search/adapter.ts
export interface SearchResult {
  answer: string;
  citations: string[];
  rawResults?: Array<{ title: string; url: string; snippet: string }>;
}

export interface SearchAdapter {
  search(query: string, opts?: { recency?: string; domains?: string[] }): Promise<SearchResult>;
}

// Legacy adapter (existing Google/Bing implementation)
class GoogleSearchAdapter implements SearchAdapter {
  async search(query: string): Promise<SearchResult> {
    // Existing Google CSE code
    const results = await googleCustomSearch(query);
    return {
      answer: "", // No built-in answer generation
      citations: results.items.map((i: any) => i.link),
      rawResults: results.items.map((i: any) => ({
        title: i.title,
        url: i.link,
        snippet: i.snippet,
      })),
    };
  }
}

// New Perplexity adapter
class PerplexitySearchAdapter implements SearchAdapter {
  private client: OpenAI;

  constructor() {
    this.client = new OpenAI({
      apiKey: process.env.PERPLEXITY_API_KEY!,
      baseURL: "https://api.perplexity.ai",
    });
  }

  async search(query: string, opts?: { recency?: string; domains?: string[] }): Promise<SearchResult> {
    const response = await this.client.chat.completions.create({
      model: "sonar",
      messages: [{ role: "user", content: query }],
      ...(opts?.recency && { search_recency_filter: opts.recency }),
      ...(opts?.domains && { search_domain_filter: opts.domains }),
    } as any);

    return {
      answer: response.choices[0].message.content || "",
      citations: (response as any).citations || [],
      rawResults: (response as any).search_results || [],
    };
  }
}
```

### Step 3: Feature Flag Traffic Split
```typescript
// src/search/factory.ts
function getSearchAdapter(): SearchAdapter {
  const perplexityPercent = parseInt(process.env.PERPLEXITY_TRAFFIC_PERCENT || "0");

  if (Math.random() * 100 < perplexityPercent) {
    return new PerplexitySearchAdapter();
  }
  return new GoogleSearchAdapter();
}

// Migration schedule:
// Week 1: PERPLEXITY_TRAFFIC_PERCENT=10  (canary)
// Week 2: PERPLEXITY_TRAFFIC_PERCENT=50  (half traffic)
// Week 3: PERPLEXITY_TRAFFIC_PERCENT=100 (full migration)
// Week 4: Remove Google adapter code
```

### Step 4: Validate Migration Quality
```typescript
// Compare results between old and new adapter
async function compareSearchResults(query: string): Promise<{
  perplexity: SearchResult;
  google: SearchResult;
  citationOverlap: number;
}> {
  const [perplexity, google] = await Promise.all([
    new PerplexitySearchAdapter().search(query),
    new GoogleSearchAdapter().search(query),
  ]);

  // Check citation overlap (shared domains)
  const pplxDomains = new Set(perplexity.citations.map((u) => new URL(u).hostname));
  const googleDomains = new Set(google.citations.map((u) => new URL(u).hostname));
  const overlap = [...pplxDomains].filter((d) => googleDomains.has(d)).length;

  return {
    perplexity,
    google,
    citationOverlap: overlap / Math.max(pplxDomains.size, 1),
  };
}
```

### Step 5: Simplify Post-Migration
```typescript
// Before migration: 3-step pipeline
// 1. Google Custom Search API → raw results
// 2. Send results to LLM for summarization
// 3. Extract citations manually

// After migration: 1-step
async function search(query: string): Promise<{ answer: string; sources: string[] }> {
  const client = new OpenAI({
    apiKey: process.env.PERPLEXITY_API_KEY!,
    baseURL: "https://api.perplexity.ai",
  });

  const response = await client.chat.completions.create({
    model: "sonar",
    messages: [{ role: "user", content: query }],
  });

  return {
    answer: response.choices[0].message.content || "",
    sources: (response as any).citations || [],
  };
}
```

## Rollback Plan
```bash
set -euo pipefail
# Instant rollback: set traffic to 0%
# kubectl set env deployment/search-app PERPLEXITY_TRAFFIC_PERCENT=0
# The adapter layer keeps both implementations live until decommissioned
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Citation format differs | Google returns titles, Perplexity returns URLs | Normalize in adapter |
| No raw results | Perplexity returns synthesized answer | Use `search_results` field if available |
| Higher latency | Perplexity does search + synthesis | Expected; cache to compensate |
| Cost increase | Perplexity uses more tokens | Route simple queries to sonar, limit max_tokens |

## Output
- Adapter layer abstracting search implementations
- Feature-flagged traffic split for gradual migration
- Quality comparison between old and new search
- Simplified single-API architecture post-migration

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

## Next Steps
For advanced troubleshooting, see `perplexity-advanced-troubleshooting`.
