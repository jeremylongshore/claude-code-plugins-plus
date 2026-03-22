---
name: serpapi-sdk-patterns
description: |
  Production-ready SerpApi client patterns with caching, typing, and multi-engine support.
  Use when building search services, implementing result caching,
  or wrapping SerpApi with typed responses.
  Trigger: "serpapi patterns", "serpapi best practices", "serpapi client wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi SDK Patterns

## Overview

Production patterns for SerpApi: typed result interfaces, response caching (critical since each search costs credits), multi-engine abstraction, and async search with the Searches Archive API.

## Instructions

### Step 1: Typed Result Interfaces

```typescript
interface SerpApiOrganicResult {
  position: number;
  title: string;
  link: string;
  snippet: string;
  displayed_link: string;
  source?: string;
}

interface SerpApiSearchResult {
  search_metadata: { id: string; status: string; created_at: string };
  search_parameters: Record<string, string>;
  organic_results: SerpApiOrganicResult[];
  answer_box?: { answer?: string; snippet?: string; title?: string };
  knowledge_graph?: { title: string; description?: string; type?: string };
  related_questions?: Array<{ question: string; snippet: string }>;
  pagination?: { next: string };
}
```

### Step 2: Cached Search Client

```typescript
import { getJson } from 'serpapi';
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, SerpApiSearchResult>({
  max: 500,
  ttl: 3600_000, // 1 hour -- search results are relatively stable
});

async function cachedSearch(params: Record<string, any>): Promise<SerpApiSearchResult> {
  const key = JSON.stringify(params);
  const cached = cache.get(key);
  if (cached) return cached;

  const result = await getJson({
    ...params,
    api_key: process.env.SERPAPI_API_KEY,
  }) as SerpApiSearchResult;

  cache.set(key, result);
  return result;
}
```

### Step 3: Multi-Engine Search Abstraction

```python
import serpapi, os

class SearchService:
    ENGINES = {
        "web": {"engine": "google", "query_param": "q"},
        "news": {"engine": "google_news", "query_param": "q"},
        "images": {"engine": "google_images", "query_param": "q"},
        "youtube": {"engine": "youtube", "query_param": "search_query"},
        "bing": {"engine": "bing", "query_param": "q"},
        "shopping": {"engine": "google_shopping", "query_param": "q"},
    }

    def __init__(self):
        self.client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])

    def search(self, query: str, engine: str = "web", **kwargs) -> dict:
        config = self.ENGINES[engine]
        params = {
            "engine": config["engine"],
            config["query_param"]: query,
            **kwargs,
        }
        return self.client.search(**params)

# Usage
svc = SearchService()
web = svc.search("Claude AI")
news = svc.search("Claude AI", engine="news")
videos = svc.search("Claude AI tutorial", engine="youtube")
```

### Step 4: Async Search (Background Processing)

```python
# Submit search asynchronously -- retrieve later
result = client.search(engine="google", q="expensive query", async_search=True)
search_id = result["search_metadata"]["id"]

# Later: retrieve from archive (no extra credit charge)
import time
while True:
    archived = client.search(engine="google", search_id=search_id)
    if archived["search_metadata"]["status"] == "Success":
        break
    time.sleep(2)
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| LRU cache | Repeated queries | Saves API credits |
| Engine abstraction | Multi-engine | Clean API for consumers |
| Async search | Heavy queries | Non-blocking, same credit cost |
| Type interfaces | All usage | Catch response changes early |

## Resources

- [SerpApi Python Client](https://github.com/serpapi/serpapi-python)
- [Searches Archive API](https://serpapi.com/search-archive-api)
- [All Engines](https://serpapi.com/)

## Next Steps

Apply patterns in `serpapi-core-workflow-a` for real-world usage.
