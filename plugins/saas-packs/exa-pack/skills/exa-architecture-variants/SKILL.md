---
name: exa-architecture-variants
description: |
  Choose and implement Exa validated architecture blueprints for different scales.
  Use when designing new Exa integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths for Exa applications.
  Trigger with phrases like "exa architecture", "exa blueprint",
  "how to structure exa", "exa project layout", "exa microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Exa Architecture Variants

## Overview
Deployment architectures for Exa neural search at different scales. Exa's search-and-contents model supports everything from simple search features to full RAG pipelines and semantic knowledge bases.

## Prerequisites
- Exa API configured
- Clear search use case defined
- Infrastructure for chosen architecture tier

## Instructions

### Step 1: Direct Search Integration (Simple)

**Best for:** Adding search to an existing app, < 1K queries/day.

```
User Query -> Backend -> Exa Search API -> Format Results -> User
```

```python
from exa_py import Exa
exa = Exa(api_key=os.environ["EXA_API_KEY"])

@app.route('/search')
def search():
    query = request.args.get('q')
    results = exa.search_and_contents(
        query, num_results=5, text={"max_characters": 1000}
    )
    return jsonify([{
        "title": r.title, "url": r.url, "snippet": r.text[:200]
    } for r in results.results])
```

### Step 2: Cached Search with Semantic Layer (Moderate)

**Best for:** High-traffic search, 1K-50K queries/day, content aggregation.

```
User Query -> Cache Check -> (miss) -> Exa API -> Cache Store -> User
                  |                                    
                  v (hit)                              
              Cached Results -> User
```

```python
class CachedExaSearch:
    def __init__(self, exa_client, redis_client, ttl=600):
        self.exa = exa_client
        self.cache = redis_client
        self.ttl = ttl

    def search(self, query: str, **kwargs):
        key = self._cache_key(query, **kwargs)
        cached = self.cache.get(key)
        if cached:
            return json.loads(cached)
        results = self.exa.search_and_contents(query, **kwargs)
        serialized = self._serialize(results)
        self.cache.setex(key, self.ttl, json.dumps(serialized))
        return serialized
```

### Step 3: RAG Pipeline with Exa as Knowledge Source (Scale)

**Best for:** AI-powered apps, 50K+ queries/day, LLM-augmented answers.

```
User Query -> Query Planner -> Exa Search -> Content Extraction
                                                  |
                                                  v
                                          Vector Store (cache)
                                                  |
                                                  v
                                    LLM Generation with Context -> User
```

```python
class ExaRAGPipeline:
    def __init__(self, exa, llm, vector_store):
        self.exa = exa
        self.llm = llm
        self.vectors = vector_store

    async def answer(self, question: str) -> dict:
        # 1. Search for relevant content
        results = self.exa.search_and_contents(
            question, num_results=5, text={"max_characters": 3000},
            highlights=True
        )
        # 2. Store in vector cache for future queries
        for r in results.results:
            self.vectors.upsert(r.url, r.text, {"title": r.title})
        # 3. Generate answer with citations
        context = "\n\n".join([f"[{i+1}] {r.text}" for i, r in enumerate(results.results)])
        answer = await self.llm.generate(
            f"Based on the following sources, answer: {question}\n\n{context}"
        )
        return {"answer": answer, "sources": [r.url for r in results.results]}
```

## Decision Matrix

| Factor | Direct | Cached | RAG Pipeline |
|--------|--------|--------|--------------|
| Volume | < 1K/day | 1K-50K/day | 50K+/day |
| Latency | 1-3s | 50ms (cached) | 3-8s |
| Use Case | Simple search | Content aggregation | AI-powered answers |
| Complexity | Low | Medium | High |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow search in UI | No caching | Add result cache with TTL |
| Stale cached results | Long TTL | Reduce TTL for time-sensitive queries |
| RAG hallucination | Poor source selection | Use highlights, increase num_results |
| High API costs | No query deduplication | Cache layer deduplicates identical queries |

## Examples

### Health Check
```python
health = {
    "cache_hit_rate": cache.hit_rate(),
    "avg_search_latency_ms": metrics.avg("exa_latency"),
    "queries_today": metrics.count("exa_queries")
}
```

## Resources
- [Exa API Docs](https://docs.exa.ai)
- [Exa RAG Guide](https://docs.exa.ai/reference/rag)
