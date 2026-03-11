---
name: perplexity-cost-tuning
description: |
  Optimize Perplexity costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Perplexity billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "perplexity cost", "perplexity billing",
  "reduce perplexity costs", "perplexity pricing", "perplexity expensive", "perplexity budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Cost Tuning

## Overview
Reduce Perplexity AI search API costs by choosing the right model per query, caching search results, and limiting token output. Perplexity charges per query with significant cost differences between models: `sonar` (lightweight, cheaper) vs `sonar-pro` (deeper research, 3-5x more expensive). The biggest cost lever is routing simple factual queries to `sonar` and reserving `sonar-pro` for complex research that actually needs multi-source synthesis.

## Prerequisites
- Perplexity API account with usage dashboard
- Understanding of query patterns in your application
- Cache infrastructure for search results

## Instructions

### Step 1: Route Queries to the Right Model
```typescript
// Smart model selection based on query complexity
function selectModel(query: string, context: string): 'sonar' | 'sonar-pro' {
  // Simple factual queries -> sonar (cheap)
  const simplePatterns = [/^what is/i, /^define/i, /^who is/i, /^when did/i, /current price of/i];
  if (simplePatterns.some(p => p.test(query))) return 'sonar';

  // Complex research queries -> sonar-pro (expensive but worth it)
  const complexPatterns = [/compare.*vs/i, /analysis of/i, /comprehensive.*overview/i, /pros and cons/i];
  if (complexPatterns.some(p => p.test(query))) return 'sonar-pro';

  return 'sonar'; // Default to cheaper model
}
// Impact: 60-70% of queries can use sonar, saving 3-5x per query
```

### Step 2: Cache Search Results
```typescript
import { LRUCache } from 'lru-cache';

const searchCache = new LRUCache<string, any>({
  max: 10000,
  ttl: 4 * 3600_000, // 4-hour TTL (search results go stale)
});

async function cachedQuery(query: string, model: string) {
  const key = `${model}:${query.toLowerCase().trim()}`;
  const cached = searchCache.get(key);
  if (cached) return cached;

  const result = await perplexity.chat.completions.create({
    model, messages: [{ role: 'user', content: query }],
  });
  searchCache.set(key, result);
  return result;
}
```

### Step 3: Limit Token Output
```bash
# Set max_tokens to reduce output (and cost) for simple queries
# Factual queries need ~100 tokens, not 4096
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PPLX_API_KEY" \
  -d '{
    "model": "sonar",
    "messages": [{"role": "user", "content": "What is the current population of Tokyo?"}],
    "max_tokens": 100
  }'
# Saves tokens on output; Perplexity charges for both input and output tokens
```

### Step 4: Use Domain Filters to Reduce Processing
```bash
# Restricting search domains means less content to process = faster + cheaper
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PPLX_API_KEY" \
  -d '{
    "model": "sonar",
    "messages": [{"role": "user", "content": "latest Python 3.13 release notes"}],
    "search_domain_filter": ["python.org", "docs.python.org"],
    "max_tokens": 500
  }'
```

### Step 5: Monitor and Budget
```bash
# Track daily spend and project monthly cost
curl -s https://api.perplexity.ai/v1/usage \
  -H "Authorization: Bearer $PPLX_API_KEY" | \
  jq '{
    queries_today: .queries_today,
    cost_today: .cost_today_usd,
    monthly_projection: (.cost_today_usd * 30),
    budget_remaining: .budget_remaining_usd,
    avg_cost_per_query: (.cost_today_usd / (.queries_today + 0.01))
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High cost per query | Using sonar-pro for everything | Route simple queries to sonar |
| Cache hit rate low | Queries too unique | Normalize queries before caching |
| Budget exhausted early | No per-key spending limits | Set monthly budget caps per API key |
| Stale cached results | TTL too long | Reduce cache TTL for time-sensitive queries |

## Examples
```bash
# Cost comparison: sonar vs sonar-pro
echo "1000 simple queries on sonar: ~\$X"
echo "1000 simple queries on sonar-pro: ~\$3-5X"
echo "Savings by routing correctly: 60-80%"
```
