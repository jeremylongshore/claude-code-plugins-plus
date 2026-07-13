# Customer.io Rate Limits -- Implementation Details

## Rate Limit Reference

| API | Limit |
|-----|-------|
| Track API (identify/event) | 100 requests/second per site |
| App API (data/reporting) | 10 requests/second |
| Bulk imports | 1 concurrent job per workspace |

## Advanced Patterns

### Throttled Event Sender

```python
import time
import threading
import requests
import os

class ThrottledTracker:
    """Send Customer.io events at a controlled rate to stay within limits."""

    def __init__(self, requests_per_second: float = 80.0):
        self.min_interval = 1.0 / requests_per_second
        self._lock = threading.Lock()
        self._last_call = 0.0
        self.site_id = os.environ["CUSTOMERIO_SITE_ID"]
        self.api_key = os.environ["CUSTOMERIO_TRACK_API_KEY"]

    def _wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.monotonic()

    def identify(self, customer_id: str, attributes: dict) -> bool:
        with self._lock:
            self._wait()
        resp = requests.post(
            "https://track.customer.io/api/v2/entity",
            auth=(self.site_id, self.api_key),
            json={
                "type": "person",
                "action": "identify",
                "identifiers": {"id": customer_id},
                "attributes": attributes,
            },
            timeout=10,
        )
        return resp.status_code in (200, 202)

    def track(self, customer_id: str, event_name: str, data: dict | None = None) -> bool:
        with self._lock:
            self._wait()
        resp = requests.post(
            "https://track.customer.io/api/v2/entity",
            auth=(self.site_id, self.api_key),
            json={
                "type": "person",
                "action": "event",
                "identifiers": {"id": customer_id},
                "name": event_name,
                "attributes": data or {},
            },
            timeout=10,
        )
        return resp.status_code in (200, 202)


tracker = ThrottledTracker(requests_per_second=80.0)

# Bulk import 1000 customers within rate limits
customers = [{"id": f"user-{i}", "email": f"user{i}@example.com"} for i in range(1000)]
for c in customers:
    tracker.identify(c["id"], {"email": c["email"]})
```

### Batch Import for High Volume

For importing more than 1000 records, use the bulk import API instead of individual events:

```python
import json
import csv
from pathlib import Path

def build_bulk_import_file(customers: list[dict], output_path: str = "import.csv") -> str:
    """
    Create a CSV file for Customer.io bulk import.
    Bulk imports bypass per-request rate limits.
    """
    if not customers:
        raise ValueError("No customers to import")

    fieldnames = list(customers[0].keys())
    if "id" not in fieldnames and "email" not in fieldnames:
        raise ValueError("Each customer must have 'id' or 'email' field")

    output = Path(output_path)
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(customers)

    print(f"Created import file: {output} ({len(customers)} records)")
    return str(output)


customers = [{"id": f"user-{i}", "email": f"user{i}@example.com", "plan": "pro"} for i in range(10000)]
build_bulk_import_file(customers, "bulk-import.csv")
# Then upload via Customer.io dashboard: Data & Events > People > Import
```

## Troubleshooting

### 429 Errors Despite Staying Under Limits

1. Multiple services sharing the same site credentials -- aggregate rate applies
2. Check if CI/CD pipelines run tests that send events to production workspace
3. Burst traffic from campaign triggers (many users qualifying at once)
4. Review the Retry-After header value and respect it exactly

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
