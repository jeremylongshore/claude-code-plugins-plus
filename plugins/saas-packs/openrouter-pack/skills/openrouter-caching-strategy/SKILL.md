---
name: openrouter-caching-strategy
description: |
  Implement response caching for OpenRouter efficiency. Use when optimizing costs or reducing latency for repeated queries. Trigger with phrases like 'openrouter cache', 'cache llm responses', 'openrouter redis', 'semantic caching'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Caching Strategy

## Overview

This skill covers caching strategies from simple LRU caches to semantic similarity caching for intelligent response reuse.

## Prerequisites

- OpenRouter integration
- Caching infrastructure (Redis recommended for production)

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill covers caching strategies from simple LRU caches to semantic similarity caching for intelligent response reuse.

## Prerequisites

- OpenRouter integration
- Caching infrastructure (Redis recommended for production)

## In-Memory Caching

### Simple LRU Cache
```python
from functools import lru_cache
import hashlib

def hash_request(messages: tuple, model: str) -> str:
    """Create hash key for cache lookup."""
    content = f"{model}:{str(messages)}"
    return hashlib.sha256(content.encode()).hexdigest()

@lru_cache(maxsize=1000)
def cached_chat(cache_key: str, model: str, messages_tuple: tuple) -> str:
    """Cached chat completion."""
    messages = [{"role": m[0], "content": m[1]} for m in messages_tuple]

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content

def chat_with_cache(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    """Use cache for identical requests."""
    messages = (("user", prompt),)
    cache_key = hash_request(messages, model)
    return cached_chat(cache_key, model, messages)
```

### TTL Cache
```python
import time
from collections import OrderedDict

class TTLCache:
    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        self.maxsize = maxsize
        self.ttl = ttl  # seconds
        self.cache = OrderedDict()

    def _hash(self, model: str, messages: list) -> str:
        content = f"{model}:{messages}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, model: str, messages: list) -> str | None:
        key = self._hash(model, messages)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.cache.move_to_end(key)
                return value
            else:
                del self.cache[key]
        return None

    def set(self, model: str, messages: list, value: str):
        key = self._hash(model, messages)
        self.cache[key] = (value, time.time())
        self.cache.move_to_end(key)

        while len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)

cache = TTLCache(maxsize=1000, ttl=3600)

def chat_with_ttl_cache(
    prompt: str,
    model: str = "openai/gpt-4-turbo"
) -> str:
    messages = [{"role": "user", "content": prompt}]

    # Check cache
    cached = cache.get(model, messages)
    if cached:
        return cached

    # Make request
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = response.choices[0].message.content

    # Cache result
    cache.set(model, messages, content)
    return content
```

## Redis Caching

### Redis Implementation
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

class RedisCache:
    def __init__(self, prefix: str = "openrouter", ttl: int = 3600):
        self.prefix = prefix
        self.ttl = ttl

    def _key(self, model: str, messages: list) -> str:
        content = json.dumps({"model": model, "messages": messages}, sort_keys=True)
        hash_val = hashlib.sha256(content.encode()).hexdigest()
        return f"{self.prefix}:{hash_val}"

    def get(self, model: str, messages: list) -> str | None:
        key = self._key(model, messages)
        value = redis_client.get(key)
        return value.decode() if value else None

    def set(self, model: str, messages: list, value: str):
        key = self._key(model, messages)
        redis_client.setex(key, self.ttl, value)

redis_cache = RedisCache(ttl=3600)

def chat_with_redis(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    messages = [{"role": "user", "content": prompt}]

    # Check Redis
    cached = redis_cache.get(model, messages)
    if cached:
        return cached

    # Make request
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = response.choices[0].message.content

    # Cache in Redis
    redis_cache.set(model, messages, content)
    return content
```

### Async Redis
```python
import aioredis

async_redis = aioredis.from_url("redis://localhost")

async def async_chat_with_redis(
    prompt: str,
    model: str = "openai/gpt-4-turbo"
) -> str:
    messages = [{"role": "user", "content": prompt}]
    key = redis_cache._key(model, messages)

    # Check cache
    cached = await async_redis.get(key)
    if cached:
        return cached.decode()

    # Make request
    response = await async_client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = response.choices[0].message.content

    # Cache
    await async_redis.setex(key, 3600, content)
    return content
```

## Semantic Caching

### Embedding-Based Cache
```python
import numpy as np
from openai import OpenAI

# For embeddings (can use OpenRouter or direct)
embedding_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.95):
        self.threshold = similarity_threshold
        self.embeddings = []  # (embedding, prompt, response)

    def _get_embedding(self, text: str) -> list:
        # Note: Use embedding model if available
        # This is a placeholder - OpenRouter may have embedding models
        response = embedding_client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def _cosine_similarity(self, a: list, b: list) -> float:
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def get(self, prompt: str) -> str | None:
        if not self.embeddings:
            return None

        query_embedding = self._get_embedding(prompt)

        for emb, cached_prompt, response in self.embeddings:
            similarity = self._cosine_similarity(query_embedding, emb)
            if similarity >= self.threshold:
                return response

        return None

    def set(self, prompt: str, response: str):
        embedding = self._get_embedding(prompt)
        self.embeddings.append((embedding, prompt, response))

