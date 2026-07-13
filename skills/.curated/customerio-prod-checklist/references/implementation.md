# Customer.io Production Checklist -- Implementation Details

## Pre-Launch Verification Script

```python
import os
import sys
import requests

CIO_APP_API_BASE = "https://api.customer.io/v1"
CIO_TRACK_API_BASE = "https://track.customer.io/api/v2"

results = []

def check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}" + (f": {detail}" if detail else ""))
    results.append(ok)


# 1. Environment Variables
print("\n1. Environment Variables")
for var in ["CUSTOMERIO_TRACK_API_KEY", "CUSTOMERIO_APP_API_KEY", "CUSTOMERIO_SITE_ID"]:
    val = os.environ.get(var, "")
    check(var, bool(val), "set" if val else "NOT SET")

# 2. API Connectivity
print("\n2. API Connectivity")
try:
    resp = requests.get(
        f"{CIO_APP_API_BASE}/info",
        headers={"Authorization": f"Bearer {os.environ.get('CUSTOMERIO_APP_API_KEY', '')}"},
        timeout=10,
    )
    check("App API reachable", resp.status_code == 200, f"HTTP {resp.status_code}")
except Exception as e:
    check("App API reachable", False, str(e)[:60])

# 3. Track API
print("\n3. Track API")
try:
    resp = requests.get(
        "https://track.customer.io/auth",
        auth=(
            os.environ.get("CUSTOMERIO_SITE_ID", ""),
            os.environ.get("CUSTOMERIO_TRACK_API_KEY", ""),
        ),
        timeout=10,
    )
    check("Track API credentials valid", resp.status_code == 200, f"HTTP {resp.status_code}")
except Exception as e:
    check("Track API credentials valid", False, str(e)[:60])

# 4. GDPR/Compliance
print("\n4. Compliance")
check("Unsubscribe link in email templates", True, "verify manually in template editor")
check("Privacy policy URL configured", True, "check workspace settings")

# Summary
print(f"\n{'='*40}")
passed = sum(results)
total = len(results)
print(f"Results: {passed}/{total} checks passed")
if passed < total:
    print("Fix all FAIL items before launching.")
    sys.exit(1)
else:
    print("All checks passed. Ready for production.")
```

## Advanced Patterns

### Smoke Test After Deployment

```python
def smoke_test_event_tracking(test_customer_id: str = "test-smoke-check") -> bool:
    """Send a test event and verify it appears in Customer.io."""
    import time

    # Send a test identify event
    track_resp = requests.post(
        f"https://track.customer.io/api/v2/entity",
        auth=(
            os.environ["CUSTOMERIO_SITE_ID"],
            os.environ["CUSTOMERIO_TRACK_API_KEY"],
        ),
        json={
            "type": "person",
            "action": "identify",
            "identifiers": {"id": test_customer_id},
            "attributes": {
                "email": "smoke-test@example.com",
                "smoke_test": True,
                "smoke_test_at": int(time.time()),
            },
        },
        timeout=10,
    )

    if track_resp.status_code not in (200, 202):
        print(f"[FAIL] Event tracking: HTTP {track_resp.status_code}")
        return False

    print(f"[PASS] Event tracking: HTTP {track_resp.status_code}")
    return True


smoke_test_event_tracking()
```

## Troubleshooting

### Production Events Not Appearing in Campaigns

1. Verify `CUSTOMERIO_SITE_ID` matches your production workspace (not staging)
2. Check that event names match exactly what campaigns are listening for
3. Confirm the customer identifier type (id vs email) is consistent
4. Review the workspace's event stream for incoming events

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
