---
name: palantir-performance-tuning
description: |
  Optimize Palantir Foundry API performance with caching, batching, and pagination.
  Use when experiencing slow API responses, optimizing transform builds,
  or improving request throughput for Foundry integrations.
  Trigger with phrases like "palantir performance", "optimize foundry",
  "foundry slow", "palantir caching", "foundry batch".
allowed-tools: Read, Write, Edit
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, performance, optimization]
compatible-with: claude-code, codex, openclaw
---

# Palantir Performance Tuning

## Overview
Optimize Foundry API performance: efficient pagination, client-side caching, batch object retrieval, and Spark transform tuning with `@configure` profiles.

## Prerequisites
- Completed `palantir-install-auth` setup
- Working Foundry integration to optimize
- Access to Foundry build metrics (for transform tuning)

## Instructions

### Step 1: Efficient Pagination
```python
from functools import lru_cache

def fetch_all_objects(client, ontology: str, object_type: str, page_size: int = 500):
    """Fetch all objects with maximum page size to minimize API calls."""
    all_objects = []
    page_token = None
    while True:
        result = client.ontologies.OntologyObject.list(
            ontology=ontology,
            object_type=object_type,
            page_size=min(page_size, 500),  # Foundry max is 500
            page_token=page_token,
        )
        all_objects.extend(result.data)
        page_token = result.next_page_token
        if not page_token:
            break
    return all_objects
```

### Step 2: Client-Side Caching
```python
from cachetools import TTLCache
import hashlib, json

_cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute TTL

def cached_get_object(client, ontology, object_type, primary_key):
    """Cache Ontology object reads to reduce API calls."""
    cache_key = f"{ontology}:{object_type}:{primary_key}"
    if cache_key in _cache:
        return _cache[cache_key]
    obj = client.ontologies.OntologyObject.get(
        ontology=ontology, object_type=object_type, primary_key=primary_key,
    )
    _cache[cache_key] = obj
    return obj

def invalidate_cache(ontology, object_type, primary_key):
    cache_key = f"{ontology}:{object_type}:{primary_key}"
    _cache.pop(cache_key, None)
```

### Step 3: Batch Object Retrieval
```python
def batch_get_objects(client, ontology, object_type, primary_keys, batch_size=50):
    """Retrieve multiple objects using search filter instead of individual GETs."""
    results = {}
    for i in range(0, len(primary_keys), batch_size):
        batch = primary_keys[i:i+batch_size]
        search_result = client.ontologies.OntologyObject.search(
            ontology=ontology,
            object_type=object_type,
            where={
                "type": "in",
                "field": "primaryKey",
                "value": batch,
            },
            page_size=batch_size,
        )
        for obj in search_result.data:
            pk = obj.properties.get("primaryKey", obj.rid)
            results[pk] = obj
    return results
```

### Step 4: Transform Build Performance
```python
from transforms.api import transform_df, Input, Output, configure, incremental

# Use incremental for append-only data — processes only new rows
@incremental()
@transform_df(
    Output("/Company/datasets/events_processed"),
    events=Input("/Company/datasets/raw_events"),
)
def process_events(events):
    return events.filter(events.event_type.isNotNull())

# Tune Spark resources for heavy aggregations
@configure(profile=["DRIVER_MEMORY_LARGE", "EXECUTOR_MEMORY_LARGE"])
@transform_df(
    Output("/Company/datasets/daily_summary"),
    data=Input("/Company/datasets/large_table"),
)
def daily_summary(data):
    from pyspark.sql import functions as F
    return data.groupBy("date", "region").agg(
        F.sum("revenue").alias("total_revenue"),
        F.countDistinct("user_id").alias("unique_users"),
    )
```

### Step 5: Connection Pooling
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503]),
)
session.mount("https://", adapter)
```

## Output
- Maximum page size pagination reducing API call count
- TTL-based caching for repeated object reads
- Batch search replacing individual GET calls
- Optimized Spark transforms with `@configure` and `@incremental`

## Error Handling
| Performance Issue | Diagnosis | Fix |
|-------------------|-----------|-----|
| Slow pagination | Small page_size | Increase to 500 (max) |
| Repeated reads | No caching | Add TTLCache |
| N+1 object fetches | Individual GETs | Use batch search |
| Transform OOM | Insufficient memory | Add `@configure(profile=["..._LARGE"])` |
| Full rebuild on append data | Not incremental | Add `@incremental()` decorator |

## Resources
- [Transforms @configure](https://www.palantir.com/docs/foundry/api-reference/transforms-python-library/api-configure)
- [Incremental Transforms](https://www.palantir.com/docs/foundry/transforms-python/transforms-pipelines)
- [cachetools](https://cachetools.readthedocs.io/)

## Next Steps
For cost optimization, see `palantir-cost-tuning`.
