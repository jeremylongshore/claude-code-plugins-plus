---
name: palantir-rate-limits
description: |
  Implement Palantir Foundry API rate limiting, backoff, and request queuing.
  Use when handling 429 errors, implementing retry logic,
  or optimizing API request throughput for Foundry.
  Trigger with phrases like "palantir rate limit", "foundry throttling",
  "palantir 429", "foundry retry", "palantir backoff".
allowed-tools: Read, Write, Edit
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, rate-limits, reliability]
compatible-with: claude-code, codex, openclaw
---

# Palantir Rate Limits

## Overview
Handle Foundry API rate limits with exponential backoff, request queuing, and monitoring. Foundry rate limits vary by endpoint and enrollment tier.

## Prerequisites
- `foundry-platform-sdk` installed
- Understanding of HTTP 429 responses

## Instructions

### Step 1: Understand Foundry Rate Limits
Foundry rate limits are per-user and per-endpoint. Key limits:

| Endpoint Category | Typical Limit | Burst |
|-------------------|---------------|-------|
| Ontology reads | 100 req/s | 200 |
| Ontology writes (Actions) | 50 req/s | 100 |
| Dataset reads | 50 req/s | 100 |
| Search queries | 20 req/s | 50 |

Rate limit headers returned:
- `X-RateLimit-Limit` — max requests per window
- `X-RateLimit-Remaining` — requests left in window
- `Retry-After` — seconds to wait (on 429)

### Step 2: Implement Retry with Backoff (Python)
```python
import time
import random
import foundry

def retry_foundry_call(fn, *args, max_retries=5, base_delay=1.0, **kwargs):
    """Retry Foundry API calls with jittered exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except foundry.ApiError as e:
            if attempt == max_retries:
                raise
            if e.status_code not in (429, 500, 502, 503):
                raise  # Non-retryable error
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            retry_after = getattr(e, "retry_after", None)
            if retry_after:
                delay = max(delay, float(retry_after))
            print(f"  Retry {attempt+1}/{max_retries} in {delay:.1f}s (HTTP {e.status_code})")
            time.sleep(delay)

# Usage
employees = retry_foundry_call(
    client.ontologies.OntologyObject.list,
    ontology="my-company", object_type="Employee", page_size=100,
)
```

### Step 3: Request Queue for Batch Operations
```python
import asyncio
from collections import deque

class FoundryRateLimiter:
    """Token bucket rate limiter for batch Foundry operations."""
    def __init__(self, max_per_second: int = 50):
        self.max_per_second = max_per_second
        self.tokens = max_per_second
        self._last_refill = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        self.tokens = min(self.max_per_second, self.tokens + elapsed * self.max_per_second)
        self._last_refill = now

    def acquire(self):
        self._refill()
        if self.tokens < 1:
            wait = (1 - self.tokens) / self.max_per_second
            time.sleep(wait)
            self._refill()
        self.tokens -= 1

limiter = FoundryRateLimiter(max_per_second=40)  # 80% of limit

def rate_limited_call(fn, *args, **kwargs):
    limiter.acquire()
    return retry_foundry_call(fn, *args, **kwargs)
```

### Step 4: Batch Operations with Rate Limiting
```python
def batch_update_objects(client, ontology, action_type, items, batch_size=10):
    """Apply actions in rate-limited batches."""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        for item in batch:
            result = rate_limited_call(
                client.ontologies.Action.apply,
                ontology=ontology,
                action_type=action_type,
                parameters=item,
            )
            results.append({"item": item, "status": result.validation})
        print(f"  Processed {min(i+batch_size, len(items))}/{len(items)}")
    return results
```

## Output
- Automatic retry on 429/5xx with exponential backoff
- Token bucket rate limiter for batch operations
- Rate-limited batch processing for bulk updates

## Error Handling
| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 429 | Rate limited | Wait `Retry-After` seconds, then retry |
| 500 | Server error | Retry with backoff |
| 502/503 | Gateway error | Retry with backoff |
| 400/403/404 | Client error | Do not retry — fix the request |

## Resources
- [Foundry API Reference](https://www.palantir.com/docs/foundry/api/general/overview/introduction)
- [Authentication Guide](https://www.palantir.com/docs/foundry/api/general/overview/authentication)

## Next Steps
For security best practices, see `palantir-security-basics`.
