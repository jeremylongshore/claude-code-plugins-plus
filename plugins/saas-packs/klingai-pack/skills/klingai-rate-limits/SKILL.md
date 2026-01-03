---
name: klingai-rate-limits
description: |
  Handle Kling AI rate limits with proper backoff strategies. Use when experiencing 429 errors
  or building high-throughput systems. Trigger with phrases like 'klingai rate limit',
  'kling ai 429', 'klingai throttle', 'klingai backoff'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Rate Limits

## Overview

This skill teaches rate limit handling patterns including exponential backoff, token bucket algorithms, request queuing, and concurrent job management for reliable Kling AI integrations.

## Prerequisites

- Kling AI integration
- Understanding of HTTP status codes
- Python 3.8+ or Node.js 18+

## Instructions

Follow these steps to handle rate limits:

1. **Understand Limits**: Know the rate limit structure
2. **Implement Detection**: Detect rate limit responses
3. **Add Backoff**: Implement exponential backoff
4. **Queue Requests**: Add request queuing
5. **Monitor Usage**: Track rate limit consumption

## Rate Limit Structure

```
Kling AI Rate Limits (typical):

Requests per minute:
- Free tier: 10 RPM
- Standard tier: 60 RPM
- Pro tier: 200 RPM
- Enterprise: Custom

Concurrent jobs:
- Free tier: 2 concurrent
- Standard tier: 10 concurrent
- Pro tier: 50 concurrent
- Enterprise: Custom

Burst limits:
- Short burst allowed (10-20% over limit)
- Sustained over-limit triggers 429
```

## Exponential Backoff

```python
import time
import random
from functools import wraps
from typing import TypeVar, Callable

T = TypeVar('T')

def exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> Callable:
    """Decorator for exponential backoff on rate limits."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" not in str(e) and "rate" not in str(e).lower():
                        raise  # Not a rate limit error

                    last_exception = e

                    if attempt == max_retries - 1:
                        raise

                    # Calculate delay
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    print(f"Rate limited. Attempt {attempt + 1}/{max_retries}. "
                          f"Waiting {delay:.2f}s...")
                    time.sleep(delay)

            raise last_exception

        return wrapper
    return decorator

# Usage
@exponential_backoff(max_retries=5, base_delay=2.0)
def generate_video(prompt: str):
    # API call here
    pass
```

## Token Bucket Rate Limiter

```python
import time
import threading
from dataclasses import dataclass

@dataclass
class TokenBucket:
    """Token bucket rate limiter."""

    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = None
    last_refill: float = None
    lock: threading.Lock = None

    def __post_init__(self):
        self.tokens = float(self.capacity) if self.tokens is None else self.tokens
        self.last_refill = time.time() if self.last_refill is None else self.last_refill
        self.lock = threading.Lock() if self.lock is None else self.lock

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def acquire(self, tokens: int = 1, timeout: float = None) -> bool:
        """Acquire tokens, blocking if necessary."""
        start = time.time()

        while True:
            with self.lock:
                self._refill()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                # Calculate wait time
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.refill_rate

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start
                if elapsed + wait_time > timeout:
                    return False

            time.sleep(min(wait_time, 1.0))  # Sleep in chunks

    def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without blocking."""
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

# Usage
rate_limiter = TokenBucket(
    capacity=60,      # 60 requests
    refill_rate=1.0   # 1 request per second (60 RPM)
)

def rate_limited_request(prompt: str):
    if rate_limiter.acquire(timeout=30):
        return generate_video(prompt)
    else:
        raise Exception("Rate limit timeout")
```

## Request Queue

