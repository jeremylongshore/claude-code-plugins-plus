---
name: perplexity-architecture-variants
description: |
  Choose and implement Perplexity validated architecture blueprints for different scales.
  Use when designing new Perplexity integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths for Perplexity applications.
  Trigger with phrases like "perplexity architecture", "perplexity blueprint",
  "how to structure perplexity", "perplexity project layout", "perplexity microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Architecture Variants

## Overview
Deployment architectures for Perplexity Sonar search API at different scales. Perplexity's search-augmented generation model fits different patterns from simple search widgets to full research automation pipelines.

## Prerequisites
- Perplexity API key configured
- Clear search/research use case
- Infrastructure for chosen scale

## Instructions

### Step 1: Direct Search Widget (Simple)

**Best for:** Adding AI search to an app, < 500 queries/day.

```python
@app.route('/ask')
def ask():
    response = pplx_client.chat.completions.create(
        model="sonar", messages=[{"role": "user", "content": request.args["q"]}]
    )
    return jsonify({
        "answer": response.choices[0].message.content,
        "citations": response.citations
    })
```

### Step 2: Cached Research Layer (Moderate)

**Best for:** Repeated queries, 500-5K queries/day, research tools.

```python
class CachedResearch:
    def __init__(self, client, cache, ttl=1800):
        self.client = client
        self.cache = cache
        self.ttl = ttl

    def search(self, query: str, model: str = "sonar"):
        key = f"pplx:{hashlib.sha256(query.encode()).hexdigest()}"
        cached = self.cache.get(key)
        if cached:
            return json.loads(cached)
        result = self.client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": query}]
        )
        data = {"answer": result.choices[0].message.content, "citations": result.citations}
        self.cache.setex(key, self.ttl, json.dumps(data))
        return data
```

### Step 3: Multi-Query Research Pipeline (Scale)

**Best for:** Automated research, 5K+ queries/day, report generation.

```python
class ResearchPipeline:
    async def research_topic(self, topic: str) -> dict:
        # Decompose into sub-questions
        sub_questions = await self.decompose(topic)
        # Run parallel searches
        results = await asyncio.gather(*[
            self.search_with_cache(q) for q in sub_questions
        ])
        # Synthesize into report
        report = await self.synthesize(topic, results)
        return {"topic": topic, "sections": results, "synthesis": report}

    async def decompose(self, topic: str) -> list[str]:
        r = self.client.chat.completions.create(
            model="sonar", messages=[
                {"role": "system", "content": "Break this topic into 3-5 specific research questions."},
                {"role": "user", "content": topic}
            ])
        return r.choices[0].message.content.strip().split("\n")
```

## Decision Matrix

| Factor | Direct Widget | Cached Layer | Research Pipeline |
|--------|--------------|--------------|-------------------|
| Volume | < 500/day | 500-5K/day | 5K+/day |
| Use Case | Quick answers | Repeated queries | Deep research |
| Latency | 2-5s | 50ms (cached) | 10-30s |
| Model | sonar | sonar | sonar-pro |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow in UI | No caching | Cache repeated queries |
| High cost | sonar-pro everywhere | Route by complexity |
| Stale answers | Long cache TTL | Reduce TTL for current events |

## Resources
- [Perplexity API Docs](https://docs.perplexity.ai)
