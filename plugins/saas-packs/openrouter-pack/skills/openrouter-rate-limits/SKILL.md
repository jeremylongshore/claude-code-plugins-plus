---
name: openrouter-rate-limits
description: |
  Handle OpenRouter rate limits and quotas. Triggers on "openrouter rate limit",
  "openrouter 429", "openrouter throttle", "openrouter quota".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Rate Limits

## Understanding Rate Limits

### Types of Limits
```
1. Requests per minute (RPM)
   - Varies by model and provider
   - OpenRouter applies its own limits on top

2. Tokens per minute (TPM)
   - Combined prompt + completion tokens
   - Provider-specific limits

3. Per-key credit limits
   - Set in dashboard
   - Prevents overspending
```

### Response Headers
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1234567890
Retry-After: 30
```

## Rate Limit Detection

### Python
```python
from openai import RateLimitError

def is_rate_limited(error):
    """Check if error is a rate limit."""
    if isinstance(error, RateLimitError):
        return True
    if hasattr(error, 'status_code') and error.status_code == 429:
        return True
    return False
```

### TypeScript
```typescript
import { RateLimitError } from 'openai';

function isRateLimited(error: unknown): boolean {
  if (error instanceof RateLimitError) return true;
  if (error && typeof error === 'object' && 'status' in error) {
    return error.status === 429;
  }
  return false;
}
```

## Retry Strategies

### Exponential Backoff
```python
import time
import random

def exponential_backoff(attempt: int, base: float = 1.0, max_wait: float = 60.0):
    """Calculate wait time with jitter."""
    wait = min(base * (2 ** attempt), max_wait)
    jitter = random.uniform(0, wait * 0.1)
    return wait + jitter

def chat_with_backoff(prompt: str, model: str, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = exponential_backoff(attempt)
            print(f"Rate limited, waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
```

### With Retry-After Header
```python
def get_retry_after(error) -> float:
    """Extract Retry-After from error response."""
    if hasattr(error, 'response') and error.response:
        retry_after = error.response.headers.get('Retry-After')
        if retry_after:
            return float(retry_after)
    return 1.0  # Default

def chat_with_retry_header(prompt: str, model: str, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = get_retry_after(e)
            time.sleep(wait_time)
```

## Rate Limiter Implementation

### Token Bucket
```python
import threading
import time

class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.capacity = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        refill = elapsed * (self.capacity / 60)  # tokens per second
        self.tokens = min(self.capacity, self.tokens + refill)
        self.last_refill = now

    def acquire(self, timeout: float = 60.0) -> bool:
        deadline = time.time() + timeout

        while time.time() < deadline:
            with self.lock:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True

            time.sleep(0.1)

        return False

# Usage
limiter = RateLimiter(requests_per_minute=60)

def rate_limited_chat(prompt: str, model: str):
    if not limiter.acquire():
        raise Exception("Rate limit timeout")

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```

### Async Rate Limiter
```python
import asyncio

class AsyncRateLimiter:
    def __init__(self, requests_per_minute: int):
        self.semaphore = asyncio.Semaphore(requests_per_minute)
        self.interval = 60.0 / requests_per_minute

    async def acquire(self):
        await self.semaphore.acquire()
        asyncio.create_task(self._release_after_interval())

    async def _release_after_interval(self):
        await asyncio.sleep(self.interval)
        self.semaphore.release()

async_limiter = AsyncRateLimiter(requests_per_minute=60)

async def async_rate_limited_chat(prompt: str, model: str):
    await async_limiter.acquire()
    return await async_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```

## Per-Model Rate Limits

### Model-Aware Limiter
```python
class ModelRateLimiter:
    def __init__(self):
        # Different limits per model (approximate)
        self.limits = {
            "openai/gpt-4-turbo": 60,
            "openai/gpt-3.5-turbo": 200,
            "anthropic/claude-3.5-sonnet": 60,
            "anthropic/claude-3-haiku": 200,
            "meta-llama/llama-3.1-70b-instruct": 100,
        }
        self.limiters = {}

    def get_limiter(self, model: str) -> RateLimiter:
        if model not in self.limiters:
            rpm = self.limits.get(model, 60)  # Default to 60
            self.limiters[model] = RateLimiter(rpm)
        return self.limiters[model]

    def acquire(self, model: str) -> bool:
        return self.get_limiter(model).acquire()

model_limiter = ModelRateLimiter()
```

## Batch Processing with Rate Limits

### Controlled Batch Processing
```python
import asyncio
from typing import List

async def process_batch(
    prompts: List[str],
    model: str,
    requests_per_minute: int = 60
):
    """Process prompts with rate limiting."""
    delay = 60.0 / requests_per_minute
    results = []

    for i, prompt in enumerate(prompts):
        if i > 0:
            await asyncio.sleep(delay)

        try:
            response = await async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            results.append({
                "prompt": prompt,
                "response": response.choices[0].message.content,
                "success": True
            })
        except RateLimitError:
            # Extra wait on rate limit
            await asyncio.sleep(delay * 5)
            results.append({
                "prompt": prompt,
                "response": None,
                "success": False,
                "error": "rate_limited"
            })

    return results
```

### Concurrent with Semaphore
```python
async def process_batch_concurrent(
    prompts: List[str],
    model: str,
    max_concurrent: int = 5
):
    """Process with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(prompt: str):
        async with semaphore:
            try:
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return {"prompt": prompt, "response": response, "success": True}
            except RateLimitError:
                await asyncio.sleep(5)
                return {"prompt": prompt, "response": None, "success": False}

    return await asyncio.gather(*[process_one(p) for p in prompts])
```

## Monitoring Rate Limit Usage

### Rate Limit Tracker
```python
class RateLimitTracker:
    def __init__(self):
        self.windows = {}  # model -> list of timestamps

    def record_request(self, model: str):
        now = time.time()
        if model not in self.windows:
            self.windows[model] = []

        # Clean old entries (older than 1 minute)
        self.windows[model] = [t for t in self.windows[model] if now - t < 60]
        self.windows[model].append(now)

    def get_rpm(self, model: str) -> int:
        """Get current requests per minute."""
        now = time.time()
        if model not in self.windows:
            return 0
        return len([t for t in self.windows[model] if now - t < 60])

    def should_throttle(self, model: str, limit: int) -> bool:
        return self.get_rpm(model) >= limit * 0.9  # 90% threshold

tracker = RateLimitTracker()
```

## Best Practices

### Pre-Request Check
```python
def safe_chat(prompt: str, model: str):
    """Chat with proactive rate limit checking."""
    # Check current usage
    if tracker.should_throttle(model, limit=60):
        time.sleep(2)  # Proactive slowdown

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        tracker.record_request(model)
        return response
    except RateLimitError:
        # Aggressive backoff on actual rate limit
        time.sleep(10)
        raise
```

### Circuit Breaker
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 60):
        self.failures = 0
        self.threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure = 0
        self.state = "closed"  # closed, open, half-open

    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.threshold:
            self.state = "open"

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def can_proceed(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure > self.reset_timeout:
                self.state = "half-open"
                return True
            return False
        return True  # half-open allows one request
```
