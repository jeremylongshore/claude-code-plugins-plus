---
name: oraclecloud-rate-limits
description: 'Handle OCI API rate limits with defensive retry patterns and known limits
  by service.

  Use when automating bulk OCI operations, hitting 429 TooManyRequests errors, or
  building resilient API clients.

  Trigger with "oraclecloud rate limits", "oci 429 error", "oci throttling", "oci
  backoff".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(oci:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Rate Limits

## Overview

OCI API rate limits vary by service and are not well documented. A `429 TooManyRequests` response kills your automation, and unlike AWS or Azure, OCI does not return a `Retry-After` header. This skill maps known limits by service, implements exponential backoff with jitter, and provides circuit breaker patterns for bulk operations.

**Purpose:** Build resilient OCI API clients that handle throttling gracefully without data loss.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **OCI config file** at `~/.oci/config` with valid credentials (user, fingerprint, tenancy, region, key_file)
- Python 3.8+
- Understanding of which OCI service you are calling (limits vary per service)

## Instructions

### Step 1: Know the Limits

OCI publishes some rate limits, but many are undocumented. Here are the known limits observed in production:

| Service | Endpoint Type | Observed Limit | Notes |
|---------|--------------|----------------|-------|
| Compute | List/Get | ~20 req/sec | Per-tenancy, not per-user |
| Compute | Create/Update/Delete | ~10 req/sec | Stricter for mutating operations |
| Object Storage | List/Get | ~100 req/sec | Per-bucket namespace |
| Object Storage | Put/Delete | ~50 req/sec | Varies by region load |
| Identity | List/Get | ~10 req/sec | Tenancy-wide shared limit |
| Identity | Create/Update | ~5 req/sec | Very conservative |
| Database | All operations | ~10 req/sec | Shared across DB family |
| Networking (VCN) | All operations | ~20 req/sec | Per-compartment |
| Monitoring | Post metrics | ~50 req/sec | Per-metric namespace |
| Events | Rule CRUD | ~10 req/sec | Per-compartment |

**Critical:** These are observed limits, not guaranteed SLAs. OCI may throttle lower under load.

### Step 2: Implement Exponential Backoff with Jitter

OCI returns no `Retry-After` header on 429 responses, so you must implement your own backoff. The SDK's built-in retry handles some cases, but for bulk operations you need explicit control:

```python
import oci
import time
import random

config = oci.config.from_file("~/.oci/config")

def call_with_retry(fn, max_retries=5, base_delay=1.0):
    """Call an OCI SDK function with exponential backoff and jitter.

    OCI returns 429 TooManyRequests with NO Retry-After header,
    so we implement our own backoff strategy.
    """
    for attempt in range(max_retries):
        try:
            return fn()
        except oci.exceptions.ServiceError as e:
            if e.status == 429:
                # Exponential backoff with full jitter
                delay = base_delay * (2 ** attempt)
                jitter = random.uniform(0, delay)
                wait_time = delay + jitter
                print(f"Rate limited (429). Attempt {attempt + 1}/{max_retries}. "
                      f"Waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            elif e.status >= 500:
                # Server errors — retry with backoff
                delay = base_delay * (2 ** attempt)
                print(f"Server error ({e.status}). Retrying in {delay}s")
                time.sleep(delay)
            else:
                raise  # 4xx errors (except 429) are not retryable
    raise Exception(f"Max retries ({max_retries}) exceeded")
```

### Step 3: Use the SDK's Built-in Retry Configuration

The OCI Python SDK supports retry configuration natively. Use this for simple cases:

```python
import oci
from oci.retry import RetryStrategyBuilder

config = oci.config.from_file("~/.oci/config")

# Build a custom retry strategy
retry_strategy = RetryStrategyBuilder(
    max_attempts_check=True,
    max_attempts=5,
    total_elapsed_time_check=True,
    total_elapsed_time_seconds=300,
    retry_max_wait_between_calls_seconds=30,
    retry_base_sleep_time_seconds=1,
    service_error_check=True,
    service_error_retry_on_any_5xx=True,
    service_error_retry_config={429: []},  # Retry on 429 with any message
    backoff_type=oci.retry.BACKOFF_DECORRELATED_JITTER
).get_retry_strategy()

compute = oci.core.ComputeClient(config, retry_strategy=retry_strategy)

# All calls through this client will automatically retry on 429 and 5xx
instances = compute.list_instances(
    compartment_id="ocid1.compartment.oc1..example"
)
```

