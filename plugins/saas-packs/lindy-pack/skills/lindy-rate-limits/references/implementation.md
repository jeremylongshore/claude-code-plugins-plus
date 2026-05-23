# Lindy Rate Limits -- Implementation Details

## Rate Limit Architecture

Lindy enforces rate limits at two levels:

1. **API rate limits** -- requests per minute/hour to the Lindy REST API
2. **Agent execution limits** -- concurrent runs per workspace

## Advanced Patterns

### Exponential Backoff with Jitter

```python
import time
import random
import requests
import os
from typing import Callable, TypeVar

T = TypeVar("T")

def with_exponential_backoff(
    fn: Callable[[], T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> T:
    """Execute a function with exponential backoff on rate limit errors."""
    for attempt in range(max_retries):
        try:
            return fn()
        except requests.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status in (429, 502, 503) and attempt < max_retries - 1:
                retry_after = e.response.headers.get("Retry-After") if e.response else None
                delay = float(retry_after) if retry_after else min(base_delay * (2 ** attempt), max_delay)
                delay = random.uniform(0, delay)  # Full jitter
                print(f"[{status}] Retry {attempt + 1}/{max_retries} in {delay:.1f}s")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError("Max retries exceeded")


LINDY_API_BASE = "https://api.lindy.ai/v1"
HEADERS = {"Authorization": f"Bearer {os.environ['LINDY_API_KEY']}"}

def trigger_with_backoff(agent_id: str, inputs: dict) -> dict:
    def _trigger():
        resp = requests.post(
            f"{LINDY_API_BASE}/agents/{agent_id}/runs",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"inputs": inputs}, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    return with_exponential_backoff(_trigger)
```

### Rate Limit Aware Queue

```python
import time
import threading

class RateLimitedQueue:
    """Execute tasks at a controlled rate to stay within API limits."""

    def __init__(self, requests_per_second: float = 10.0):
        self.min_interval = 1.0 / requests_per_second
        self._lock = threading.Lock()
        self._last_request_time = 0.0

    def _wait_if_needed(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_time = time.monotonic()

    def submit(self, fn, *args, **kwargs):
        with self._lock:
            self._wait_if_needed()
            return fn(*args, **kwargs)

    def submit_batch(self, tasks: list[tuple]) -> list:
        results = []
        for fn, args, kwargs in tasks:
            try:
                result = self.submit(fn, *args, **kwargs)
                results.append({"status": "ok", "result": result})
            except Exception as e:
                results.append({"status": "error", "error": str(e)})
        return results


queue = RateLimitedQueue(requests_per_second=5.0)

leads = [{"email": f"user{i}@example.com"} for i in range(100)]
tasks = [(trigger_with_backoff, ("agent-abc123", lead), {}) for lead in leads]
results = queue.submit_batch(tasks)
print(f"Processed {len(results)} leads")
```

## Troubleshooting

### Hitting Rate Limits Despite Low Volume

1. Multiple processes sharing the same API key -- aggregate limits apply per key
2. Retry storms -- retries without backoff re-hit rate limits immediately
3. Scheduled agents all firing at the same time (top of hour)
4. Check for webhook duplicate events from Slack/email integrations

### Rate Limits in Production But Not Staging

1. Production has more traffic -- check actual request volume in dashboard
2. Staging uses a separate API key with its own rate limit bucket
3. Look for cron jobs that spike at top-of-hour in production

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
