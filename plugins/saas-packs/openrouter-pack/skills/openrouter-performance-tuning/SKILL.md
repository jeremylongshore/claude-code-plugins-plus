---
name: openrouter-performance-tuning
description: |
  Optimize OpenRouter performance. Triggers on "openrouter performance",
  "openrouter latency", "speed up openrouter", "openrouter optimization".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Performance Tuning

## Latency Optimization

### Connection Pooling
```python
import httpx
from openai import OpenAI

# Create persistent HTTP client with connection pooling
http_client = httpx.Client(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30.0
    ),
    timeout=httpx.Timeout(60.0, connect=5.0)
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    http_client=http_client
)
```

### Async for Concurrency
```python
from openai import AsyncOpenAI
import asyncio

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

async def batch_process(prompts: list, max_concurrent: int = 10):
    """Process multiple prompts concurrently."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(prompt: str):
        async with semaphore:
            return await async_client.chat.completions.create(
                model="anthropic/claude-3-haiku",  # Fast model
                messages=[{"role": "user", "content": prompt}]
            )

    return await asyncio.gather(*[process_one(p) for p in prompts])
```

## Model Selection for Speed

### Fast Model Options
```python
FAST_MODELS = [
    {
        "id": "anthropic/claude-3-haiku",
        "avg_latency_ms": 500,
        "quality": "good"
    },
    {
        "id": "openai/gpt-3.5-turbo",
        "avg_latency_ms": 600,
        "quality": "good"
    },
    {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "avg_latency_ms": 400,
        "quality": "moderate"
    },
    {
        "id": "mistralai/mistral-7b-instruct",
        "avg_latency_ms": 350,
        "quality": "moderate"
    }
]

def select_fast_model(min_quality: str = "moderate") -> str:
    """Select fastest model meeting quality threshold."""
    quality_order = ["low", "moderate", "good", "excellent"]
    min_quality_idx = quality_order.index(min_quality)

    candidates = [
        m for m in FAST_MODELS
        if quality_order.index(m["quality"]) >= min_quality_idx
    ]

    candidates.sort(key=lambda m: m["avg_latency_ms"])
    return candidates[0]["id"] if candidates else FAST_MODELS[0]["id"]
```

## Request Optimization

### Minimize Token Usage
```python
def optimize_request(
    prompt: str,
    system: str = None,
    max_tokens: int = None
) -> dict:
    """Create optimized request parameters."""
    messages = []

    # Minimal system prompt
    if system:
        messages.append({
            "role": "system",
            "content": system.strip()[:500]  # Limit system prompt
        })

    messages.append({"role": "user", "content": prompt})

    params = {
        "messages": messages,
    }

    # Set max_tokens to limit response
    if max_tokens:
        params["max_tokens"] = max_tokens
    else:
        # Auto-calculate based on expected response
        params["max_tokens"] = min(500, estimate_tokens(prompt))

    return params

def fast_chat(prompt: str, model: str = "anthropic/claude-3-haiku"):
    """Optimized chat for speed."""
    params = optimize_request(prompt, max_tokens=500)

    return client.chat.completions.create(
        model=model,
        **params
    )
```

### Streaming for Perceived Speed
```python
def stream_response(prompt: str, model: str = "anthropic/claude-3-haiku"):
    """Stream response for faster time-to-first-token."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        max_tokens=500
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

## Caching Strategies

### Response Caching
```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_completion(cache_key: str) -> str:
    """Return cached response for identical requests."""
    # This is called only on cache miss
    # Actual call happens in wrapper
    pass

def fast_cached_chat(
    prompt: str,
    model: str = "anthropic/claude-3-haiku"
) -> str:
    """Chat with caching for repeated queries."""
    cache_key = hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()

    # Check if in cache
    try:
        return cached_completion(cache_key)
    except:
        pass

    # Make request
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    content = response.choices[0].message.content

    # Update cache (hack for lru_cache)
    cached_completion.cache_clear()
    cached_completion.__wrapped__(cache_key)

    return content