### Step 4: Implement a Circuit Breaker for Bulk Operations

For operations that process hundreds of resources, a circuit breaker prevents cascading failures:

```python
import oci
import time
import random

class OCICircuitBreaker:
    """Circuit breaker for bulk OCI API operations."""

    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = 0
        self.state = "closed"  # closed = normal, open = blocking

    def call(self, fn, max_retries=3, base_delay=1.0):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "half-open"
                print("Circuit half-open — testing one request")
            else:
                remaining = self.reset_timeout - (time.time() - self.last_failure_time)
                raise Exception(f"Circuit open. Retry in {remaining:.0f}s")

        try:
            result = call_with_retry(fn, max_retries=max_retries, base_delay=base_delay)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                print("Circuit closed — resuming normal operation")
            return result
        except Exception:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                print(f"Circuit OPEN after {self.failure_count} failures. "
                      f"Pausing for {self.reset_timeout}s")
            raise

# Usage for bulk listing
breaker = OCICircuitBreaker(failure_threshold=3, reset_timeout=30)
config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)

compartment_ids = ["ocid1.compartment.oc1..aaa", "ocid1.compartment.oc1..bbb"]
all_instances = []

for cid in compartment_ids:
    result = breaker.call(
        lambda c=cid: compute.list_instances(compartment_id=c)
    )
    all_instances.extend(result.data)
    time.sleep(0.1)  # Courtesy delay between bulk calls
```

### Step 5: Batch Operations with Rate Limiting

For operations that must process many items (e.g., tagging all instances), throttle proactively:

```python
import oci
import time

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)

def batch_with_throttle(items, operation, requests_per_second=5):
    """Process items with proactive rate limiting."""
    delay = 1.0 / requests_per_second
    results = []

    for i, item in enumerate(items):
        result = call_with_retry(lambda it=item: operation(it))
        results.append(result)

        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(items)}")

        time.sleep(delay)

    return results
```

## Output

Successful implementation produces:
- A retry wrapper function that handles 429 responses with exponential backoff and jitter
- SDK-level retry configuration applied to all OCI client calls
- A circuit breaker that prevents cascading failures during bulk operations
- Proactive rate limiting for batch processing scripts

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| TooManyRequests | 429 | API rate limit exceeded (no Retry-After header) | Use exponential backoff with jitter — start at 1s, max 30s |
| NotAuthenticated | 401 | Bad config or expired key | Verify `~/.oci/config` credentials |
| NotAuthorizedOrNotFound | 404 | Missing IAM policy or wrong OCID | Check compartment OCID and IAM policies |
| InternalError | 500 | OCI service error | Retry with backoff; check https://ocistatus.oraclecloud.com |
| ServiceError (status -1) | -1 | Request timeout | Increase SDK timeout or reduce request payload |
| CERTIFICATE_VERIFY_FAILED | — | SSL certificate issue | Update CA certificates: `pip install certifi` |

## Examples

**Quick 429 test — intentionally trigger rate limiting:**

```python
import oci

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)

# Rapid-fire requests to observe throttling behavior
for i in range(100):
    try:
        compute.list_instances(compartment_id="ocid1.compartment.oc1..example")
    except oci.exceptions.ServiceError as e:
        if e.status == 429:
            print(f"Throttled at request {i + 1}")
            break
```

**Check current OCI SDK retry defaults:**

```python
import oci
print(f"SDK version: {oci.__version__}")
# Default retry: NoneRetryStrategy (no retries unless configured)
# Always set explicit retry strategies for production code
```

## Resources

- [OCI API Request Limits](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apiconcepts.htm) — official rate limit documentation
- [Python SDK Retry Configuration](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — RetryStrategyBuilder reference
- [SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — common SDK errors
- [OCI Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — known service issues
- [OCI Status](https://ocistatus.oraclecloud.com) — service health dashboard

## Next Steps

After implementing rate limit handling, see `oraclecloud-security-basics` for IAM policy patterns, or `oraclecloud-observability` for monitoring your API call patterns and error rates.
