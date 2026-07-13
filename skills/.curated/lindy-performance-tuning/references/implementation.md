# Lindy Performance Tuning -- Implementation Details

## Latency Optimization

### Parallel Step Execution

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Any

def run_parallel_tasks(tasks: list[Callable], max_workers: int = 5) -> list[Any]:
    """Execute multiple independent API calls in parallel."""
    results = [None] * len(tasks)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {executor.submit(task): i for i, task in enumerate(tasks)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = {"error": str(e)}
    return results


def enrich_lead_parallel(lead_id: str, email: str) -> dict:
    """Fetch CRM data and tickets simultaneously (2x faster than sequential)."""
    crm_data, tickets = run_parallel_tasks([
        lambda: fetch_crm_data(lead_id),
        lambda: fetch_support_tickets(email),
    ])
    return {"crm": crm_data, "tickets": tickets}
```

## Advanced Patterns

### Response Cache

```python
import hashlib
import json
import time
from typing import Any, Optional

class AgentResponseCache:
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self._store: dict[str, dict] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _make_key(self, agent_id: str, inputs: dict) -> str:
        data = json.dumps({"id": agent_id, "inputs": inputs}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:20]

    def get(self, agent_id: str, inputs: dict) -> Optional[Any]:
        key = self._make_key(agent_id, inputs)
        entry = self._store.get(key)
        if entry and time.time() - entry["ts"] < self.ttl:
            self.hits += 1
            return entry["value"]
        self.misses += 1
        return None

    def set(self, agent_id: str, inputs: dict, value: Any) -> None:
        if len(self._store) >= self.max_size:
            oldest = min(self._store, key=lambda k: self._store[k]["ts"])
            del self._store[oldest]
        key = self._make_key(agent_id, inputs)
        self._store[key] = {"value": value, "ts": time.time()}

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


cache = AgentResponseCache(ttl_seconds=300)

def cached_trigger(agent_id: str, inputs: dict) -> dict:
    cached = cache.get(agent_id, inputs)
    if cached is not None:
        return cached
    result = trigger_lindy_agent(agent_id, inputs)
    cache.set(agent_id, inputs, result)
    return result
```

### Batch Processing

```python
import time

def process_batch(items: list[dict], agent_id: str,
                  batch_size: int = 10, delay: float = 0.5) -> list[dict]:
    """Process a large list in batches to avoid overwhelming the API."""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        print(f"Batch {i // batch_size + 1} ({len(batch)} items)...")
        batch_results = run_parallel_tasks([
            lambda item=item: trigger_lindy_agent(agent_id, item)
            for item in batch
        ], max_workers=min(len(batch), 5))
        results.extend(batch_results)
        if i + batch_size < len(items):
            time.sleep(delay)
    return results
```

## Troubleshooting

### Slow Agent Execution

1. Profile each step -- run logs show per-step timing
2. Check if AI steps use overly large context windows
3. Look for sequential steps that could be parallelized
4. Verify connected integrations are not rate-limiting

### High Memory Usage in Long-Running Agents

1. Clear conversation memory between unrelated agent runs
2. Use summarization steps to compress long histories
3. Pass only relevant excerpts, not entire email threads

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
