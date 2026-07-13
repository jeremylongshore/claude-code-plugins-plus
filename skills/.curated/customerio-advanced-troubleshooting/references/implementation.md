# Customer.io Advanced Troubleshooting -- Implementation Details

## Diagnosing Delivery Issues

### Check Message Delivery Status via API

```python
import os
import requests

CIO_APP_API_BASE = "https://api.customer.io/v1"
CIO_TRACK_API_BASE = "https://track.customer.io/api/v2"

HEADERS_APP = {
    "Authorization": f"Bearer {os.environ['CUSTOMERIO_APP_API_KEY']}",
    "Content-Type": "application/json",
}
HEADERS_TRACK = {
    "Authorization": f"Bearer {os.environ['CUSTOMERIO_TRACK_API_KEY']}",
    "Content-Type": "application/json",
}


def get_customer_messages(customer_id: str, limit: int = 20) -> list[dict]:
    """Retrieve recent messages sent to a specific customer."""
    resp = requests.get(
        f"{CIO_APP_API_BASE}/customers/{customer_id}/messages",
        headers=HEADERS_APP,
        params={"limit": limit},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("messages", [])


def get_message_details(message_id: str) -> dict:
    """Get detailed delivery information for a specific message."""
    resp = requests.get(
        f"{CIO_APP_API_BASE}/messages/{message_id}",
        headers=HEADERS_APP,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def check_delivery_issues(customer_id: str) -> dict:
    """Identify delivery problems for a customer."""
    messages = get_customer_messages(customer_id)
    issues = []
    delivered = 0
    bounced = 0
    unsubscribed = 0

    for msg in messages:
        status = msg.get("status", "")
        if status == "delivered":
            delivered += 1
        elif status in ("bounced", "dropped"):
            bounced += 1
            issues.append(f"Message {msg['id']} bounced: {msg.get('failure_message', 'unknown')}")
        elif status == "unsubscribed":
            unsubscribed += 1

    total = len(messages)
    return {
        "customer_id": customer_id,
        "total_messages": total,
        "delivered": delivered,
        "bounced": bounced,
        "unsubscribed": unsubscribed,
        "delivery_rate": f"{delivered / max(1, total):.0%}",
        "issues": issues,
    }
```

### Debug Event Tracking

```python
def verify_customer_attributes(customer_id: str, expected_attrs: dict) -> list[str]:
    """Check if a customer has the expected attributes for segmentation."""
    resp = requests.get(
        f"{CIO_APP_API_BASE}/customers/{customer_id}",
        headers=HEADERS_APP,
        timeout=10,
    )
    if resp.status_code == 404:
        return [f"Customer '{customer_id}' not found -- check ID and workspace"]
    resp.raise_for_status()
    customer = resp.json()
    actual_attrs = customer.get("attributes", {})

    mismatches = []
    for key, expected_value in expected_attrs.items():
        actual_value = actual_attrs.get(key)
        if actual_value is None:
            mismatches.append(f"Missing attribute '{key}' (expected: {expected_value!r})")
        elif actual_value != expected_value:
            mismatches.append(f"Attribute '{key}': expected {expected_value!r}, got {actual_value!r}")

    return mismatches
```

## Advanced Patterns

### Segment Membership Check

```python
def check_segment_membership(customer_id: str, segment_ids: list[str]) -> dict[str, bool]:
    """Verify which segments a customer belongs to."""
    resp = requests.get(
        f"{CIO_APP_API_BASE}/customers/{customer_id}/segments",
        headers=HEADERS_APP,
        timeout=10,
    )
    resp.raise_for_status()
    member_of = {seg["id"] for seg in resp.json().get("segments", [])}
    return {seg_id: seg_id in member_of for seg_id in segment_ids}
```

## Troubleshooting

### Campaign Not Triggering

1. Verify the trigger event name matches exactly (case-sensitive)
2. Check that the customer is in the campaign's entry segment
3. Confirm the campaign is active (not paused or draft)
4. Look at the campaign's entry conditions -- all must be met

### Emails Going to Spam

1. Verify SPF, DKIM, and DMARC records are configured
2. Check bounce and complaint rates in the sending domain settings
3. Review email content for spam trigger words
4. Confirm the From address matches your authenticated sending domain

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
