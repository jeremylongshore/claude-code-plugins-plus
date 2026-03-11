---
name: exa-reliability-patterns
description: |
  Implement Exa reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Exa integrations, implementing retry strategies,
  or adding resilience to production Exa services.
  Trigger with phrases like "exa reliability", "exa circuit breaker",
  "exa idempotent", "exa resilience", "exa fallback", "exa bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Exa Reliability Patterns

## Overview
Production reliability patterns for Exa neural search integrations. Exa's search-focused API has unique failure modes: query relevance degradation, empty result sets, and variable response times based on query complexity.

## Prerequisites
- Exa API configured
- Caching infrastructure (Redis recommended)
- Understanding of search quality metrics

## Instructions

### Step 1: Cache Search Results with TTL

Search results for the same query are stable over short periods. Caching reduces API calls and latency.

```python
import hashlib, json, time

class ExaSearchCache:
    def __init__(self, redis_client, default_ttl=300):
        self.r = redis_client
        self.ttl = default_ttl

    def _key(self, query: str, **params) -> str:
        data = json.dumps({"q": query, **params}, sort_keys=True)
        return f"exa:search:{hashlib.sha256(data.encode()).hexdigest()}"

    def search(self, exa_client, query: str, **params):
        key = self._key(query, **params)
        cached = self.r.get(key)
        if cached:
            return json.loads(cached)
        results = exa_client.search(query, **params)
        self.r.setex(key, self.ttl, json.dumps(results.to_dict()))
        return results
```

### Step 2: Query Fallback Chain

If neural search returns low-relevance results, fall back to keyword search, then to cached results.

```python
from exa_py import Exa

def resilient_search(exa: Exa, query: str, min_results: int = 3):
    # Try neural search first
    results = exa.search(query, type="neural", num_results=10)
    if len(results.results) >= min_results:
        return results

    # Fall back to keyword search
    results = exa.search(query, type="keyword", num_results=10)
    if len(results.results) >= min_results:
        return results

    # Fall back to broader query with autoprompt
    results = exa.search(query, type="neural", use_autoprompt=True, num_results=10)
    return results
```

### Step 3: Retry with Exponential Backoff

Exa returns 429 on rate limits and 5xx on transient failures.

```python
import time, random

def exa_with_retry(fn, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            status = getattr(e, 'status_code', 0)
            if status == 429 or status >= 500:
                if attempt == max_retries:
                    raise
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(delay)
            else:
                raise
```

### Step 4: Result Quality Monitoring

Track search quality metrics to detect degradation before users notice.

```python
class SearchQualityMonitor:
    def __init__(self, redis_client):
        self.r = redis_client

    def record(self, query: str, result_count: int, has_content: bool):
        key = f"exa:quality:{time.strftime('%Y-%m-%d-%H')}"
        self.r.hincrby(key, "total", 1)
        if result_count == 0:
            self.r.hincrby(key, "empty", 1)
        if not has_content:
            self.r.hincrby(key, "no_content", 1)
        self.r.expire(key, 86400 * 7)

    def get_health(self) -> dict:
        key = f"exa:quality:{time.strftime('%Y-%m-%d-%H')}"
        stats = self.r.hgetall(key)
        total = int(stats.get(b"total", 0))
        empty = int(stats.get(b"empty", 0))
        return {
            "total": total,
            "empty_rate": empty / total if total > 0 else 0,
            "healthy": (empty / total < 0.2) if total > 10 else True
        }
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Empty results | Overly specific query | Use autoprompt and query fallback chain |
| Slow responses | Complex neural search | Cache results, set timeouts |
| 429 rate limit | Burst traffic | Exponential backoff with jitter |
| Quality degradation | API changes or query drift | Monitor empty result rates |

## Examples

### Timeout Wrapper
```python
import asyncio

async def search_with_timeout(exa, query, timeout=10):
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(exa.search, query),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return cached_fallback(query)
```

## Resources
- [Exa API Reference](https://docs.exa.ai/reference)
