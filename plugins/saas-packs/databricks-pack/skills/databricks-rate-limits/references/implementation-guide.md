# Databricks Rate Limits - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Understand Rate Limit Tiers

| API Category | Rate Limit | Notes |
|--------------|------------|-------|
| Workspace APIs | 30 req/s | Clusters, jobs, notebooks |
| SQL Warehouse | 10 req/s | Statement execution |
| Unity Catalog | 100 req/s | Tables, grants, lineage |
| Jobs Runs | 1000 runs/hour | Per workspace |
| Clusters | 20 creates/hour | Per workspace |

### Step 2: Implement Exponential Backoff with Jitter
```python
import time
import random
from typing import Callable, TypeVar
from databricks.sdk.errors import (
    DatabricksError,
    TooManyRequests,
    TemporarilyUnavailable,
    ResourceConflict,
)

T = TypeVar("T")

def with_exponential_backoff(
    operation: Callable[[], T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_factor: float = 0.5,
) -> T:
    """
    Execute operation with exponential backoff on rate limits.

    Args:
        operation: Callable to execute
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        jitter_factor: Random jitter factor (0-1)

    Returns:
        Result of operation

    Raises:
        Original exception after max retries
    """
    retryable_errors = (TooManyRequests, TemporarilyUnavailable, ResourceConflict)

    for attempt in range(max_retries + 1):
        try:
            return operation()
        except retryable_errors as e:
            if attempt == max_retries:
                raise

            # Calculate delay with exponential backoff
            exponential_delay = base_delay * (2 ** attempt)
            # Add jitter to prevent thundering herd
            jitter = random.uniform(0, jitter_factor * exponential_delay)
            delay = min(exponential_delay + jitter, max_delay)

            # Check for Retry-After header
            if hasattr(e, 'retry_after') and e.retry_after:
                delay = max(delay, float(e.retry_after))

            print(f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                  f"Retrying in {delay:.2f}s...")
            time.sleep(delay)

        except DatabricksError as e:
            # Don't retry client errors (4xx except 429)
            if e.error_code and e.error_code.startswith("4"):
                raise
            if attempt == max_retries:
                raise
            time.sleep(base_delay * (2 ** attempt))

    raise RuntimeError("Unreachable")
```

### Step 3: Implement Request Queue for Bulk Operations
```python
import time
from collections import deque
from threading import Lock
from typing import Callable, TypeVar

T = TypeVar("T")

class RateLimitedQueue:
    """Token bucket rate limiter for API calls."""

    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: int = 20,
    ):
        self.rate = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.monotonic()
        self.lock = Lock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(
            self.burst_size,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now

    def acquire(self, tokens: int = 1) -> None:
        """Block until tokens are available."""
        with self.lock:
            while True:
                self._refill_tokens()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                # Calculate wait time
                wait_time = (tokens - self.tokens) / self.rate
                time.sleep(wait_time)

    def execute(self, operation: Callable[[], T]) -> T:
        """Execute operation with rate limiting."""
        self.acquire()
        return operation()


rate_limiters = {
    "workspace": RateLimitedQueue(requests_per_second=25, burst_size=30),
    "sql": RateLimitedQueue(requests_per_second=8, burst_size=10),
    "unity_catalog": RateLimitedQueue(requests_per_second=80, burst_size=100),
}

def rate_limited(category: str = "workspace"):
    """Decorator for rate-limited API calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            limiter = rate_limiters.get(category, rate_limiters["workspace"])
            return limiter.execute(lambda: func(*args, **kwargs))
        return wrapper
    return decorator

@rate_limited("workspace")
def list_clusters(w):
    return list(w.clusters.list())
```

### Step 4: Async Batch Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, TypeVar
from databricks.sdk import WorkspaceClient

T = TypeVar("T")

