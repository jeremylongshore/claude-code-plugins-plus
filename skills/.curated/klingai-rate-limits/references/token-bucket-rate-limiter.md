# Token Bucket Rate Limiter

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
