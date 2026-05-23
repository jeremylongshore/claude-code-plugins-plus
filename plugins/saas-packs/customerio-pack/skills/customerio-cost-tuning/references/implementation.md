# Customer.io Cost Tuning -- Implementation Details

## Understanding Customer.io Billing

Customer.io charges are based on the number of people in your workspace and message volume.
Key cost levers:

1. **Active person count** -- reduce by suppressing inactive contacts
2. **Email/SMS volume** -- optimize send frequency and campaign targeting
3. **API call volume** -- batch events and use efficient attribute updates

## Advanced Patterns

### Suppress Inactive Contacts

Remove contacts who have not engaged in a defined period to reduce billable people count:

```python
import os
import requests
from datetime import datetime, timedelta, timezone

CIO_APP_API_BASE = "https://api.customer.io/v1"
HEADERS = {
    "Authorization": f"Bearer {os.environ['CUSTOMERIO_APP_API_KEY']}",
    "Content-Type": "application/json",
}

def get_inactive_customers(days_inactive: int = 180) -> list[str]:
    """Find customers with no activity in the past N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_inactive)).timestamp()
    customers = []
    page = 1

    while True:
        resp = requests.get(
            f"{CIO_APP_API_BASE}/customers",
            headers=HEADERS,
            params={"page": page, "limit": 100},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("customers", [])
        if not batch:
            break

        for customer in batch:
            last_seen = customer.get("last_seen_at", 0)
            if last_seen < cutoff:
                customers.append(customer["id"])

        if len(batch) < 100:
            break
        page += 1

    return customers


def suppress_customers(customer_ids: list[str], dry_run: bool = True) -> dict:
    """Suppress inactive customers to reduce billable count."""
    if dry_run:
        print(f"[DRY RUN] Would suppress {len(customer_ids)} customers")
        return {"suppressed": 0, "dry_run": True, "count": len(customer_ids)}

    suppressed = 0
    for cid in customer_ids:
        try:
            resp = requests.put(
                f"{CIO_APP_API_BASE}/customers/{cid}/suppress",
                headers=HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            suppressed += 1
        except Exception as e:
            print(f"[WARN] Failed to suppress {cid}: {e}")

    return {"suppressed": suppressed, "total": len(customer_ids)}
```

### Batch Event Updates (Reduce API Call Volume)

```python
def batch_update_attributes(updates: list[dict]) -> int:
    """
    Update multiple customer attributes in a single API call.
    More efficient than making one call per customer.
    """
    # Customer.io supports batch imports via the bulk import API
    resp = requests.post(
        "https://track.customer.io/api/v2/batch",
        headers={
            "Authorization": f"Bearer {os.environ['CUSTOMERIO_TRACK_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={"batch": updates},
        timeout=30,
    )
    resp.raise_for_status()
    return len(updates)


# Instead of 100 individual API calls, use one batch call
updates = [
    {"type": "person", "action": "identify", "attributes": {"plan": "pro", "id": f"user-{i}"}}
    for i in range(100)
]
count = batch_update_attributes(updates)
print(f"Updated {count} customers in one batch call")
```

## Troubleshooting

### Unexpected High Person Count

1. Check if test/development contacts are being synced to production workspace
2. Review integrations (CRMs, data warehouses) that might be creating duplicate records
3. Audit inactive contacts and set up automatic suppression
4. Verify that delete events are properly sent for churned customers

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
