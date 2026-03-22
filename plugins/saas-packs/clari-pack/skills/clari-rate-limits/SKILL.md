---
name: clari-rate-limits
description: |
  Handle Clari API rate limits with backoff and export job scheduling.
  Use when hitting 429 errors, optimizing export frequency,
  or scheduling bulk forecast exports.
  Trigger with phrases like "clari rate limit", "clari 429",
  "clari throttle", "clari api limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Rate Limits

## Overview

The Clari API enforces rate limits per API key. Export jobs are asynchronous and queued server-side, so the primary concern is polling frequency and concurrent export requests.

## Rate Limit Behavior

| Aspect | Value |
|--------|-------|
| Scope | Per API key |
| Response on limit | HTTP 429 |
| Export job queue | Server-managed, async |
| Recommended polling | 5-10 second intervals |

## Instructions

### Exponential Backoff for Export Polling

```python
import time
import requests

def poll_with_backoff(
    job_id: str,
    api_key: str,
    max_attempts: int = 60,
    base_delay: float = 5.0,
    max_delay: float = 60.0,
) -> dict:
    for attempt in range(max_attempts):
        resp = requests.get(
            f"https://api.clari.com/v4/export/jobs/{job_id}",
            headers={"apikey": api_key},
        )

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", base_delay))
            time.sleep(retry_after)
            continue

        resp.raise_for_status()
        status = resp.json()

        if status["status"] in ("COMPLETED", "FAILED"):
            return status

        delay = min(base_delay * (1.5 ** attempt), max_delay)
        time.sleep(delay)

    raise TimeoutError(f"Job {job_id} did not complete in {max_attempts} attempts")
```

### Sequential Export Scheduler

```python
def export_all_periods(
    client,
    forecast_name: str,
    periods: list[str],
    delay_between: float = 10.0,
) -> list[dict]:
    results = []
    for period in periods:
        print(f"Exporting {period}...")
        job = client.export_forecast(forecast_name, period)
        result = poll_with_backoff(job["jobId"], client.config.api_key)
        results.append(result)
        time.sleep(delay_between)  # Avoid hitting rate limits
    return results
```

## Error Handling

| Scenario | Detection | Response |
|----------|-----------|----------|
| 429 with Retry-After | Check header | Wait exact duration |
| 429 without header | Status code only | Backoff from 5s |
| Job queue full | Multiple pending jobs | Wait for completion before new exports |

## Resources

- [Clari API Reference](https://developer.clari.com/documentation/external_spec)

## Next Steps

For security configuration, see `clari-security-basics`.
