---
name: clari-performance-tuning
description: 'Optimize Clari API performance with caching, batch exports, and data
  pipeline efficiency.

  Use when exports take too long, optimizing data warehouse load times,

  or reducing API calls in multi-forecast environments.

  Trigger with phrases like "clari performance", "clari slow export",

  "optimize clari pipeline", "clari caching".

  '
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- revenue-intelligence
- forecasting
- clari
compatibility: Designed for Claude Code
---
# Clari Performance Tuning

## Overview

Optimize Clari export pipelines: reduce export times, cache forecast data, and parallelize multi-period exports.

## Prerequisites

- A scoped Clari API credential stored outside source control
- An approved forecast/export scope and named data owner
- A warehouse destination with retention and access controls
- A representative non-production or read-only validation window

## Instructions

### Parallel Multi-Period Export

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def parallel_export(
    client,
    forecast_name: str,
    periods: list[str],
    max_workers: int = 3,
) -> dict[str, list[dict]]:
    results = {}

    def export_period(period: str) -> tuple[str, list[dict]]:
        data = client.export_and_download(forecast_name, period)
        return period, data.get("entries", [])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(export_period, p): p for p in periods
        }
        for future in as_completed(futures):
            period, entries = future.result()
            results[period] = entries
            print(f"  {period}: {len(entries)} entries")

    return results
```

### Cache Export Results

```python
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

class ExportCache:
    def __init__(self, cache_dir: str = ".cache/clari", ttl_hours: int = 4):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _key(self, forecast: str, period: str) -> str:
        return hashlib.md5(f"{forecast}:{period}".encode()).hexdigest()

    def get(self, forecast: str, period: str) -> list[dict] | None:
        path = self.cache_dir / f"{self._key(forecast, period)}.json"
        if not path.exists():
            return None
        meta = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(meta["cached_at"])
        if datetime.utcnow() - cached_at > self.ttl:
            return None
        return meta["entries"]

    def set(self, forecast: str, period: str, entries: list[dict]):
        path = self.cache_dir / f"{self._key(forecast, period)}.json"
        path.write_text(json.dumps({
            "cached_at": datetime.utcnow().isoformat(),
            "entries": entries,
        }))
```

### Incremental Load to Warehouse

```sql
-- Use MERGE for incremental updates instead of full reload
MERGE INTO clari_forecasts AS target
USING staging_clari AS source
ON target.owner_email = source.owner_email
   AND target.time_period = source.time_period
   AND target.forecast_name = source.forecast_name
WHEN MATCHED THEN UPDATE SET
    forecast_amount = source.forecast_amount,
    quota_amount = source.quota_amount,
    crm_total = source.crm_total,
    crm_closed = source.crm_closed,
    exported_at = source.exported_at
WHEN NOT MATCHED THEN INSERT VALUES (
    source.owner_name, source.owner_email, source.forecast_amount,
    source.quota_amount, source.crm_total, source.crm_closed,
    source.adjustment_amount, source.time_period,
    source.exported_at, source.forecast_name
);
```

## Performance Benchmarks

| Optimization | Before | After |
|--------------|--------|-------|
| Sequential 4-period export | 2 min | 40s (parallel) |
| Cache hit | 5-10s API call | <1ms |
| Full table reload | 30s | 5s (MERGE) |

## Error Handling

| Condition | Response |
|---|---|
| Export job fails or times out | Stop the batch, retain the job ID, and retry only within a bounded budget. |
| Cached result is stale | Expire it by policy and re-export rather than silently mixing periods. |
| Warehouse merge is rejected | Preserve the staged data, inspect the schema/constraint failure, and do not fall back to a destructive reload. |
| API rate limiting occurs | Reduce concurrency and honor retry guidance before resuming. |

## Output

Return a per-period export manifest with source job IDs, record counts, cache
age, destination load status, duration, and a redacted failure reason where
applicable. Forecast and owner-level information remains access-controlled;
the performance report should expose aggregates rather than raw sales data.

## Examples

Export two closed periods in staging with a concurrency limit of two, confirm
their counts and timestamps in the warehouse, then rerun once to prove the
cache path is fresh and idempotent. If a period returns partial data, publish a
failed manifest and halt downstream reporting instead of merging it with a
previous period’s result.

## Resources

- [Clari API Reference](https://developer.clari.com/documentation/external_spec)

## Next Steps

For cost optimization, see `clari-cost-tuning`.
