# Clay Reliability Patterns — Implementation Guide

## Enrichment Job Tracking

```python
import time
import redis

r = redis.Redis()

class ClayEnrichmentTracker:
    def submit_rows(self, table_id: str, rows: list) -> str:
        response = requests.post(
            f"{CLAY_API}/tables/{table_id}/rows",
            json={"rows": rows},
            headers=self.headers
        )
        job_id = response.json()["job_id"]
        r.hset(f"clay:job:{job_id}", mapping={
            "table_id": table_id,
            "row_count": len(rows),
            "submitted_at": time.time(),
            "status": "pending"
        })
        return job_id

    def check_completion(self, job_id: str, timeout_minutes: int = 30) -> bool:
        job = r.hgetall(f"clay:job:{job_id}")
        elapsed = time.time() - float(job[b"submitted_at"])
        if elapsed > timeout_minutes * 60:
            r.hset(f"clay:job:{job_id}", "status", "timeout")
            return False
        table_id = job[b"table_id"].decode()
        status = requests.get(
            f"{CLAY_API}/tables/{table_id}/status",
            headers=self.headers
        ).json()
        return status["enrichment_complete"]
```

## Credit Budget Circuit Breaker

```python
class CreditBudgetBreaker:
    def __init__(self, daily_limit: int = 1000):
        self.daily_limit = daily_limit
        self.today_key = f"clay:credits:{time.strftime('%Y-%m-%d')}"

    def can_proceed(self, estimated_credits: int) -> bool:
        used = int(r.get(self.today_key) or 0)
        if used + estimated_credits > self.daily_limit:
            return False
        return True

    def record_usage(self, credits_used: int):
        r.incrby(self.today_key, credits_used)
        r.expire(self.today_key, 86400 * 2)

budget = CreditBudgetBreaker(daily_limit=5000)

def safe_enrich(table_id, rows, credits_per_row=3):
    estimated = len(rows) * credits_per_row
    if not budget.can_proceed(estimated):
        raise Exception("Daily credit budget exceeded")
    result = submit_to_clay(table_id, rows)
    budget.record_usage(estimated)
    return result
```

## Provider Health Tracking

```python
class ProviderHealth:
    def __init__(self):
        self.window = 100

    def record(self, provider: str, success: bool):
        key = f"clay:provider:{provider}"
        r.lpush(key, 1 if success else 0)
        r.ltrim(key, 0, self.window - 1)

    def success_rate(self, provider: str) -> float:
        results = r.lrange(f"clay:provider:{provider}", 0, -1)
        if not results:
            return 1.0
        return sum(int(x) for x in results) / len(results)

    def get_healthy_providers(self, threshold: float = 0.5) -> list:
        providers = ["clearbit", "zoominfo", "apollo", "hunter"]
        return [p for p in providers if self.success_rate(p) >= threshold]
```

## Batch Processing with Dead Letter Queue

```python
from collections import deque

class ClayBatchProcessor:
    def __init__(self):
        self.dlq = deque(maxlen=10000)

    def process_batch(self, table_id: str, rows: list, batch_size: int = 50):
        results = {"success": 0, "failed": 0}
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            try:
                response = requests.post(
                    f"{CLAY_API}/tables/{table_id}/rows",
                    json={"rows": batch}, headers=self.headers
                )
                response.raise_for_status()
                results["success"] += len(batch)
            except Exception as e:
                results["failed"] += len(batch)
                self.dlq.append({"batch": batch, "error": str(e)})
            time.sleep(2)
        return results
```

## Health Check

```python
health = {
    "credits_remaining": get_credit_balance(),
    "daily_usage": int(r.get(budget.today_key) or 0),
    "active_jobs": len(r.keys("clay:job:*")),
    "dlq_size": len(processor.dlq)
}
```
