---
name: databricks-rate-limits
description: |
  Implement Databricks API rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Databricks.
  Trigger with phrases like "databricks rate limit", "databricks throttling",
  "databricks 429", "databricks retry", "databricks backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, api]

---
# Databricks Rate Limits

## Overview
Handle Databricks API rate limits with exponential backoff, token-bucket queuing, and idempotent job submissions. The API returns HTTP 429 with a `Retry-After` header when limits are exceeded. The SDK has built-in retries for transient errors, but custom logic is needed for bulk operations.

## Prerequisites
- `databricks-sdk` installed
- Understanding of async patterns for batch operations

## Instructions

### Step 1: Understand Rate Limit Tiers
Databricks enforces per-endpoint, per-workspace rate limits.

| API Category | Approx. Limit | Notes |
|-------------|---------------|-------|
| Jobs API (create/run) | ~10 req/sec | Per workspace |
| Jobs API (list/get) | ~30 req/sec | Read endpoints more generous |
| Clusters API | ~10 req/sec | Create/start are expensive |
| DBFS / Files API | ~10 req/sec | Uploads have 1MB/5MB size limits |
| SQL Statement API | ~10 concurrent | Concurrent execution limit |
| Unity Catalog | ~100 req/min | Permission checks add up fast |
| Model Serving | Varies | ITPM/OTPM/QPH limits per endpoint |

```python
from databricks.sdk.errors import TooManyRequests, ResourceConflict

w = WorkspaceClient()
try:
    w.jobs.run_now(job_id=123)
except TooManyRequests as e:
    print(f"Rate limited. Retry after: {e.retry_after_secs}s")
except ResourceConflict as e:
    print(f"Conflict (409): {e.message}")  # Job already running
```

### Step 2: Exponential Backoff with Jitter
```python
import time
import random
from functools import wraps
from databricks.sdk.errors import TooManyRequests, TemporarilyUnavailable

def retry_with_backoff(max_retries=5, base_delay=1.0, max_delay=60.0):
    """Decorator for Databricks API calls with exponential backoff + jitter."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except TooManyRequests as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.5)
                    wait = e.retry_after_secs or (delay + jitter)
                    print(f"429 (attempt {attempt + 1}/{max_retries}), waiting {wait:.1f}s")
                    time.sleep(wait)
                except TemporarilyUnavailable:
                    if attempt == max_retries - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    print(f"503 (attempt {attempt + 1}/{max_retries}), waiting {delay:.1f}s")
                    time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@retry_with_backoff(max_retries=5)
def get_job_status(w, job_id):
    return w.jobs.get(job_id)
```

### Step 3: Token-Bucket Rate Limiter for Bulk Operations
Prevent bursts when iterating over hundreds of resources.

```python
import threading
import time

class RateLimiter:
    """Token-bucket rate limiter for Databricks API calls."""

    def __init__(self, requests_per_second: float = 8.0):
        self._interval = 1.0 / requests_per_second
        self._lock = threading.Lock()
        self._last_request = 0.0

    def acquire(self):
        """Block until the next request slot is available."""
        with self._lock:
            now = time.monotonic()
            wait = self._last_request + self._interval - now
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

# Usage: enumerate jobs without hitting limits
limiter = RateLimiter(requests_per_second=8)

def list_all_job_runs(w, job_ids: list[int]) -> dict:
    results = {}
    for job_id in job_ids:
        limiter.acquire()
        runs = list(w.jobs.list_runs(job_id=job_id, limit=5))
        results[job_id] = runs
    return results
```

### Step 4: Concurrent Batch Processing with Throttle
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_run_jobs(w, job_ids: list[int], max_concurrent: int = 5) -> dict:
    """Run multiple jobs with concurrency throttling."""
    results = {}

    def run_one(job_id):
        limiter.acquire()
        try:
            run = w.jobs.run_now(job_id=job_id)
            return job_id, {"run_id": run.run_id, "status": "submitted"}
        except TooManyRequests:
            time.sleep(5)
            run = w.jobs.run_now(job_id=job_id)
            return job_id, {"run_id": run.run_id, "status": "submitted_after_retry"}
        except ResourceConflict:
            return job_id, {"status": "already_running"}

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = {executor.submit(run_one, jid): jid for jid in job_ids}
        for future in as_completed(futures):
            job_id, result = future.result()
            results[job_id] = result

    return results
```

### Step 5: Idempotent Job Submissions
Prevent duplicate runs when retrying failed submissions using `idempotency_token`.

```python
import hashlib
from datetime import datetime

def submit_idempotent(w, job_id: int, params: dict | None = None) -> int:
    """Submit a job run with idempotency — safe to retry."""
    # Deterministic token: same job + date + params = same token
    token_input = f"{job_id}-{datetime.utcnow().strftime('%Y-%m-%d')}-{sorted(params.items()) if params else ''}"
    idempotency_token = hashlib.sha256(token_input.encode()).hexdigest()[:32]

    run = w.jobs.run_now(
        job_id=job_id,
        idempotency_token=idempotency_token,
        notebook_params=params or {},
    )
    return run.run_id

# Calling twice with same inputs on the same day returns the same run_id
run1 = submit_idempotent(w, 456, params={"date": "2025-03-01"})
run2 = submit_idempotent(w, 456, params={"date": "2025-03-01"})
assert run1 == run2  # No duplicate run created
```

## Output
- Retry-safe API calls handling 429 and 503 with exponential backoff
- Token-bucket rate limiter for bulk resource enumeration
- Thread-pool batch runner with configurable concurrency
- Idempotent job submissions preventing duplicate runs

## Error Handling
| Error | HTTP | Solution |
|-------|------|----------|
| `TooManyRequests` | 429 | Use `Retry-After` header, fall back to exponential backoff |
| `TemporarilyUnavailable` | 503 | Retry with 5-10s delay; check [status.databricks.com](https://status.databricks.com) |
| `ResourceConflict` | 409 | Job already running — check `list_runs()` before submitting |
| `TimeoutError` | - | Increase SDK timeout: `WorkspaceClient(timeout=120)` |
| Sustained rate limiting | 429 | Reduce concurrency, spread load across time windows |

## Examples

### Monitor Rate Limit Headers (Raw HTTP)
```python
import requests

resp = requests.get(
    f"{w.config.host}/api/2.1/jobs/list",
    headers={"Authorization": f"Bearer {w.config.token}"},
)
print(f"Status: {resp.status_code}")
print(f"Retry-After: {resp.headers.get('Retry-After', 'N/A')}")
```

### Bulk Cluster Cleanup with Rate Limiting
```python
limiter = RateLimiter(requests_per_second=5)
terminated = 0
for cluster in w.clusters.list():
    if cluster.state.value == "TERMINATED" and cluster.cluster_name.startswith("dev-"):
        limiter.acquire()
        w.clusters.permanent_delete(cluster_id=cluster.cluster_id)
        terminated += 1
print(f"Cleaned up {terminated} dev clusters")
```

## Resources
- [Resource Limits](https://docs.databricks.com/aws/en/resources/limits)
- [Model Serving Limits](https://docs.databricks.com/aws/en/machine-learning/model-serving/model-serving-limits)
- [Status Page](https://status.databricks.com)

## Next Steps
For security configuration, see `databricks-security-basics`.
