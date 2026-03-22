---
name: openrouter-rate-limits
description: |
  Understand and handle OpenRouter rate limits. Use when hitting 429 errors, building high-throughput systems, or implementing retry logic. Triggers: 'openrouter rate limit', 'openrouter 429', 'openrouter throttle', 'rate limiting openrouter'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, rate-limits, throttling]

---
# OpenRouter Rate Limits

## Overview

OpenRouter rate limits are per-key, not per-account. Free tier keys get lower limits; paid keys get higher limits that scale with credit balance. The OpenAI SDK has built-in retry with exponential backoff for 429 responses. Check your current limits via `GET /api/v1/auth/key`. Rate limit headers are returned on every response.

## Check Your Rate Limits

```bash
# Query current rate limit configuration for your key
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '{
    label: .data.label,
    rate_limit: .data.rate_limit,
    is_free_tier: .data.is_free_tier,
    credits_used: .data.usage,
    credit_limit: .data.limit
  }'
# Example output:
# {
#   "label": "my-app-prod",
#   "rate_limit": {"requests": 200, "interval": "10s"},
#   "is_free_tier": false,
#   "credits_used": 12.34,
#   "credit_limit": 100
# }
```

## Rate Limit Tiers

| Tier | Requests | Interval | Who |
|------|----------|----------|-----|
| Free (no credits) | 20 | 10s | New accounts |
| Free (with credits) | 200 | 10s | Accounts with any credits |
| Paid | Higher | Varies | Based on credit balance |

Free models have separate limits: 50 req/day (free users), 1000 req/day (with $10+ credits).

## Read Rate Limit Headers

```python
import os
from openai import OpenAI
import requests as http_requests

# The OpenAI SDK abstracts headers, so use requests for direct access
def check_rate_headers():
    """Make a request and inspect rate limit headers."""
    resp = http_requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://my-app.com",
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 1,
        },
    )
    return {
        "status": resp.status_code,
        "x-ratelimit-limit": resp.headers.get("x-ratelimit-limit"),
        "x-ratelimit-remaining": resp.headers.get("x-ratelimit-remaining"),
        "x-ratelimit-reset": resp.headers.get("x-ratelimit-reset"),
        "retry-after": resp.headers.get("retry-after"),
    }
```

## Retry Strategy with OpenAI SDK

```python
from openai import OpenAI

# The SDK handles 429 retries automatically with exponential backoff
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    max_retries=5,           # Default is 2; increase for high-throughput
    timeout=60.0,            # Per-request timeout
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

# The SDK will:
# 1. Catch 429 responses
# 2. Read Retry-After header
# 3. Wait with exponential backoff (+ jitter)
# 4. Retry up to max_retries times
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
)
```

## Custom Rate Limiter (Client-Side)

```python
import time, threading
from collections import deque

class TokenBucket:
    """Client-side rate limiter to prevent hitting server limits."""

    def __init__(self, rate: int = 200, interval: float = 10.0):
        self.rate = rate           # Max requests per interval
        self.interval = interval
        self._timestamps = deque()
        self._lock = threading.Lock()

    def acquire(self, timeout: float = 30.0) -> bool:
        """Block until a request slot is available."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                now = time.monotonic()
                # Remove timestamps outside the window
                while self._timestamps and now - self._timestamps[0] > self.interval:
                    self._timestamps.popleft()

                if len(self._timestamps) < self.rate:
                    self._timestamps.append(now)
                    return True

            time.sleep(0.1)  # Wait and retry
        return False  # Timed out

limiter = TokenBucket(rate=150, interval=10.0)  # Stay under 200 limit

def rate_limited_completion(messages, **kwargs):
    """Completion with client-side rate limiting."""
    if not limiter.acquire(timeout=30):
        raise TimeoutError("Rate limiter timeout")
    return client.chat.completions.create(messages=messages, **kwargs)
```

## Batch Processing with Rate Awareness

```python
import asyncio
from openai import AsyncOpenAI

async def batch_with_rate_limit(prompts: list[str], model="openai/gpt-4o-mini",
                                 max_concurrent=10, delay_between=0.05):
    """Process a batch of prompts with rate-aware concurrency."""
    semaphore = asyncio.Semaphore(max_concurrent)
    aclient = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        max_retries=5,
        default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
    )

    async def process(prompt, idx):
        await asyncio.sleep(idx * delay_between)  # Stagger requests
        async with semaphore:
            response = await aclient.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            return response.choices[0].message.content

    return await asyncio.gather(*[process(p, i) for i, p in enumerate(prompts)])
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 429 Too Many Requests | Exceeded requests per interval | SDK auto-retries; increase `max_retries` |
| Retry storm | Multiple clients retrying simultaneously | Add random jitter (0-1s) to retry delay |
| Silent throttling | Responses slow down before 429 | Monitor latency; proactively reduce rate |
| Free tier limit hit | 50 req/day on free models | Add credits ($10+) for 1000 req/day limit |

## Enterprise Considerations

- Rate limits are per-key: use multiple keys to multiply effective throughput
- The OpenAI SDK handles 429 retries automatically -- configure `max_retries` (default 2)
- Implement client-side rate limiting to stay under limits proactively (cheaper than retries)
- Free models have daily limits separate from the per-key rate limit
- Monitor `x-ratelimit-remaining` headers to detect approaching limits before hitting 429
- For batch workloads, use staggered concurrent requests rather than burst patterns

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Rate Limits](https://openrouter.ai/docs/api/limits) | [Auth/Key API](https://openrouter.ai/docs/api/reference/authentication)
