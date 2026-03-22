---
name: openrouter-caching-strategy
description: |
  Implement caching for OpenRouter API responses to reduce cost and latency. Use when optimizing repeat queries, building RAG systems, or reducing API spend. Triggers: 'openrouter cache', 'cache llm responses', 'openrouter caching', 'reduce openrouter cost'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, caching, cost-optimization]

---
# OpenRouter Caching Strategy

## Overview

OpenRouter charges per token, so caching identical or similar requests can dramatically cut costs. Deterministic requests (`temperature=0`) with the same model and messages produce identical outputs -- these are safe to cache. This skill covers in-memory caching, persistent caching with TTL, and Anthropic prompt caching via OpenRouter.

## In-Memory Cache

```python
import os, hashlib, json, time
from typing import Optional
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

class LLMCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[str, tuple[dict, float]] = {}
        self._ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _key(self, model: str, messages: list, **kwargs) -> str:
        blob = json.dumps({"model": model, "messages": messages, **kwargs}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def get(self, model: str, messages: list, **kwargs) -> Optional[dict]:
        k = self._key(model, messages, **kwargs)
        if k in self._cache:
            data, ts = self._cache[k]
            if time.time() - ts < self._ttl:
                self.hits += 1
                return data
            del self._cache[k]
        self.misses += 1
        return None

    def set(self, model: str, messages: list, response: dict, **kwargs):
        k = self._key(model, messages, **kwargs)
        self._cache[k] = (response, time.time())

cache = LLMCache(ttl_seconds=1800)

def cached_completion(messages, model="anthropic/claude-3.5-sonnet", **kwargs):
    """Only cache deterministic requests (temperature=0)."""
    kwargs.setdefault("temperature", 0)
    kwargs.setdefault("max_tokens", 1024)

    cached = cache.get(model, messages, **kwargs)
    if cached:
        return cached

    response = client.chat.completions.create(model=model, messages=messages, **kwargs)
    result = {
        "content": response.choices[0].message.content,
        "model": response.model,
        "usage": {"prompt": response.usage.prompt_tokens, "completion": response.usage.completion_tokens},
    }
    cache.set(model, messages, result, **kwargs)
    return result
```

## Persistent Cache with Redis

```python
import redis, json, hashlib

r = redis.Redis(host="localhost", port=6379, db=0)

def redis_cached_completion(messages, model="openai/gpt-4o-mini", ttl=3600, **kwargs):
    """Cache in Redis with automatic TTL expiry."""
    kwargs["temperature"] = 0  # Must be deterministic
    key = f"or:{hashlib.sha256(json.dumps({'m': model, 'msgs': messages, **kwargs}, sort_keys=True).encode()).hexdigest()}"

    cached = r.get(key)
    if cached:
        return json.loads(cached)

    response = client.chat.completions.create(model=model, messages=messages, **kwargs)
    result = {
        "content": response.choices[0].message.content,
        "model": response.model,
        "tokens": response.usage.prompt_tokens + response.usage.completion_tokens,
    }
    r.setex(key, ttl, json.dumps(result))
    return result
```

## Anthropic Prompt Caching via OpenRouter

Anthropic models on OpenRouter support prompt caching -- large system prompts are cached server-side, reducing input cost by 90% on cache hits.

```python
# Mark large static content blocks with cache_control
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are an expert. Here is the full source:\n" + large_context,
                    "cache_control": {"type": "ephemeral"},  # Cache this block
                }
            ],
        },
        {"role": "user", "content": "What does the main() function do?"},
    ],
    max_tokens=1024,
)
# First call: cache_creation_input_tokens charged at 1.25x
# Subsequent: cache_read_input_tokens charged at 0.1x (90% savings)
```

## Cache Key Design

```python
def cache_key(model: str, messages: list, **params) -> str:
    """Deterministic cache key. Include everything that affects output.

    Include: model ID (with variant like :floor), messages, temperature,
    max_tokens, top_p, transforms, provider routing.
    Exclude: stream (doesn't affect content), HTTP-Referer, X-Title.
    """
    canonical = json.dumps({
        "model": model, "messages": messages,
        "temperature": params.get("temperature", 0),
        "max_tokens": params.get("max_tokens"),
        "top_p": params.get("top_p"),
    }, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
```

## Cache Invalidation

| Trigger | Action | Why |
|---------|--------|-----|
| Model version update | Flush keys for that model | New version may give different outputs |
| System prompt change | Flush all keys | Output semantics changed |
| TTL expiry | Automatic eviction | Prevents stale data |
| Manual purge | `r.delete(key)` or clear by prefix | Debugging or policy change |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Stale cache response | TTL too long | Reduce TTL or version cache keys |
| Cache miss storm | Cold start or invalidation | Warm cache with common queries at deploy |
| Redis connection error | Redis down | Fall through to direct API call |
| Non-deterministic cache | `temperature > 0` cached | Only cache when `temperature=0` |

## Enterprise Considerations

- Only cache deterministic requests (`temperature=0`) -- non-zero temperatures produce different outputs each time
- Use Anthropic prompt caching for large system prompts (RAG context) -- 90% cost reduction on cache hits
- Set TTL based on content freshness needs (30 min for dynamic, 24h for reference data)
- Track cache hit rate to justify caching infrastructure cost
- Use Redis or Memcached for multi-instance deployments; in-memory only works for single-process
- Version cache keys when updating system prompts or switching model versions

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Prompt Caching](https://openrouter.ai/docs/features/prompt-caching) | [Models API](https://openrouter.ai/docs/api/api-reference/models/get-models)
