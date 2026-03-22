---
name: openrouter-load-balancing
description: |
  Distribute OpenRouter requests across multiple keys and models for high throughput. Use when scaling beyond single-key rate limits or building high-availability systems. Triggers: 'openrouter load balance', 'openrouter scaling', 'distribute openrouter requests', 'multiple api keys'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, scaling, high-availability, load-balancing]

---
# OpenRouter Load Balancing

## Overview

A single OpenRouter API key has rate limits (requests/minute and tokens/minute). To scale beyond those limits, distribute requests across multiple keys. OpenRouter also provides server-side load balancing via provider routing and the `:nitro` variant for low-latency inference. This skill covers multi-key rotation, health-based routing, circuit breakers, and concurrent request patterns.

## Multi-Key Round Robin

```python
import os, itertools, time, logging
from openai import OpenAI, RateLimitError
from dataclasses import dataclass, field

log = logging.getLogger("openrouter.lb")

@dataclass
class KeyPool:
    """Round-robin API key pool with health tracking."""
    keys: list[str]
    _cycle: itertools.cycle = field(init=False, repr=False)
    _health: dict[str, dict] = field(init=False, default_factory=dict)

    def __post_init__(self):
        self._cycle = itertools.cycle(self.keys)
        self._health = {k: {"errors": 0, "last_error": 0, "healthy": True} for k in self.keys}

    def next_key(self) -> str:
        """Get next healthy key."""
        attempts = 0
        while attempts < len(self.keys):
            key = next(self._cycle)
            h = self._health[key]
            # Recover after 60s cooldown
            if not h["healthy"] and time.time() - h["last_error"] > 60:
                h["healthy"] = True
                h["errors"] = 0
            if h["healthy"]:
                return key
            attempts += 1
        # All keys unhealthy -- return any and hope for the best
        return next(self._cycle)

    def mark_error(self, key: str):
        h = self._health[key]
        h["errors"] += 1
        h["last_error"] = time.time()
        if h["errors"] >= 3:  # Circuit breaker: 3 errors → unhealthy
            h["healthy"] = False
            log.warning(f"Key {key[:12]}... marked unhealthy after {h['errors']} errors")

    def mark_success(self, key: str):
        self._health[key]["errors"] = 0
        self._health[key]["healthy"] = True

pool = KeyPool(keys=[
    os.environ.get("OPENROUTER_KEY_1", ""),
    os.environ.get("OPENROUTER_KEY_2", ""),
    os.environ.get("OPENROUTER_KEY_3", ""),
])

def balanced_completion(messages, model="anthropic/claude-3.5-sonnet", **kwargs):
    """Send request using next healthy key from the pool."""
    key = pool.next_key()
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
        default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
    )
    try:
        response = client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )
        pool.mark_success(key)
        return response
    except RateLimitError:
        pool.mark_error(key)
        # Retry with next key
        return balanced_completion(messages, model, **kwargs)
```

## Concurrent Request Processing

```python
import asyncio
from openai import AsyncOpenAI

async def parallel_completions(prompts: list[str], model="openai/gpt-4o-mini",
                                max_concurrent=5, **kwargs):
    """Process multiple prompts concurrently with rate limiting."""
    semaphore = asyncio.Semaphore(max_concurrent)
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
    )

    async def process_one(prompt: str):
        async with semaphore:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return response.choices[0].message.content

    return await asyncio.gather(*[process_one(p) for p in prompts])

# Usage
results = asyncio.run(parallel_completions(
    ["Summarize X", "Translate Y", "Analyze Z"],
    max_concurrent=3,
    max_tokens=500,
))
```

## Provider-Level Load Balancing

```python
# OpenRouter can distribute across providers for the same model
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
    extra_body={
        "provider": {
            # Let OpenRouter pick the best available provider
            "order": ["Anthropic", "AWS Bedrock", "GCP Vertex"],
            "allow_fallbacks": True,
        },
    },
)
```

## Rate Limit Awareness

```python
import requests

def check_rate_limits(api_key: str) -> dict:
    """Check current rate limit status for a key."""
    resp = requests.get(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    data = resp.json()["data"]
    return {
        "requests_limit": data["rate_limit"]["requests"],
        "interval": data["rate_limit"]["interval"],
        "credits_used": data["usage"],
        "credits_limit": data.get("limit"),
    }

# Check all keys in pool
for key in pool.keys:
    limits = check_rate_limits(key)
    print(f"Key {key[:12]}...: {limits}")
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 429 on all keys | All keys rate-limited simultaneously | Add more keys; implement request queuing |
| Uneven load distribution | Round-robin not accounting for in-flight requests | Use weighted distribution based on current load |
| Key health false positive | Transient error marked key unhealthy | Use sliding window (3 errors in 60s) before marking unhealthy |
| Concurrent request failures | Too many parallel requests | Reduce semaphore limit; add backoff |

## Enterprise Considerations

- Create separate API keys per service/team with individual credit limits for cost isolation
- Use 3+ keys to multiply effective rate limits (each key gets its own quota)
- Implement circuit breakers: mark keys unhealthy after N consecutive errors, recover after cooldown
- Use `asyncio.Semaphore` to control concurrency and prevent overwhelming the API
- Monitor per-key error rates and latency to detect degraded keys early
- Combine multi-key rotation with provider routing for maximum resilience

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Rate Limits](https://openrouter.ai/docs/api/limits) | [Provider Routing](https://openrouter.ai/docs/features/provider-routing)
