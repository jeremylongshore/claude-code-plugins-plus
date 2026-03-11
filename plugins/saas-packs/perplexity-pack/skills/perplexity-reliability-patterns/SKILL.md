---
name: perplexity-reliability-patterns
description: |
  Implement Perplexity reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Perplexity integrations, implementing retry strategies,
  or adding resilience to production Perplexity services.
  Trigger with phrases like "perplexity reliability", "perplexity circuit breaker",
  "perplexity idempotent", "perplexity resilience", "perplexity fallback", "perplexity bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Reliability Patterns

## Overview
Production reliability patterns for Perplexity Sonar API integrations. Perplexity performs live web searches per request, making response times variable and dependent on search complexity -- unlike static LLM inference.

## Prerequisites
- Perplexity API key configured
- Caching layer (Redis recommended)
- Understanding of search-augmented generation latency

## Instructions

### Step 1: Cache Identical Queries

Perplexity's web search is expensive per call. Cache results for repeated queries within a time window.

```python
import hashlib, json

class PerplexityCache:
    def __init__(self, redis_client, ttl=600):
        self.r = redis_client
        self.ttl = ttl

    def get_or_search(self, client, messages, model="sonar", **kwargs):
        key = self._cache_key(messages, model, **kwargs)
        cached = self.r.get(key)
        if cached:
            return json.loads(cached)
        result = client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )
        self.r.setex(key, self.ttl, json.dumps(result.to_dict()))
        return result

    def _cache_key(self, messages, model, **kwargs):
        data = json.dumps({"m": messages, "model": model, **kwargs}, sort_keys=True)
        return f"pplx:{hashlib.sha256(data.encode()).hexdigest()}"
```

### Step 2: Model Tier Fallback

If `sonar-pro` times out or errors, fall back to `sonar` for a faster but shallower response.

```python
def resilient_search(client, messages, timeout=30):
    try:
        return client.chat.completions.create(
            model="sonar-pro", messages=messages, timeout=timeout
        )
    except Exception:
        return client.chat.completions.create(
            model="sonar", messages=messages, timeout=15
        )
```

### Step 3: Streaming with Timeout Protection

Perplexity streams can stall on complex searches. Set per-chunk timeouts.

```python
import time

def stream_with_timeout(client, messages, chunk_timeout=10):
    stream = client.chat.completions.create(
        model="sonar", messages=messages, stream=True
    )
    last_chunk = time.time()
    full_response = ""
    citations = []

    for chunk in stream:
        if time.time() - last_chunk > chunk_timeout:
            raise TimeoutError("Stream stalled")
        last_chunk = time.time()
        delta = chunk.choices[0].delta.content or ""
        full_response += delta
        if hasattr(chunk, 'citations'):
            citations = chunk.citations
        yield delta

    return full_response, citations
```

### Step 4: Citation Validation

Verify cited URLs are accessible before presenting to users.

```python
import aiohttp

async def validate_citations(citations: list[str]) -> list[dict]:
    validated = []
    async with aiohttp.ClientSession() as session:
        for url in citations[:5]:  # limit to top 5
            try:
                async with session.head(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    validated.append({"url": url, "status": r.status, "valid": r.status < 400})
            except:
                validated.append({"url": url, "status": 0, "valid": False})
    return validated
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow responses (>15s) | Complex search query | Use sonar instead of sonar-pro |
| Stream stalls | Search taking too long | Per-chunk timeout detection |
| Stale results | Cached data too old | Reduce TTL for time-sensitive queries |
| Broken citation links | Source pages moved | Validate URLs before displaying |

## Examples

### Health Check
```python
def pplx_health(client, cache):
    start = time.time()
    r = client.chat.completions.create(model="sonar", messages=[
        {"role": "user", "content": "What day is it today?"}
    ])
    latency = time.time() - start
    return {"status": "ok", "latency_ms": int(latency * 1000), "cache_size": cache.r.dbsize()}
```

## Resources
- [Perplexity API Docs](https://docs.perplexity.ai)
