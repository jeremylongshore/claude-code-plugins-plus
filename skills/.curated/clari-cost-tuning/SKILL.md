---
name: clari-cost-tuning
description: 'Optimize Clari API usage and integration costs.

  Use when reducing API call volume, optimizing export frequency,

  or evaluating Clari license utilization.

  Trigger with phrases like "clari cost", "clari api usage",

  "reduce clari calls", "clari optimization".

  '
allowed-tools: Read, Write, Edit, Grep
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
# Clari Cost Tuning

## Overview

Minimize Clari API overhead: reduce export frequency, cache aggressively, export only needed data types, and monitor usage.

## Prerequisites

- An approved consumer inventory and freshness requirement for each report
- Usage telemetry for API calls, export jobs, warehouse loads, and cache age
- Data-owner approval for retention, aggregation, and delivery changes
- A non-production validation path for schedule or payload changes

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

## Error Handling

| Condition | Response |
|---|---|
| Consumer needs fresher data than the approved schedule | Obtain owner approval and measure incremental load before changing cadence. |
| Cache returns an expired or mismatched period | Discard it and run the controlled export path. |
| Usage spikes or provider throttles | Reduce scope/concurrency and preserve the last certified dataset. |
| Cost reduction removes an audit-required field | Reject the change until the compliance owner approves an alternative. |

## Output

Publish a cost-and-usage decision with current and proposed cadence, payload
scope, cache policy, observed API/warehouse load, forecast impact, owner, and
rollback threshold. Keep business amounts and rep-level data out of the
operational report unless the recipient is authorized.

## Examples

Move a non-critical dashboard from hourly full exports to daily minimal exports
in staging, verify freshness and audit coverage, and compare job count and
warehouse cost for a week. Roll back the schedule if the certified data window
or required field coverage no longer meets the report contract.

## Resources

- [Clari Pricing](https://www.clari.com/pricing)

## Next Steps

For architecture patterns, see `clari-reference-architecture`.
