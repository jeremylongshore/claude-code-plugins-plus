---
name: palantir-cost-tuning
description: |
  Optimize Palantir Foundry costs through compute tuning, incremental builds, and usage monitoring.
  Use when analyzing Foundry compute costs, reducing API usage,
  or implementing cost monitoring for Foundry workloads.
  Trigger with phrases like "palantir cost", "foundry billing",
  "reduce foundry costs", "foundry pricing", "foundry expensive".
allowed-tools: Read, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, cost, optimization]
compatible-with: claude-code, codex, openclaw
---

# Palantir Cost Tuning

## Overview
Optimize Foundry compute and API costs through incremental transforms, right-sized Spark profiles, efficient pagination, and usage monitoring.

## Prerequisites
- Active Foundry enrollment with build history
- Access to Foundry resource usage metrics
- Understanding of transform build patterns

## Instructions

### Step 1: Cost Drivers in Foundry
| Cost Category | Driver | Optimization |
|---------------|--------|-------------|
| Compute | Full rebuilds of large transforms | Use `@incremental()` |
| Compute | Oversized Spark profiles | Right-size `@configure` profiles |
| Storage | Redundant dataset snapshots | Configure retention policies |
| API | High-frequency polling | Use webhooks instead |
| API | Small page sizes | Use max page_size (500) |

### Step 2: Convert Full Rebuilds to Incremental
```python
from transforms.api import transform_df, Input, Output, incremental

# BEFORE: Full rebuild every run (expensive for large datasets)
@transform_df(Output("/out"), data=Input("/in"))
def expensive(data):
    return data.filter(data.status == "active")

# AFTER: Only processes new/changed rows
@incremental()
@transform_df(Output("/out"), data=Input("/in"))
def cheap(data):
    return data.filter(data.status == "active")
```

### Step 3: Right-Size Spark Profiles
```python
from transforms.api import configure

# DON'T: Default profile for everything
# DO: Match profile to actual data size

# Small data (< 1GB) — use lightweight transforms (no Spark)
from transforms.api import transform_polars
@transform_polars(Output("/out"), data=Input("/small_table"))
def small_job(data):
    return data.filter(data["status"] == "active")

# Medium data (1-50GB) — default profile is fine
@transform_df(Output("/out"), data=Input("/medium_table"))
def medium_job(data):
    return data.select("id", "name")

# Large data (50GB+) — explicit large profile
@configure(profile=["DRIVER_MEMORY_LARGE"])
@transform_df(Output("/out"), data=Input("/big_table"))
def large_job(data):
    return data.groupBy("region").count()
```

### Step 4: Replace Polling with Webhooks
```python
# EXPENSIVE: Polling every 30 seconds
import time
while True:
    result = client.ontologies.OntologyObject.list(
        ontology="co", object_type="Order", page_size=100,
    )
    process_new_orders(result.data)
    time.sleep(30)  # 2,880 API calls/day!

# CHEAP: Webhook-driven (0 polling API calls)
# Register webhook for ontology.object.created events
# See palantir-webhooks-events skill
```

### Step 5: Monitor Usage
```python
def log_api_usage(response):
    """Log rate limit headers to track usage patterns."""
    remaining = response.headers.get("X-RateLimit-Remaining", "?")
    limit = response.headers.get("X-RateLimit-Limit", "?")
    print(f"API usage: {remaining}/{limit} remaining")
```

## Output
- Incremental transforms reducing rebuild compute by 90%+
- Right-sized Spark profiles matching actual data volumes
- Webhook-driven architecture eliminating polling costs
- Usage monitoring for ongoing optimization

## Error Handling
| Optimization | Risk | Mitigation |
|-------------|------|------------|
| Incremental | Missed data on schema change | Schedule periodic full rebuild |
| Polars (no Spark) | Data too large for memory | Fall back to Spark for > 1GB |
| Aggressive caching | Stale data | Set TTL matching business requirements |
| Webhook-only | Missed events | Periodic reconciliation job |

## Resources
- [Incremental Transforms](https://www.palantir.com/docs/foundry/transforms-python/transforms-pipelines)
- [Transform Polars](https://www.palantir.com/docs/foundry/transforms-python/lightweight-api-evolution)
- [@configure Profiles](https://www.palantir.com/docs/foundry/api-reference/transforms-python-library/api-configure)

## Next Steps
For reference architecture, see `palantir-reference-architecture`.
