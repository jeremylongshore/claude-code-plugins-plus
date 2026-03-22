---
name: serpapi-cost-tuning
description: |
  Optimize SerpApi costs by reducing credit consumption and choosing the right plan.
  Use when analyzing search usage, reducing monthly costs,
  or implementing credit-saving strategies.
  Trigger: "serpapi cost", "serpapi pricing", "reduce serpapi costs", "serpapi credits".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Cost Tuning

## Overview

SerpApi charges per search (1 credit each). Plans: Free (100/mo), Developer ($75, 5K/mo), Business ($200, 15K/mo), Enterprise (custom). Key savings: caching, archive retrieval (free), and Google Light API.

## Cost Strategies

### Strategy 1: Aggressive Caching (Biggest Savings)

```python
# Search results rarely change within an hour
# Cache for 1 hour = up to 24x credit reduction for hourly queries
# Cache for 1 day = up to 720x for queries checked every 2 minutes

import hashlib, json, redis, serpapi, os

r = redis.Redis.from_url(os.environ["REDIS_URL"])
client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])

def cached_search(ttl_seconds=3600, **params):
    key = f"serpapi:{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
    cached = r.get(key)
    if cached:
        return json.loads(cached)  # FREE: no credit consumed
    result = client.search(**params)   # 1 credit
    r.setex(key, ttl_seconds, json.dumps(dict(result)))
    return result
```

### Strategy 2: Archive API (Free Retrieval)

```python
# Every search result is stored in the archive
# Retrieve by search_id at no cost
archived = client.search(engine="google", search_id="previous_id")
# 0 credits -- use for re-processing or delayed access
```

### Strategy 3: Google Light API (Same Cost, Faster)

```python
# Same 1 credit but faster response (~1s vs 3-5s)
# Good for: organic results only, no knowledge graph needed
result = client.search(engine="google_light", q="query")
```

### Strategy 4: Reduce num Parameter

```python
# Default num=10 (10 results). If you only need top 3:
result = client.search(engine="google", q="query", num=3)
# Still 1 credit, but faster response
```

## Cost Calculator

```python
def estimate_monthly_cost(
    daily_searches: int,
    cache_hit_rate: float = 0.7,  # 70% cache hits typical
) -> dict:
    actual_api_calls = daily_searches * 30 * (1 - cache_hit_rate)
    plans = [
        ("Free", 100, 0), ("Developer", 5000, 75),
        ("Business", 15000, 200), ("Enterprise", 50000, 500),
    ]
    for name, limit, price in plans:
        if actual_api_calls <= limit:
            return {"plan": name, "price": f"${price}/mo",
                    "api_calls": int(actual_api_calls), "raw_searches": daily_searches * 30}
    return {"plan": "Enterprise+", "price": "Custom", "api_calls": int(actual_api_calls)}

# Examples:
# 100 searches/day, 70% cache = 900 API calls/mo = Developer ($75)
# 500 searches/day, 80% cache = 3000 API calls/mo = Developer ($75)
# 1000 searches/day, 50% cache = 15000 API calls/mo = Business ($200)
```

## Usage Monitoring

```bash
# Daily credit check
curl -s "https://serpapi.com/account.json?api_key=$SERPAPI_API_KEY" | jq '{
  plan: .plan_name,
  used: .this_month_usage,
  remaining: .plan_searches_left,
  daily_avg: (.this_month_usage / ([1, (now | strftime("%d") | tonumber)] | max))
}'
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected costs | No caching | Implement Redis/LRU cache |
| Credits exhausted mid-month | Underestimated volume | Upgrade plan or increase cache TTL |
| Cache miss rate high | Short TTL | Increase cache TTL to 1-4 hours |

## Resources

- [SerpApi Pricing](https://serpapi.com/pricing)
- [Account API](https://serpapi.com/account-api)

## Next Steps

For architecture patterns, see `serpapi-reference-architecture`.