async def batch_api_calls(
    w: WorkspaceClient,
    items: List[any],
    operation: Callable[[WorkspaceClient, any], T],
    concurrency: int = 5,
    delay_between_batches: float = 1.0,
) -> List[T]:
    """
    Execute API calls in batches with rate limiting.

    Args:
        w: WorkspaceClient instance
        items: Items to process
        operation: Function to call for each item
        concurrency: Max concurrent requests
        delay_between_batches: Delay between batches

    Returns:
        List of results
    """
    results = []
    semaphore = asyncio.Semaphore(concurrency)
    loop = asyncio.get_event_loop()

    async def process_item(item):
        async with semaphore:
            # Run in thread pool since SDK is sync
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    lambda: with_exponential_backoff(
                        lambda: operation(w, item)
                    )
                )
            return result

    # Process in batches
    batch_size = concurrency * 2
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_item(item) for item in batch],
            return_exceptions=True
        )
        results.extend(batch_results)

        # Delay between batches
        if i + batch_size < len(items):
            await asyncio.sleep(delay_between_batches)

    return results

async def update_all_job_tags(w: WorkspaceClient, job_ids: List[int], tags: dict):
    def update_job(w, job_id):
        return w.jobs.update(job_id=job_id, new_settings={"tags": tags})

    results = await batch_api_calls(
        w, job_ids, update_job,
        concurrency=5,
        delay_between_batches=1.0
    )
    return results
```

### Step 5: Idempotency for Job Submissions
```python
import hashlib
import json
from typing import Optional
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import RunNow, BaseRun

def generate_idempotency_token(
    job_id: int,
    params: dict,
    timestamp_bucket: int = 3600,  # 1 hour buckets
) -> str:
    """
    Generate deterministic idempotency token for job run.

    Uses timestamp buckets to allow retries within a time window
    while preventing duplicate runs across windows.
    """
    import time
    bucket = int(time.time()) // timestamp_bucket

    data = json.dumps({
        "job_id": job_id,
        "params": params,
        "bucket": bucket,
    }, sort_keys=True)

    return hashlib.sha256(data.encode()).hexdigest()[:32]

def idempotent_run_now(
    w: WorkspaceClient,
    job_id: int,
    notebook_params: Optional[dict] = None,
    idempotency_token: Optional[str] = None,
) -> BaseRun:
    """
    Submit job run with idempotency guarantee.

    If a run with the same idempotency token exists,
    returns the existing run instead of creating a new one.
    """
    # Generate token if not provided
    if not idempotency_token:
        idempotency_token = generate_idempotency_token(
            job_id,
            notebook_params or {}
        )

    # Check for existing run with same token
    recent_runs = list(w.jobs.list_runs(
        job_id=job_id,
        active_only=True,
    ))

    for run in recent_runs:
        # Check if run was started with same token
        # (Token would need to be stored in run tags in practice)
        pass

    # Submit new run
    run = w.jobs.run_now(
        job_id=job_id,
        notebook_params=notebook_params,
    )

    return run
```


## Complete Examples

### Bulk Cluster Operations
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

@rate_limited("workspace")
def safe_list_clusters():
    return list(w.clusters.list())

cluster_ids = [c.cluster_id for c in safe_list_clusters()]

async def update_all_clusters():
    results = await batch_api_calls(
        w,
        cluster_ids,
        lambda w, cid: w.clusters.edit(
            cluster_id=cid,
            autotermination_minutes=30
        ),
        concurrency=3
    )
    return results

import asyncio
asyncio.run(update_all_clusters())
```

### Monitor Rate Limit Usage
```python
class RateLimitMonitor:
    """Track rate limit usage across API calls."""

    def __init__(self):
        self.calls = []
        self.window_seconds = 60

    def record_call(self, category: str):
        import time
        now = time.time()
        self.calls.append({"time": now, "category": category})
        # Cleanup old entries
        self.calls = [c for c in self.calls if now - c["time"] < self.window_seconds]

    def get_rate(self, category: str) -> float:
        import time
        now = time.time()
        recent = [c for c in self.calls
                  if c["category"] == category and now - c["time"] < self.window_seconds]
        return len(recent) / self.window_seconds

    def should_throttle(self, category: str, limit: float) -> bool:
        return self.get_rate(category) > limit * 0.8  # 80% threshold
```
