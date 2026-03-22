---
name: vastai-rate-limits
description: |
  Handle Vast.ai API rate limits with backoff and request optimization.
  Use when encountering 429 errors, implementing retry logic,
  or optimizing API request throughput.
  Trigger with phrases like "vastai rate limit", "vastai throttling",
  "vastai 429", "vastai retry", "vastai backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, api]

---
# Vast.ai Rate Limits

## Overview
Handle Vast.ai REST API rate limits gracefully. The API at `cloud.vast.ai/api/v0` returns HTTP 429 when request limits are exceeded. Most operations (search, show) are read-heavy and rarely hit limits, but automated scripts doing rapid provisioning or polling can trigger throttling.

## Prerequisites
- Vast.ai CLI or REST API client
- Understanding of exponential backoff

## Instructions

### Step 1: Rate-Limited HTTP Client

```python
import requests
import time

class RateLimitedVastClient:
    BASE_URL = "https://cloud.vast.ai/api/v0"

    def __init__(self, api_key, min_delay=0.5, max_retries=5):
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {api_key}"
        self.min_delay = min_delay
        self.max_retries = max_retries
        self.last_request = 0

    def request(self, method, endpoint, **kwargs):
        # Enforce minimum delay between requests
        elapsed = time.time() - self.last_request
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)

        for attempt in range(self.max_retries):
            self.last_request = time.time()
            resp = self.session.request(method, f"{self.BASE_URL}{endpoint}", **kwargs)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                print(f"Rate limited. Waiting {retry_after}s (attempt {attempt+1})")
                time.sleep(retry_after)
                continue

            resp.raise_for_status()
            return resp.json()

        raise RuntimeError("Max retries exceeded due to rate limiting")
```

### Step 2: Polling with Adaptive Backoff

```python
def poll_instance_status(client, instance_id, target="running", timeout=300):
    """Poll instance status with increasing intervals."""
    start = time.time()
    interval = 5  # Start at 5s, increase to max 30s

    while time.time() - start < timeout:
        info = client.request("GET", f"/instances/{instance_id}/")
        status = info.get("actual_status", "unknown")

        if status == target:
            return info
        if status in ("error", "offline"):
            raise RuntimeError(f"Instance {instance_id} failed: {status}")

        time.sleep(interval)
        interval = min(interval * 1.5, 30)

    raise TimeoutError(f"Instance did not reach '{target}' within {timeout}s")
```

### Step 3: Batch Search with Throttling

```python
def batch_search(client, gpu_configs):
    """Search for multiple GPU types with rate-limit-safe delays."""
    results = {}
    for config in gpu_configs:
        query = GPUQuery(**config).to_filter()
        offers = client.request("GET", "/bundles/", params={"q": str(query)})
        results[config.get("gpu_name", "any")] = offers.get("offers", [])
        time.sleep(1)  # Be polite between searches
    return results

# Usage
configs = [
    {"gpu_name": "RTX_4090", "max_dph": 0.30},
    {"gpu_name": "A100", "max_dph": 2.00},
    {"gpu_name": "H100_SXM", "max_dph": 4.00},
]
all_offers = batch_search(client, configs)
```

### Step 4: Request Optimization

Strategies to reduce API calls:
- **Cache search results**: Offers change slowly; cache for 60-120 seconds
- **Use `--limit`**: Restrict search results to what you need
- **Batch instance checks**: Use `show instances` (lists all) instead of individual `show instance ID` calls
- **Avoid polling loops**: Use longer intervals (15-30s) for status checks

## Output
- Rate-limited HTTP client with automatic retry on 429
- Adaptive polling for instance status changes
- Batch search with inter-request delays
- Request optimization strategies

## Error Handling
| Scenario | Response |
|----------|----------|
| First 429 | Wait `Retry-After` header value, then retry |
| Repeated 429s | Double wait time between retries |
| 429 during provisioning | Instance creation is idempotent; safe to retry |
| 429 during search | Cache previous results and use them temporarily |

## Resources
- [Vast.ai REST API](https://vast.ai/developers/api)
- [API Reference](https://docs.vast.ai/api-reference/introduction)

## Next Steps
For security best practices, see `vastai-security-basics`.

## Examples

**Safe multi-instance provisioning**: Create 10 instances with 2-second delays between each `create instance` call to avoid triggering rate limits during cluster setup.

**Efficient monitoring**: Poll all instances with a single `show instances` call every 30 seconds instead of individual calls per instance.
