---
name: openrouter-caching-strategy
description: 'Implement caching for OpenRouter API responses to reduce cost and latency.
  Use when optimizing repeat queries, building RAG systems, or reducing API spend.
  Triggers: ''openrouter cache'', ''cache llm responses'', ''openrouter caching'',
  ''reduce openrouter cost''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(node:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- caching
- cost-optimization
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Caching Strategy

## Overview

OpenRouter charges per token, so caching identical or similar requests can dramatically cut costs. Deterministic requests (`temperature=0`) with the same model and messages produce identical outputs -- these are safe to cache. This skill covers in-memory caching, persistent caching with TTL, and Anthropic prompt caching via OpenRouter.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- Python 3.8+ with the OpenAI SDK, plus the `redis` client package for the persistent cache; Node.js 18+ with the OpenAI SDK for the TypeScript variant in the references
- A Redis server reachable at `localhost:6379` for Persistent Cache with Redis (the in-memory `LLMCache` needs no infrastructure)
- Deterministic request settings — caching is only safe at `temperature=0`

## Instructions

1. Confirm the requests you want to cache are deterministic (`temperature=0`); non-zero temperatures produce different outputs each call and must never be cached.
2. Start with the In-Memory Cache: `LLMCache` plus `cached_completion()` gives you TTL expiry and hit/miss counters in a single process.
3. For multi-instance deployments, switch to Persistent Cache with Redis — `redis_cached_completion()` stores results under `or:<sha256>` keys with `r.setex` TTL expiry and falls through to a direct API call on a miss.
4. Build keys per Cache Key Design: include the model ID (with variants like `:floor`), messages, temperature, max_tokens, and top_p; exclude `stream` and the HTTP-Referer/X-Title headers.
5. For large static system prompts (RAG context), add `cache_control: {"type": "ephemeral"}` per Anthropic Prompt Caching via OpenRouter — cache reads bill at 0.1x the input rate.
6. Wire the Cache Invalidation table: flush per-model keys on model version updates, flush everything on system prompt changes, and let TTL handle the rest.

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

## Output

- Cached completion payloads returned without an API round-trip: `{"content", "model", "usage"}` from the in-memory cache or `{"content", "model", "tokens"}` from Redis
- Redis keys of the form `or:<sha256-of-canonical-request>` that expire automatically via TTL
- Hit/miss counters and a `hit_rate` figure you can use to justify the caching infrastructure
- On Anthropic models, `cache_creation_input_tokens` billed at 1.25x on the first call and `cache_read_input_tokens` at 0.1x (90% savings) on subsequent hits

## Examples

Two identical deterministic calls through the `ResponseCache` from the references — the second returns instantly from cache:

```python
result1 = cached_completion("What is Python?")   # [Cache MISS] key=3f8a92c1... (stored)
result2 = cached_completion("What is Python?")   # [Cache HIT] key=3f8a92c1...
print(f"Hit rate: {cache.hit_rate:.0%}")         # Hit rate: 50%
```

More worked examples, including a TypeScript Redis-style cache: `references/examples.md`.

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

- Examples | Errors
- [Prompt Caching](https://openrouter.ai/docs/features/prompt-caching) | [Models API](https://openrouter.ai/docs/api/api-reference/models/get-models)
