# Rate Limits Examples

## Python — Exponential Backoff with Jitter

```python
import os
import time
import random
from openai import OpenAI, RateLimitError

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def completion_with_backoff(prompt: str, max_retries: int = 5) -> str:
    """Make a completion request with exponential backoff on rate limits."""
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise

            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"[Rate limit] Attempt {attempt + 1}, retrying in {delay:.1f}s")
            time.sleep(delay)

    raise RuntimeError("Should not reach here")

# Usage
result = completion_with_backoff("What is rate limiting?")
print(result)
```

## Python — Token Bucket Rate Limiter

```python
import time
import threading

class TokenBucket:
    """Client-side rate limiter using token bucket algorithm."""

    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: Tokens added per second
            capacity: Maximum burst size
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, timeout: float = 30.0) -> bool:
        """Wait up to `timeout` seconds for a token. Returns False if timed out."""
        deadline = time.monotonic() + timeout

        while True:
            with self._lock:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True

            if time.monotonic() >= deadline:
                return False
            time.sleep(0.1)

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

# 10 requests per second, burst of 20
limiter = TokenBucket(rate=10, capacity=20)

def rate_limited_completion(prompt: str) -> str:
    if not limiter.acquire(timeout=30):
        raise RuntimeError("Rate limiter timeout — too many queued requests")

    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
    )
    return response.choices[0].message.content

# Burst 20 requests — limiter smooths them out
import concurrent.futures
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
    futures = [pool.submit(rate_limited_completion, f"Count to {i}") for i in range(20)]
    results = [f.result() for f in futures]
    print(f"Completed {len(results)} requests")
```

## cURL — Read Rate Limit Headers

```bash
# Make a request and inspect rate limit headers
curl -si https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 1
  }' 2>&1 | grep -i 'x-ratelimit'

# Expected headers:
# x-ratelimit-limit-requests: 200
# x-ratelimit-limit-tokens: 200000
# x-ratelimit-remaining-requests: 199
# x-ratelimit-remaining-tokens: 199990
# x-ratelimit-reset-requests: 500ms
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
