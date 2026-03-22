---
name: serpapi-reference-architecture
description: |
  Production architecture for SerpApi search services with caching, monitoring, and multi-engine support.
  Use when designing search features, building SERP tracking systems,
  or architecting search-powered applications.
  Trigger: "serpapi architecture", "serpapi project structure", "serpapi design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Reference Architecture

## Overview

Production architecture for search-powered applications using SerpApi. Core components: cached search service, multi-engine abstraction, SERP monitoring pipeline, and credit budget management.

## Architecture Diagram

```
┌──────────────────────────────────┐
│          API Layer               │
│  /search  /track  /health        │
├──────────────────────────────────┤
│        Search Service            │
│  Multi-engine  Caching  Parsing  │
├──────────────────────────────────┤
│       SerpApi Client             │
│  Rate Limiting  Retry  Archive   │
├──────────────────────────────────┤
│       Infrastructure             │
│  Redis Cache  PostgreSQL  Cron   │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│        SerpApi REST API          │
│  google  youtube  bing  news     │
│  1 credit/search, 100-50K/mo     │
└──────────────────────────────────┘
```

## Project Structure

```
search-service/
├── src/
│   ├── serpapi/
│   │   ├── client.ts          # Cached search with rate limiting
│   │   ├── engines.ts         # Engine-specific param mapping
│   │   └── types.ts           # Typed result interfaces
│   ├── services/
│   │   ├── search.ts          # Multi-engine search facade
│   │   ├── tracking.ts        # Keyword rank tracking
│   │   └── credits.ts         # Usage monitoring
│   ├── api/
│   │   ├── search.ts          # /search proxy endpoint
│   │   └── health.ts          # /health with credit check
│   └── jobs/
│       └── rank-tracker.ts    # Daily keyword monitoring
├── tests/
│   ├── fixtures/              # Recorded SerpApi responses
│   └── search.test.ts         # Fixture-based tests
└── config/
```

## Key Components

### Search Service Facade

```typescript
class SearchService {
  constructor(private client: CachedSerpApiClient, private db: Database) {}

  async search(query: string, options?: { engine?: string; num?: number }) {
    const engine = options?.engine || 'google';
    const result = await this.client.cachedSearch({
      engine, q: query, num: options?.num || 5,
    });

    // Normalize across engines
    return {
      results: result.organic_results || result.video_results || [],
      answer_box: result.answer_box || null,
      knowledge_graph: result.knowledge_graph || null,
      search_id: result.search_metadata.id,
      cached: result._cached || false,
    };
  }

  async trackKeyword(keyword: string, domain: string) {
    const result = await this.client.cachedSearch({
      engine: 'google', q: keyword, num: 100,
    });
    const position = result.organic_results?.findIndex(
      (r: any) => r.link?.includes(domain)
    );
    await this.db.saveRanking(keyword, domain, position >= 0 ? position + 1 : null);
  }
}
```

### Credit Budget Manager

```typescript
class CreditBudget {
  async check(): Promise<{ ok: boolean; remaining: number }> {
    const account = await fetch(
      `https://serpapi.com/account.json?api_key=${process.env.SERPAPI_API_KEY}`
    ).then(r => r.json());

    return {
      ok: account.plan_searches_left > 100,
      remaining: account.plan_searches_left,
    };
  }
}
```

## Error Handling

| Component | Failure | Recovery |
|-----------|---------|----------|
| Search API | Credits exhausted | Return cached results, alert ops |
| Cache | Redis down | Fall through to API (graceful degradation) |
| Rank tracker | Query fails | Skip and retry next cycle |
| Health check | API unreachable | Report degraded status |

## Resources

- [SerpApi Documentation](https://serpapi.com/)
- [Searches Archive](https://serpapi.com/search-archive-api)

## Next Steps

See individual skill docs for deep-dives on each component.
