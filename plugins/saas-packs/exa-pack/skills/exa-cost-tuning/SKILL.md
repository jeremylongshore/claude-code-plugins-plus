---
name: exa-cost-tuning
description: |
  Optimize Exa costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Exa billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "exa cost", "exa billing",
  "reduce exa costs", "exa pricing", "exa expensive", "exa budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Exa Cost Tuning

## Overview
Reduce Exa AI search API costs by implementing caching, choosing the right search type, and limiting result count per query. Exa charges per search with costs varying by plan tier. The biggest cost levers are: caching repeated queries (RAG pipelines often search for the same topics), reducing `numResults` to only what's needed (each result adds content retrieval cost), and using `keyword` search instead of `neural` when exact matching suffices (keyword is faster and cheaper).

## Prerequisites
- Exa API account with usage dashboard access
- Understanding of search patterns in your application
- Cache infrastructure (Redis or in-memory)

## Instructions

### Step 1: Implement Query-Level Caching
```typescript
import { LRUCache } from 'lru-cache';

const searchCache = new LRUCache<string, any>({ max: 5000, ttl: 3600_000 }); // 1hr TTL

async function cachedSearch(query: string, options: any) {
  const cacheKey = `${query}:${options.type}:${options.numResults}`;
  const cached = searchCache.get(cacheKey);
  if (cached) return cached;

  const results = await exa.search(query, options);
  searchCache.set(cacheKey, results);
  return results;
}
// Typical cache hit rate for RAG: 40-60%, directly reducing search costs by half
```

### Step 2: Minimize Results Per Query
```typescript
// Don't fetch more results than you'll actually use
const SEARCH_CONFIGS: Record<string, { numResults: number; type: string }> = {
  'rag-context':    { numResults: 3, type: 'neural' },   // RAG only needs top 3
  'research-deep':  { numResults: 10, type: 'neural' },  // Research needs more
  'fact-check':     { numResults: 5, type: 'keyword' },   // Exact match is cheaper
  'autocomplete':   { numResults: 3, type: 'keyword' },   // Quick suggestions
};
```

### Step 3: Use Keyword Search When Appropriate
```bash
# Neural search: best for semantic/conceptual queries (more expensive)
curl -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -d '{"query": "best practices for microservices", "type": "neural", "numResults": 5}'

# Keyword search: best for specific terms/names (cheaper, faster)
curl -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -d '{"query": "RFC 9110 HTTP semantics", "type": "keyword", "numResults": 3}'
```

### Step 4: Deduplicate Searches in Batch Pipelines
```typescript
// If processing 1000 documents, many will need similar context searches
function deduplicateSearches(queries: string[]): string[] {
  const seen = new Set<string>();
  return queries.filter(q => {
    const normalized = q.toLowerCase().trim();
    if (seen.has(normalized)) return false;
    seen.add(normalized);
    return true;
  });
}
// Typical dedup rate: 20-40% for batch processing pipelines
```

### Step 5: Monitor and Budget
```bash
# Check remaining budget and project monthly cost
curl -s https://api.exa.ai/v1/usage \
  -H "x-api-key: $EXA_API_KEY" | \
  jq '{
    searches_today: .searches_today,
    monthly_total: .searches_this_month,
    monthly_limit: .monthly_limit,
    utilization_pct: (.searches_this_month / .monthly_limit * 100),
    days_remaining: (30 - (.searches_this_month / .monthly_limit * 30))
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Monthly limit hit early | Uncached pipeline queries | Add query caching, expect 40%+ savings |
| High cost per useful result | `numResults` too high | Reduce to 3-5 for most use cases |
| Cache hit rate low | Highly variable queries | Normalize queries before caching |
| Budget spike from batch job | No search deduplication | Deduplicate queries before batch execution |

## Examples
```bash
# Cost comparison: neural vs keyword for same query
echo "Neural:" && time curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -d '{"query": "python async programming", "type": "neural", "numResults": 3}' -o /dev/null
echo "Keyword:" && time curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -d '{"query": "python async programming", "type": "keyword", "numResults": 3}' -o /dev/null
```
