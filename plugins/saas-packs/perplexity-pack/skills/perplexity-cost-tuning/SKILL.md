---
name: perplexity-cost-tuning
description: |
  Optimize Perplexity costs through model routing, caching, token limits, and budget monitoring.
  Use when analyzing Perplexity billing, reducing API costs,
  or implementing budget alerts for Perplexity Sonar API.
  Trigger with phrases like "perplexity cost", "perplexity billing",
  "reduce perplexity costs", "perplexity pricing", "perplexity budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, api, monitoring, cost-optimization]

---
# Perplexity Cost Tuning

## Overview
Reduce Perplexity Sonar API costs. Perplexity charges per-token (input + output) plus a per-request fee that varies by search context size. The biggest cost lever is model selection: `sonar-pro` costs 3-15x more than `sonar` per request.

## Pricing Reference

| Model | Input $/M tokens | Output $/M tokens | Request Fee |
|-------|-------------------|-------------------|-------------|
| `sonar` | $1 | $1 | $5 per 1K requests |
| `sonar-pro` | $3 | $15 | $5 per 1K requests |
| `sonar-reasoning-pro` | $3 | $15 | $5 per 1K requests |
| `sonar-deep-research` | $2 | $8 | $5 per 1K searches |

Search context size (Low/Medium/High) affects the request fee. More context = higher fee.

## Prerequisites
- Perplexity API account with usage dashboard
- Understanding of query patterns in your application
- Cache infrastructure for search results

## Instructions

### Step 1: Route Queries to the Right Model
```typescript
// 60-70% of queries can use sonar, saving 3-15x per query
function selectModel(query: string): "sonar" | "sonar-pro" {
  const simplePatterns = [
    /^what is/i, /^define/i, /^who is/i, /^when did/i,
    /current price/i, /^how many/i, /^is it true/i,
  ];
  if (simplePatterns.some((p) => p.test(query))) return "sonar";

  const complexPatterns = [
    /compare.*vs/i, /analysis of/i, /comprehensive/i,
    /pros and cons/i, /in-depth/i, /research/i,
  ];
  if (complexPatterns.some((p) => p.test(query))) return "sonar-pro";

  return "sonar"; // Default to cheapest
}
```

### Step 2: Limit Output Tokens
```bash
set -euo pipefail
# Factual queries need ~100 tokens, not 4096
# Setting max_tokens dramatically reduces output costs

# Simple fact: 100 tokens = $0.0001 output
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar",
    "messages": [{"role": "user", "content": "Current population of Tokyo"}],
    "max_tokens": 100
  }'

# Research query: keep at 2048 only when needed
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-pro",
    "messages": [{"role": "user", "content": "Compare React vs Vue in 2025 for enterprise apps"}],
    "max_tokens": 2048
  }'
```

### Step 3: Cache to Eliminate Duplicate Queries
```typescript
import { LRUCache } from "lru-cache";
import { createHash } from "crypto";

const searchCache = new LRUCache<string, any>({
  max: 10000,
  ttl: 4 * 3600_000, // 4-hour default TTL
});

async function cachedQuery(query: string, model: string) {
  const key = createHash("sha256")
    .update(`${model}:${query.toLowerCase().trim()}`)
    .digest("hex");

  const cached = searchCache.get(key);
  if (cached) return cached; // $0 cost

  const result = await perplexity.chat.completions.create({
    model,
    messages: [{ role: "user", content: query }],
  });
  searchCache.set(key, result);
  return result;
}

// Track cache effectiveness
function cacheStats() {
  return {
    size: searchCache.size,
    hitRate: `${((searchCache as any).hits / ((searchCache as any).hits + (searchCache as any).misses) * 100).toFixed(1)}%`,
  };
}
```

### Step 4: Use Domain Filters to Reduce Search Cost
```bash
set -euo pipefail
# Restricting search domains = less content to process = lower request fee
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar",
    "messages": [{"role": "user", "content": "Python 3.13 release notes"}],
    "search_domain_filter": ["python.org", "docs.python.org"],
    "max_tokens": 500
  }'
```

### Step 5: Track and Budget
```typescript
class CostTracker {
  private costs: Array<{ model: string; tokens: number; timestamp: Date }> = [];

  record(model: string, usage: { total_tokens: number }) {
    this.costs.push({
      model,
      tokens: usage.total_tokens,
      timestamp: new Date(),
    });
  }

  dailySummary() {
    const today = this.costs.filter(
      (c) => c.timestamp.toDateString() === new Date().toDateString()
    );
    const sonarTokens = today.filter((c) => c.model === "sonar").reduce((s, c) => s + c.tokens, 0);
    const proTokens = today.filter((c) => c.model === "sonar-pro").reduce((s, c) => s + c.tokens, 0);

    return {
      queries: today.length,
      estimatedCost: (sonarTokens * 0.000001) + (proTokens * 0.000009), // rough estimate
      sonarQueries: today.filter((c) => c.model === "sonar").length,
      proQueries: today.filter((c) => c.model === "sonar-pro").length,
    };
  }
}
```

## Cost Optimization Checklist
- [ ] Default model is `sonar` (not `sonar-pro`)
- [ ] `max_tokens` set on every request
- [ ] Caching enabled for repeated queries
- [ ] Model routing by query complexity
- [ ] Domain filter used where applicable
- [ ] Monthly budget cap set on API key
- [ ] Cost tracking in production monitoring

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High cost per query | Using sonar-pro for everything | Route simple queries to sonar |
| Low cache hit rate | Queries too unique | Normalize queries before hashing |
| Budget exhausted early | No spending caps | Set monthly budget on API key |
| Unexpectedly high bill | No max_tokens limits | Set max_tokens on all requests |

## Output
- Model routing saving 60-70% on simple queries
- Token limiting reducing output costs
- Caching eliminating duplicate query costs
- Cost tracking for budget monitoring

## Resources
- [Perplexity Pricing](https://docs.perplexity.ai/docs/getting-started/pricing)
- [Model Cards](https://docs.perplexity.ai/getting-started/models)

## Next Steps
For architecture patterns, see `perplexity-reference-architecture`.
