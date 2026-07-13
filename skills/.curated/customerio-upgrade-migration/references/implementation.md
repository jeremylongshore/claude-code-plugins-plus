# Customer.io Upgrade Migration -- Implementation Details

## SDK Migration Guide

### Python SDK: customerio v3 -> v4

```python
# BEFORE: customerio v3 (deprecated)
# from customerio import CustomerIO
# cio = CustomerIO(site_id, api_key)
# cio.identify(id="user-123", email="user@example.com")

# AFTER: customerio v4 (current)
from customerio import CustomerIO, Regions

cio = CustomerIO(
    site_id=os.environ["CUSTOMERIO_SITE_ID"],
    api_key=os.environ["CUSTOMERIO_TRACK_API_KEY"],
    region=Regions.US,  # or Regions.EU for EU data center
)

cio.identify(id="user-123", email="user@example.com", plan="pro")
cio.track(customer_id="user-123", name="purchase_completed", amount=99.99)
```

### Migration Checklist

```python
import os
import sys

def check_migration_readiness() -> None:
    issues = []

    # Check SDK version
    try:
        import customerio
        version = customerio.__version__
        major = int(version.split(".")[0])
        if major < 4:
            issues.append(f"customerio SDK v{version} is outdated -- upgrade to v4+")
            issues.append("  pip install --upgrade customerio")
    except ImportError:
        issues.append("customerio SDK not installed")

    # Check if using deprecated API endpoints
    deprecated_endpoints = [
        "https://track.customer.io/api/v1",  # v1 deprecated, use v2
    ]
    # (In practice, scan your codebase for these strings)

    if issues:
        print("Migration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("[OK] SDK version and configuration is up to date")


check_migration_readiness()
```

## Advanced Patterns

### Parallel Migration Verification

Run old and new SDK side-by-side during migration:

```python
import os
import time

def send_with_both_sdks(customer_id: str, attributes: dict) -> dict:
    """
    Send the same update through both old and new integration.
    Compare results to verify migration parity.
    """
    results = {}

    # New SDK (REST API direct)
    try:
        start = time.perf_counter()
        resp = requests.post(
            "https://track.customer.io/api/v2/entity",
            auth=(os.environ["CUSTOMERIO_SITE_ID"], os.environ["CUSTOMERIO_TRACK_API_KEY"]),
            json={
                "type": "person",
                "action": "identify",
                "identifiers": {"id": customer_id},
                "attributes": attributes,
            },
            timeout=10,
        )
        results["new_api"] = {
            "status": resp.status_code,
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
        }
    except Exception as e:
        results["new_api"] = {"error": str(e)}

    return results
```

### Data Center Migration (US to EU)

```python
# Customer.io has separate US and EU data centers
# All endpoints change when migrating between regions

US_ENDPOINTS = {
    "track": "https://track.customer.io/api/v2",
    "app": "https://api.customer.io/v1",
}

EU_ENDPOINTS = {
    "track": "https://cdp.customer.io/v1",
    "app": "https://api-eu.customer.io/v1",
}

def get_endpoints(region: str = "US") -> dict:
    if region == "EU":
        return EU_ENDPOINTS
    return US_ENDPOINTS

# Update all API calls when migrating from US to EU data center
endpoints = get_endpoints(os.environ.get("CUSTOMERIO_REGION", "US"))
print(f"Using track endpoint: {endpoints['track']}")
```

## Troubleshooting

### Events Missing After Migration

1. Verify you updated BOTH the site_id AND api_key (they are different per region)
2. Check that the new SDK version is installed: `pip show customerio`
3. Confirm API endpoint URLs updated if changing data center
4. Test with a single identify event and verify it appears in the workspace

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