```python
import asyncio
from collections import deque
from typing import Any, Callable
import uuid

class RequestQueue:
    """Async request queue with rate limiting."""

    def __init__(self, requests_per_minute: int = 60, max_concurrent: int = 10):
        self.rpm = requests_per_minute
        self.max_concurrent = max_concurrent
        self.queue = deque()
        self.active = 0
        self.results = {}
        self.lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def enqueue(self, func: Callable, *args, **kwargs) -> str:
        """Add request to queue and return request ID."""
        request_id = str(uuid.uuid4())
        self.queue.append((request_id, func, args, kwargs))
        return request_id

    async def process_queue(self):
        """Process queued requests respecting rate limits."""
        interval = 60.0 / self.rpm

        while self.queue:
            async with self.semaphore:
                if not self.queue:
                    break

                request_id, func, args, kwargs = self.queue.popleft()

                try:
                    async with self.lock:
                        self.active += 1

                    result = await func(*args, **kwargs)
                    self.results[request_id] = {"status": "success", "result": result}

                except Exception as e:
                    self.results[request_id] = {"status": "error", "error": str(e)}

                finally:
                    async with self.lock:
                        self.active -= 1

                await asyncio.sleep(interval)

    async def get_result(self, request_id: str, timeout: float = 300) -> Any:
        """Wait for and return result."""
        start = time.time()
        while time.time() - start < timeout:
            if request_id in self.results:
                return self.results.pop(request_id)
            await asyncio.sleep(0.5)
        raise TimeoutError(f"Request {request_id} timed out")

# Usage
queue = RequestQueue(requests_per_minute=60, max_concurrent=10)
```

## Concurrent Job Manager

```python
class ConcurrentJobManager:
    """Manage concurrent video generation jobs."""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.active_jobs = set()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def acquire_slot(self, timeout: float = None) -> bool:
        """Acquire a job slot."""
        with self.condition:
            start = time.time()
            while len(self.active_jobs) >= self.max_concurrent:
                remaining = None
                if timeout:
                    elapsed = time.time() - start
                    remaining = timeout - elapsed
                    if remaining <= 0:
                        return False

                self.condition.wait(timeout=remaining)

            job_id = str(uuid.uuid4())
            self.active_jobs.add(job_id)
            return job_id

    def release_slot(self, job_id: str):
        """Release a job slot."""
        with self.condition:
            self.active_jobs.discard(job_id)
            self.condition.notify()

    def get_active_count(self) -> int:
        """Get number of active jobs."""
        with self.lock:
            return len(self.active_jobs)

# Usage
job_manager = ConcurrentJobManager(max_concurrent=10)

def generate_with_slot(prompt: str):
    slot = job_manager.acquire_slot(timeout=60)
    if not slot:
        raise Exception("No available slots")

    try:
        return generate_video(prompt)
    finally:
        job_manager.release_slot(slot)
```

## Rate Limit Headers

```python
def parse_rate_limit_headers(response) -> dict:
    """Parse rate limit information from response headers."""
    return {
        "limit": int(response.headers.get("X-RateLimit-Limit", 0)),
        "remaining": int(response.headers.get("X-RateLimit-Remaining", 0)),
        "reset": int(response.headers.get("X-RateLimit-Reset", 0)),
        "retry_after": int(response.headers.get("Retry-After", 0))
    }

def adaptive_rate_limiter(response):
    """Adjust rate limiting based on response headers."""
    info = parse_rate_limit_headers(response)

    if info["remaining"] < info["limit"] * 0.1:
        # Less than 10% remaining, slow down
        print(f"Warning: Only {info['remaining']} requests remaining")
        time.sleep(2)

    if info["remaining"] == 0:
        # Wait until reset
        wait_time = max(info["reset"] - time.time(), info["retry_after"], 1)
        print(f"Rate limit exhausted. Waiting {wait_time}s...")
        time.sleep(wait_time)
```

## Output

Successful execution produces:
- Rate limit handling without errors
- Smooth request throughput
- Proper backoff behavior
- Concurrent job management

## Error Handling

Common errors and solutions:
1. **Persistent 429**: Check if limit is per-key or per-account
2. **Thundering Herd**: Add jitter to backoff delays
3. **Starvation**: Implement fair queuing

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Rate Limits](https://docs.klingai.com/rate-limits)
- [Exponential Backoff](https://cloud.google.com/iot/docs/how-tos/exponential-backoff)
- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)
