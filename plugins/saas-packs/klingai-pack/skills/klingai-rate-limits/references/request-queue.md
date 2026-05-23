# Request Queue

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
