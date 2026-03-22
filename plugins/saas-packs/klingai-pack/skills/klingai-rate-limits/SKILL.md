---
name: klingai-rate-limits
description: |
  Handle Kling AI API rate limits with backoff and queuing strategies. Use when hitting 429 errors
  or planning high-volume workflows. Trigger with phrases like 'klingai rate limit', 'kling ai 429',
  'klingai throttle', 'kling api limits'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, rate-limits, reliability]

---
# Kling AI Rate Limits

## Overview

Kling AI enforces rate limits per API key. When exceeded, the API returns `429 Too Many Requests`. This skill covers detection, backoff strategies, request queuing, and concurrent job management.

## Rate Limit Tiers

| Tier | Concurrent Tasks | Requests/Min | Notes |
|------|------------------|-------------|-------|
| Free | 1 | 10 | 66 daily credits cap |
| Standard | 3 | 30 | Per API key |
| Pro | 5 | 60 | Per API key |
| Enterprise | 10+ | Custom | Contact sales |

## Exponential Backoff with Jitter

```python
import time, random, requests

def exponential_backoff(attempt: int, base: float = 1.0, max_wait: float = 60.0) -> float:
    """Calculate wait time with jitter to avoid thundering herd."""
    wait = min(base * (2 ** attempt), max_wait)
    jitter = random.uniform(0, wait * 0.5)
    return wait + jitter

def request_with_retry(method, url, headers, json=None, max_retries=5):
    for attempt in range(max_retries + 1):
        response = method(url, headers=headers, json=json, timeout=30)

        if response.status_code == 429:
            if attempt == max_retries:
                raise RuntimeError("Rate limit: max retries exceeded")
            wait = exponential_backoff(attempt)
            print(f"429 rate limited. Waiting {wait:.1f}s (attempt {attempt + 1})")
            time.sleep(wait)
            continue

        if response.status_code >= 500:
            if attempt == max_retries:
                response.raise_for_status()
            time.sleep(exponential_backoff(attempt, base=2.0))
            continue

        response.raise_for_status()
        return response

    raise RuntimeError("Unreachable")
```

## Concurrent Task Limiter (asyncio)

```python
import asyncio

class TaskLimiter:
    """Limit concurrent Kling AI tasks to stay within API tier."""

    def __init__(self, max_concurrent: int = 3):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active = 0

    async def submit(self, coro):
        async with self._semaphore:
            self._active += 1
            try:
                return await coro
            finally:
                self._active -= 1

    @property
    def active_count(self) -> int:
        return self._active

# Usage
limiter = TaskLimiter(max_concurrent=3)
tasks = [limiter.submit(generate_video(p)) for p in prompts]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

## Rate Limit Monitor

```python
class RateLimitMonitor:
    """Track API call frequency and warn before hitting limits."""

    def __init__(self, max_per_minute: int = 30):
        self.max_per_minute = max_per_minute
        self._calls = []

    def record_call(self):
        now = time.time()
        self._calls = [t for t in self._calls if now - t < 60]
        self._calls.append(now)

    @property
    def usage_pct(self) -> float:
        now = time.time()
        recent = sum(1 for t in self._calls if now - t < 60)
        return (recent / self.max_per_minute) * 100

    def wait_if_needed(self):
        if self.usage_pct > 80 and self._calls:
            wait = 60 - (time.time() - self._calls[0])
            if wait > 0:
                print(f"Throttling: waiting {wait:.1f}s ({self.usage_pct:.0f}% of limit)")
                time.sleep(wait)
```

## Request Queue Pattern

```python
from collections import deque
import threading

class RequestQueue:
    """FIFO queue with rate-limit-aware dispatch."""

    def __init__(self, client, max_per_minute: int = 30):
        self.client = client
        self.interval = 60.0 / max_per_minute
        self._queue = deque()

    def enqueue(self, endpoint: str, body: dict, callback=None):
        self._queue.append((endpoint, body, callback))

    def process_all(self):
        while self._queue:
            endpoint, body, callback = self._queue.popleft()
            try:
                result = self.client._post(endpoint, body)
                if callback:
                    callback(result, error=None)
            except Exception as e:
                if callback:
                    callback(None, error=e)
            time.sleep(self.interval)
```

## Error Reference

| Scenario | HTTP Code | Action |
|----------|-----------|--------|
| Soft rate limit | `429` + `Retry-After` | Wait specified seconds |
| Hard rate limit | `429` no header | Backoff from 1s, double each attempt |
| Concurrent limit hit | `429` or task rejection | Wait for active tasks to complete |
| Burst detection | Multiple `429`s | Aggressive backoff (30-60s) |

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
