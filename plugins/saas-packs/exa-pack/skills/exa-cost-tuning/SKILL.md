---
name: exa-cost-tuning
description: |
  Optimize Exa costs through search type selection, caching, and usage monitoring.
  Use when analyzing Exa billing, reducing API costs,
  or implementing budget controls and usage alerts.
  Trigger with phrases like "exa cost", "exa billing",
  "reduce exa costs", "exa pricing", "exa expensive", "exa budget".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, api, cost-optimization]

---
# Exa Cost Tuning

## Overview
Reduce Exa API costs through strategic search type selection, result caching, query deduplication, and usage monitoring. Exa charges per search request with costs varying by search type and content retrieval options.

## Cost Drivers

| Factor | Higher Cost | Lower Cost |
|--------|-------------|------------|
| Search type | `deep-reasoning` > `deep` > `neural` | `keyword` < `fast` < `instant` |
| numResults | 10-100 results | 3-5 results |
| Content retrieval | Full text + highlights + summary | Metadata only (no content) |
| Content length | `maxCharacters: 5000` | `maxCharacters: 500` |
| Live crawling | `livecrawl: "always"` | Cached content (default) |

## Instructions

### Step 1: Match Search Config to Use Case
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

// Define cost tiers per use case
const SEARCH_PROFILES = {
  // Cheapest: metadata-only keyword search
  "autocomplete": { type: "instant" as const, numResults: 3 },

  // Low cost: fast search with minimal content
  "quick-lookup": { type: "fast" as const, numResults: 3 },

  // Medium: balanced search for RAG
  "rag-context": {
    type: "auto" as const,
    numResults: 5,
    text: { maxCharacters: 1000 },
  },

  // Higher cost: deep research
  "deep-research": {
    type: "neural" as const,
    numResults: 10,
    text: { maxCharacters: 3000 },
    highlights: { maxCharacters: 500 },
  },
};

async function costAwareSearch(
  query: string,
  profile: keyof typeof SEARCH_PROFILES
) {
  const config = SEARCH_PROFILES[profile];
  if ("text" in config || "highlights" in config) {
    return exa.searchAndContents(query, config);
  }
  return exa.search(query, config);
}
```

### Step 2: Query-Level Caching (40-60% Cost Reduction)
```typescript
import { LRUCache } from "lru-cache";

const searchCache = new LRUCache<string, any>({
  max: 5000,
  ttl: 3600 * 1000, // 1-hour TTL
});

async function cachedSearch(query: string, opts: any) {
  const key = `${query.toLowerCase().trim()}:${opts.type}:${opts.numResults}`;
  const cached = searchCache.get(key);
  if (cached) return cached;

  const results = await exa.searchAndContents(query, opts);
  searchCache.set(key, results);
  return results;
}
// Typical RAG cache hit rate: 40-60%, directly cutting costs in half
```

### Step 3: Query Deduplication for Batch Jobs
```typescript
function deduplicateQueries(queries: string[]): string[] {
  const seen = new Set<string>();
  return queries.filter(q => {
    const normalized = q.toLowerCase().trim().replace(/\s+/g, " ");
    if (seen.has(normalized)) return false;
    seen.add(normalized);
    return true;
  });
}

// Before batch processing, deduplicate
const uniqueQueries = deduplicateQueries(allQueries);
console.log(`Deduped: ${allQueries.length} → ${uniqueQueries.length} queries`);
// Typical dedup rate: 20-40% for batch processing
```

### Step 4: Use Keyword Search When Appropriate
```typescript
// Neural search: best for semantic/conceptual queries (more expensive)
// Keyword search: best for specific terms/names (cheaper, faster)

function selectCostEffectiveType(query: string): "neural" | "keyword" | "auto" {
  // Use keyword for exact lookups
  if (query.match(/^https?:\/\//)) return "keyword";     // URL lookup
  if (query.match(/^[A-Z][a-z]+ [A-Z]/)) return "keyword"; // Proper nouns
  if (query.includes('"')) return "keyword";               // Quoted terms

  // Use neural for conceptual queries
  if (query.split(" ").length > 5) return "neural";
  return "auto"; // Let Exa decide for ambiguous queries
}
```

### Step 5: Monitor Usage and Set Budget Alerts
```bash
set -euo pipefail
# Check API key usage
curl -s https://api.exa.ai/v1/usage \
  -H "x-api-key: $EXA_API_KEY" | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'Searches today: {d.get(\"searches_today\", \"N/A\")}')
print(f'Monthly total: {d.get(\"searches_this_month\", \"N/A\")}')
print(f'Monthly limit: {d.get(\"monthly_limit\", \"N/A\")}')
" 2>/dev/null || echo "Usage endpoint not available"
```

```typescript
// Application-level budget tracking
class ExaBudgetTracker {
  private searchCount = 0;
  private dailyLimit: number;

  constructor(dailyLimit = 1000) {
    this.dailyLimit = dailyLimit;
  }

  async search(exa: Exa, query: string, opts: any) {
    if (this.searchCount >= this.dailyLimit) {
      throw new Error(`Daily Exa budget exceeded (${this.dailyLimit} searches)`);
    }
    this.searchCount++;
    return exa.search(query, opts);
  }

  getUsage() {
    return {
      used: this.searchCount,
      remaining: this.dailyLimit - this.searchCount,
      utilization: `${((this.searchCount / this.dailyLimit) * 100).toFixed(1)}%`,
    };
  }
}
```

## Cost Optimization Checklist
- [ ] Use `keyword` or `fast` for exact lookups instead of `neural`
- [ ] Reduce `numResults` to 3-5 for most use cases (default is 10)
- [ ] Use `highlights` instead of full `text` when snippets suffice
- [ ] Implement query-level caching (LRU or Redis)
- [ ] Deduplicate queries in batch pipelines
- [ ] Set application-level budget limits
- [ ] Monitor daily/monthly usage against budget

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Monthly limit hit early | Uncached batch queries | Add caching (40%+ savings) |
| High cost per result | `numResults` too high | Reduce to 3-5 for most use cases |
| Budget spike from batch | No deduplication | Deduplicate before batch execution |
| `402 NO_MORE_CREDITS` | Account balance exhausted | Top up at dashboard.exa.ai |

## Resources
- [Exa Pricing](https://exa.ai/pricing)
- [Exa API Usage](https://dashboard.exa.ai)
- [Exa Search Types](https://docs.exa.ai/reference/search)

## Next Steps
For performance optimization, see `exa-performance-tuning`. For reliability, see `exa-reliability-patterns`.
