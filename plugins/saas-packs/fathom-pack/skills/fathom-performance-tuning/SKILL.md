---
name: fathom-performance-tuning
description: |
  Optimize Fathom API performance with caching and batch processing.
  Trigger with phrases like "fathom performance", "fathom caching", "optimize fathom".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Performance Tuning

## Cache Meeting Data

```python
from functools import lru_cache
import time

class CachedFathomClient(FathomClient):
    def __init__(self, cache_ttl=300, **kwargs):
        super().__init__(**kwargs)
        self._cache = {}
        self._cache_ttl = cache_ttl

    def get_transcript_cached(self, recording_id: str) -> dict:
        key = f"transcript:{recording_id}"
        if key in self._cache:
            data, ts = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return data
        result = self.get_transcript(recording_id)
        self._cache[key] = (result, time.time())
        return result
```

## Use Webhooks Instead of Polling

Instead of polling for new meetings, use webhooks (see `fathom-webhooks-events`) to receive data as soon as it is ready.

## Batch Processing Within Rate Limits

```python
import time

def process_meetings_batch(client, meeting_ids, batch_size=50):
    for i in range(0, len(meeting_ids), batch_size):
        batch = meeting_ids[i:i+batch_size]
        for mid in batch:
            client.get_transcript(mid)
        if i + batch_size < len(meeting_ids):
            time.sleep(60)  # Respect 60 req/min limit
```

## Next Steps

For cost optimization, see `fathom-cost-tuning`.
