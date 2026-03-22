---
name: serpapi-rate-limits
description: |
  Handle SerpApi rate limits and credit-based usage quotas.
  Use when managing API credit consumption, implementing request throttling,
  or optimizing search volume for your plan tier.
  Trigger: "serpapi rate limit", "serpapi credits", "serpapi quota", "serpapi throttle".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Rate Limits

## Overview

SerpApi uses credit-based pricing (each search = 1 credit) plus per-second rate limits. Retrieving cached/archived searches does not consume credits. Plans range from 100 searches/month (free) to unlimited (enterprise).

## Plan Limits

| Plan | Searches/Month | Rate Limit | Price |
|------|---------------|------------|-------|
| Free | 100 | 1/second | $0 |
| Developer | 5,000 | 5/second | $75/mo |
| Business | 15,000 | 10/second | $200/mo |
| Enterprise | 50,000+ | 15/second | Custom |

## Instructions

### Step 1: Monitor Credit Usage

```python
import serpapi, os

client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])

# Check remaining credits before batch operations
account = client.account()
remaining = account["plan_searches_left"]
used = account["this_month_usage"]
total = account["total_searches_left"]

print(f"Used: {used}, Remaining: {remaining}")
if remaining < 100:
    print("WARNING: Low credits remaining")
```

### Step 2: Request Throttling

```python
import time
from threading import Semaphore

class ThrottledSerpApi:
    def __init__(self, api_key: str, max_per_second: int = 5):
        self.client = serpapi.Client(api_key=api_key)
        self.semaphore = Semaphore(max_per_second)
        self.last_request = 0

    def search(self, **params) -> dict:
        with self.semaphore:
            # Enforce minimum interval
            elapsed = time.time() - self.last_request
            if elapsed < 0.2:  # 5/sec max
                time.sleep(0.2 - elapsed)
            self.last_request = time.time()
            return self.client.search(**params)
```

### Step 3: Use Archive to Avoid Credit Waste

```python
# Retrieve a previous search result by ID (FREE, no credit charge)
archived = client.search(engine="google", search_id="previous_search_id")

# Check if a query was recently searched before spending a credit
# Store search IDs in your database keyed by query+params hash
```

### Step 4: Node.js Rate Limiter

```typescript
import PQueue from 'p-queue';
import { getJson } from 'serpapi';

const queue = new PQueue({
  concurrency: 3,       // Max parallel requests
  interval: 1000,       // Per second
  intervalCap: 5,       // Max 5 per second
});

async function throttledSearch(params: Record<string, any>) {
  return queue.add(() => getJson({
    ...params,
    api_key: process.env.SERPAPI_API_KEY,
  }));
}

// Batch search with automatic throttling
const queries = ['query1', 'query2', 'query3'];
const results = await Promise.all(
  queries.map(q => throttledSearch({ engine: 'google', q }))
);
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Rate limit exceeded | Slow down, check plan tier |
| `Searches exhausted` | Monthly credits used up | Cache results, upgrade plan |
| `Account disabled` | Payment issue or abuse | Contact SerpApi support |

## Resources

- [SerpApi Pricing](https://serpapi.com/pricing)
- [Account API](https://serpapi.com/account-api)
- [Searches Archive](https://serpapi.com/search-archive-api)

## Next Steps

For security configuration, see `serpapi-security-basics`.