semantic_cache = SemanticCache(similarity_threshold=0.95)
```

## Caching Strategies

### Cache by Intent
```python
from enum import Enum

class CachePolicy(Enum):
    NEVER = "never"
    SHORT = "short"    # 5 minutes
    MEDIUM = "medium"  # 1 hour
    LONG = "long"      # 24 hours

POLICY_TTL = {
    CachePolicy.NEVER: 0,
    CachePolicy.SHORT: 300,
    CachePolicy.MEDIUM: 3600,
    CachePolicy.LONG: 86400,
}

def determine_cache_policy(prompt: str) -> CachePolicy:
    """Determine caching policy based on prompt."""
    prompt_lower = prompt.lower()

    # Never cache time-sensitive queries
    if any(word in prompt_lower for word in ["current", "today", "now", "latest"]):
        return CachePolicy.NEVER

    # Long cache for factual/reference queries
    if any(word in prompt_lower for word in ["definition", "explain", "what is"]):
        return CachePolicy.LONG

    # Medium cache for code generation
    if any(word in prompt_lower for word in ["write", "code", "function"]):
        return CachePolicy.MEDIUM

    return CachePolicy.SHORT

def smart_cached_chat(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    policy = determine_cache_policy(prompt)

    if policy == CachePolicy.NEVER:
        # Skip cache entirely
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    # Use cache with policy TTL
    ttl = POLICY_TTL[policy]
    # ... implement with TTL-aware cache
```

### Multi-Level Caching
```python
class MultiLevelCache:
    def __init__(self):
        self.l1 = TTLCache(maxsize=100, ttl=300)    # Fast, small, short
        self.l2 = TTLCache(maxsize=1000, ttl=3600)  # Larger, longer
        # self.l3 = RedisCache(ttl=86400)           # Persistent

    def get(self, model: str, messages: list) -> str | None:
        # Try L1 first
        result = self.l1.get(model, messages)
        if result:
            return result

        # Try L2
        result = self.l2.get(model, messages)
        if result:
            # Promote to L1
            self.l1.set(model, messages, result)
            return result

        return None

    def set(self, model: str, messages: list, value: str, tier: int = 1):
        if tier >= 1:
            self.l1.set(model, messages, value)
        if tier >= 2:
            self.l2.set(model, messages, value)

multi_cache = MultiLevelCache()
```

## Cache Invalidation

### Manual Invalidation
```python
class InvalidatableCache:
    def __init__(self):
        self.cache = {}
        self.tags = {}  # tag -> set of cache keys

    def set(self, key: str, value: str, tags: list = None):
        self.cache[key] = value
        if tags:
            for tag in tags:
                if tag not in self.tags:
                    self.tags[tag] = set()
                self.tags[tag].add(key)

    def get(self, key: str) -> str | None:
        return self.cache.get(key)

    def invalidate_by_tag(self, tag: str):
        if tag in self.tags:
            for key in self.tags[tag]:
                self.cache.pop(key, None)
            del self.tags[tag]

    def invalidate_all(self):
        self.cache.clear()
        self.tags.clear()

# Usage
cache = InvalidatableCache()
cache.set("prompt:123", "response", tags=["user:456", "model:gpt4"])
cache.invalidate_by_tag("user:456")  # Invalidate user's cache
```

## Cost Savings Analysis

### Cache Hit Tracking
```python
class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.saved_tokens = 0
        self.saved_cost = 0.0

    def record_hit(self, tokens: int, cost_per_m: float):
        self.hits += 1
        self.saved_tokens += tokens
        self.saved_cost += tokens * cost_per_m / 1_000_000

    def record_miss(self):
        self.misses += 1

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "total_requests": total,
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
            "tokens_saved": self.saved_tokens,
            "cost_saved": self.saved_cost
        }

metrics = CacheMetrics()

def tracked_cached_chat(prompt: str, model: str = "openai/gpt-4-turbo"):
    messages = [{"role": "user", "content": prompt}]

    cached = cache.get(model, messages)
    if cached:
        # Estimate tokens saved
        tokens = len(prompt) // 4 + len(cached) // 4
        metrics.record_hit(tokens, 10.0)  # Assuming $10/M
        return cached

    metrics.record_miss()
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = response.choices[0].message.content
    cache.set(model, messages, content)
    return content

# Check savings
print(metrics.stats())
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
