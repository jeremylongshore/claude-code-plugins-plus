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
---
# Databricks Rate Limits

## Overview
Handle Databricks API rate limits gracefully with exponential backoff, request queuing, and idempotent job submissions. Databricks enforces per-endpoint rate limits and returns HTTP 429 when exceeded.

## Prerequisites
- Databricks SDK installed (`pip install databricks-sdk`)
- Understanding of async/await patterns (for batch operations)
- Access to Databricks workspace

## Instructions

### Step 1: Understand Rate Limit Tiers
Databricks rate limits vary by API endpoint and workspace tier. The API returns `429 Too Many Requests` with a `Retry-After` header when limits are hit.

| API Category | Approx. Limit | Notes |
|-------------|---------------|-------|
| Jobs API (create/run) | 10 req/sec | Per-workspace |
| Jobs API (list/get) | 30 req/sec | Read-heavy allowed |
| Clusters API | 10 req/sec | Create/start are expensive |
| DBFS API | 10 req/sec | Uploads have size limits too |
| SQL Statement API | 10 concurrent | Concurrent execution limit |
| Unity Catalog | 100 req/min | Permission checks add up |

```python
# The SDK returns rate limit info in error responses
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import ResourceConflict, TooManyRequests

w = WorkspaceClient()
try:
    w.jobs.run_now(job_id=123)
except TooManyRequests as e:
    print(f"Rate limited. Retry after: {e.retry_after_secs}s")
except ResourceConflict as e:
    print(f"Conflict (409): {e.message}")  # Job already running
```

### Step 2: Implement Exponential Backoff with Jitter
The SDK has built-in retries, but custom logic is needed for bulk operations.

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
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.5)
                    wait = e.retry_after_secs or (delay + jitter)
                    print(f"Rate limited (attempt {attempt + 1}/{max_retries}), waiting {wait:.1f}s")
                    time.sleep(wait)
                except TemporarilyUnavailable:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    print(f"Service unavailable (attempt {attempt + 1}/{max_retries}), waiting {delay:.1f}s")
                    time.sleep(delay)
            return func(*args, **kwargs)  # Final attempt, let exception propagate
        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_retries=5, base_delay=1.0)
def get_job_status(w, job_id):
    return w.jobs.get(job_id)
```

### Step 3: Implement Request Queue for Bulk Operations
When managing hundreds of clusters or jobs, a queue prevents bursts.

```python
import threading
import time
from collections import deque

class RateLimitedQueue:
    """Token-bucket rate limiter for Databricks API calls."""

    def __init__(self, requests_per_second=8):
        self.interval = 1.0 / requests_per_second
        self.lock = threading.Lock()
        self.last_request = 0.0

    def acquire(self):
        with self.lock:
            now = time.monotonic()
            wait = self.last_request + self.interval - now
            if wait > 0:
                time.sleep(wait)
            self.last_request = time.monotonic()

# Usage: iterate over many resources without hitting limits
limiter = RateLimitedQueue(requests_per_second=8)

def list_all_job_runs(w, job_ids):
    results = {}
    for job_id in job_ids:
        limiter.acquire()
        runs = list(w.jobs.list_runs(job_id=job_id, limit=5))
        results[job_id] = runs
    return results
```

### Step 4: Async Batch Processing
For large-scale operations, use async patterns with concurrency limits.

```python
import asyncio
from databricks.sdk.service.jobs import RunNowResponse

async def run_jobs_with_limit(w, job_ids, max_concurrent=5):
    """Run multiple jobs with concurrency throttling."""
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}

    async def run_one(job_id):
        async with semaphore:
            try:
                run = w.jobs.run_now(job_id=job_id)
                results[job_id] = {"run_id": run.run_id, "status": "submitted"}
            except TooManyRequests:
                await asyncio.sleep(5)
                run = w.jobs.run_now(job_id=job_id)
                results[job_id] = {"run_id": run.run_id, "status": "submitted_after_retry"}

    await asyncio.gather(*[run_one(jid) for jid in job_ids])
    return results
```

### Step 5: Idempotency for Job Submissions
Prevent duplicate runs when retrying failed submissions by using `idempotency_token`.

```python
import hashlib
from datetime import datetime

def submit_idempotent_job(w, job_id, params=None):
    """Submit a job run with idempotency to prevent duplicates on retry."""
    # Generate a deterministic token from job_id + date + params
    token_input = f"{job_id}-{datetime.utcnow().strftime('%Y-%m-%d')}-{params}"
    idempotency_token = hashlib.sha256(token_input.encode()).hexdigest()[:32]

    return w.jobs.run_now(
        job_id=job_id,
        idempotency_token=idempotency_token,
        notebook_params=params or {},
    )

# Calling twice with same inputs on the same day returns the same run
run1 = submit_idempotent_job(w, job_id=456, params={"date": "2025-03-01"})
run2 = submit_idempotent_job(w, job_id=456, params={"date": "2025-03-01"})
# run1.run_id == run2.run_id (no duplicate)
```

## Output
- Retry-safe API calls that handle `429` and `503` responses automatically
- Token-bucket rate limiter for bulk enumeration of resources
- Async batch runner with configurable concurrency limits
- Idempotent job submissions that prevent duplicate runs on retry

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| HTTP `429 Too Many Requests` | Rate limit exceeded | Use `Retry-After` header value, fall back to exponential backoff |
| HTTP `503 Service Unavailable` | Databricks control plane overloaded | Retry with 5-10s delay; if persistent, check [status.databricks.com](https://status.databricks.com) |
| HTTP `409 Conflict` | Job already running or resource conflict | Check existing runs with `list_runs()` before submitting |
| `TimeoutError` on SDK calls | Network or long-running operation | Increase SDK timeout: `w = WorkspaceClient(timeout=120)` |
| `Max retries exceeded` | Sustained rate limiting | Reduce concurrency, spread load across time windows |

## Examples

### Monitor Rate Limit Headers
```python
import requests

resp = requests.get(
    f"{w.config.host}/api/2.1/jobs/list",
    headers={"Authorization": f"Bearer {w.config.token}"},
)
print(f"Status: {resp.status_code}")
print(f"Rate-Limit-Remaining: {resp.headers.get('X-RateLimit-Remaining', 'N/A')}")
print(f"Retry-After: {resp.headers.get('Retry-After', 'N/A')}")
```

### Bulk Cluster Cleanup with Rate Limiting
```python
limiter = RateLimitedQueue(requests_per_second=5)
terminated = 0
for cluster in w.clusters.list():
    if cluster.state.value == "TERMINATED" and cluster.cluster_name.startswith("dev-"):
        limiter.acquire()
        w.clusters.permanent_delete(cluster_id=cluster.cluster_id)
        terminated += 1
print(f"Cleaned up {terminated} dev clusters")
```

## Resources
- [Databricks API Rate Limits](https://docs.databricks.com/dev-tools/api/latest/rate-limits.html)
- [SDK Error Handling](https://databricks-sdk-py.readthedocs.io/en/latest/authentication.html)
- [Status Page](https://status.databricks.com)

## Next Steps
For security configuration, see `databricks-security-basics`.