```

### Semantic Caching
```python
class SemanticCache:
    """Cache similar queries."""

    def __init__(self, similarity_threshold: float = 0.92):
        self.threshold = similarity_threshold
        self.cache = []  # (embedding, prompt, response)

    def get(self, prompt: str) -> str | None:
        """Get cached response for similar prompt."""
        if not self.cache:
            return None

        prompt_embedding = self._embed(prompt)

        for cached_emb, cached_prompt, cached_response in self.cache:
            similarity = self._cosine_sim(prompt_embedding, cached_emb)
            if similarity >= self.threshold:
                return cached_response

        return None

    def set(self, prompt: str, response: str):
        """Cache a response."""
        embedding = self._embed(prompt)
        self.cache.append((embedding, prompt, response))
        # Limit cache size
        self.cache = self.cache[-500:]

    def _embed(self, text: str) -> list:
        # Simplified - use actual embedding model
        return [ord(c) for c in text[:100]]

    def _cosine_sim(self, a: list, b: list) -> float:
        # Simplified cosine similarity
        import numpy as np
        a, b = np.array(a), np.array(b[:len(a)])
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
```

## Batch Processing

### Efficient Batching
```python
async def efficient_batch(
    prompts: list,
    model: str = "anthropic/claude-3-haiku",
    batch_size: int = 10,
    delay_between_batches: float = 0.1
):
    """Process prompts in efficient batches."""
    results = []

    for i in range(0, len(prompts), batch_size):
        batch = prompts[i:i + batch_size]

        # Process batch concurrently
        batch_results = await asyncio.gather(*[
            async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": p}],
                max_tokens=500
            )
            for p in batch
        ])

        results.extend(batch_results)

        # Small delay to avoid rate limits
        if i + batch_size < len(prompts):
            await asyncio.sleep(delay_between_batches)

    return results
```

## Monitoring & Profiling

### Latency Tracking
```python
import time
from dataclasses import dataclass
from statistics import mean, median, stdev

@dataclass
class LatencyMetrics:
    model: str
    latencies: list
    tokens: list

class PerformanceMonitor:
    """Track performance metrics."""

    def __init__(self):
        self.metrics = {}

    def record(
        self,
        model: str,
        latency_ms: float,
        tokens: int
    ):
        if model not in self.metrics:
            self.metrics[model] = LatencyMetrics(model, [], [])

        self.metrics[model].latencies.append(latency_ms)
        self.metrics[model].tokens.append(tokens)

        # Keep last 1000
        self.metrics[model].latencies = self.metrics[model].latencies[-1000:]
        self.metrics[model].tokens = self.metrics[model].tokens[-1000:]

    def get_stats(self, model: str) -> dict:
        if model not in self.metrics:
            return {}

        m = self.metrics[model]
        return {
            "count": len(m.latencies),
            "latency": {
                "mean": mean(m.latencies),
                "median": median(m.latencies),
                "p95": sorted(m.latencies)[int(len(m.latencies) * 0.95)],
                "stdev": stdev(m.latencies) if len(m.latencies) > 1 else 0
            },
            "tokens_per_request": mean(m.tokens),
            "tokens_per_second": sum(m.tokens) / (sum(m.latencies) / 1000)
        }

monitor = PerformanceMonitor()

def monitored_chat(prompt: str, model: str):
    """Chat with monitoring."""
    start = time.time()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    latency = (time.time() - start) * 1000
    tokens = response.usage.total_tokens

    monitor.record(model, latency, tokens)

    return response
```

## Configuration Tuning

### Optimal Parameters
```python
PERFORMANCE_CONFIGS = {
    "latency_optimized": {
        "model": "anthropic/claude-3-haiku",
        "max_tokens": 500,
        "temperature": 0,  # Deterministic = faster
    },
    "throughput_optimized": {
        "model": "anthropic/claude-3.5-sonnet",
        "max_tokens": 2000,
        "temperature": 0.7,
    },
    "cost_optimized": {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "max_tokens": 500,
        "temperature": 0.7,
    },
    "quality_optimized": {
        "model": "anthropic/claude-3.5-sonnet",
        "max_tokens": 4000,
        "temperature": 0.7,
    }
}

def chat_with_profile(prompt: str, profile: str = "latency_optimized"):
    """Chat with performance profile."""
    config = PERFORMANCE_CONFIGS.get(profile, PERFORMANCE_CONFIGS["latency_optimized"])

    return client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        **config
    )
```

## Best Practices Summary

```python
PERFORMANCE_TIPS = """
1. Connection Pooling
   - Use persistent HTTP client
   - Enable keepalive connections
   - Set appropriate connection limits

2. Model Selection
   - Use claude-3-haiku for speed
   - Use gpt-3.5-turbo for balance
   - Reserve larger models for complex tasks

3. Request Optimization
   - Minimize prompt length
   - Set appropriate max_tokens
   - Use streaming for perceived speed

4. Caching
   - Cache identical requests
   - Consider semantic caching
   - Implement TTL-based expiration

5. Async Processing
   - Use async for concurrent requests
   - Batch similar requests
   - Implement rate limiting

6. Monitoring
   - Track latency by model
   - Monitor token usage
   - Set up alerting for degradation
"""
```
