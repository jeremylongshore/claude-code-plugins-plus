# Rate Limiter Implementation

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
