---
name: clari-cost-tuning
description: |
  Optimize Clari API usage and integration costs.
  Use when reducing API call volume, optimizing export frequency,
  or evaluating Clari license utilization.
  Trigger with phrases like "clari cost", "clari api usage",
  "reduce clari calls", "clari optimization".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Cost Tuning

## Overview

Minimize Clari API overhead: reduce export frequency, cache aggressively, export only needed data types, and monitor usage.

## Instructions

### Export Only What You Need

```python
# Full export (6 data types) -- more API load
full_types = ["forecast", "quota", "forecast_updated",
              "adjustment", "crm_total", "crm_closed"]

# Minimal export (2 data types) -- faster and lighter
minimal_types = ["forecast", "crm_closed"]

# Use minimal for dashboards, full for audit/compliance
```

### Optimize Export Frequency

| Use Case | Recommended Frequency |
|----------|-----------------------|
| Executive dashboard | Daily |
| Forecast accuracy tracking | Weekly |
| Compliance audit | Quarterly |
| Ad-hoc analysis | On demand |

### Cache to Avoid Redundant Exports

```python
# Cache recent exports (see clari-performance-tuning)
cache = ExportCache(ttl_hours=8)

def smart_export(client, forecast_name, period):
    cached = cache.get(forecast_name, period)
    if cached:
        print(f"Cache hit for {period}")
        return cached

    data = client.export_and_download(forecast_name, period)
    entries = data.get("entries", [])
    cache.set(forecast_name, period, entries)
    return entries
```

### Usage Tracking

```python
class ClariUsageTracker:
    def __init__(self):
        self.api_calls = 0
        self.exports = 0

    def track_call(self):
        self.api_calls += 1

    def track_export(self):
        self.exports += 1

    def report(self) -> dict:
        return {
            "api_calls": self.api_calls,
            "exports": self.exports,
        }
```

## Resources

- [Clari Pricing](https://www.clari.com/pricing)

## Next Steps

For architecture patterns, see `clari-reference-architecture`.
