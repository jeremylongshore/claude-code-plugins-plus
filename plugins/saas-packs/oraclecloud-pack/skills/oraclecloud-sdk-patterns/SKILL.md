---
name: oraclecloud-sdk-patterns
description: 'Production-grade OCI SDK patterns for client lifecycle, retry logic,
  and memory leak avoidance.

  Use when building long-running OCI services, fixing memory leaks with Instance Principal
  auth, or implementing retry/backoff.

  Trigger with "oci sdk patterns", "oci retry", "oci memory leak", "oraclecloud client
  lifecycle".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud SDK Patterns

## Overview

Production patterns for the OCI Python SDK that avoid the most common pitfalls: memory leaks from Instance Principal authentication (~10 MiB/hour if clients are recreated per request), missing retry logic for 429/500 errors, and timeout misconfiguration across different service clients. The OCI SDK has different timeout defaults depending on the service (Compute: 60s, Object Storage: 300s for uploads), and none of them set connection timeouts by default.

**Purpose:** Provide correct client lifecycle (create once, reuse, close), exponential backoff retry, singleton patterns that prevent the Instance Principal memory leak, and per-service timeout configuration.

## Prerequisites

- **Completed `oraclecloud-install-auth`** — valid `~/.oci/config`
- **Python 3.8+** with `pip install oci`
- Familiarity with OCI service clients (`ComputeClient`, `ObjectStorageClient`, etc.)

## Instructions

### Step 1: Singleton Client Pattern (Avoids Memory Leak)

Instance Principal authentication allocates new security tokens on each client instantiation. Creating clients per-request leaks ~10 MiB/hour. Use a singleton:

```python
import oci
import threading

class OCIClients:
    """Thread-safe singleton for OCI service clients.

    Prevents the Instance Principal memory leak by reusing clients
    instead of creating new ones per request.
    """
    _lock = threading.Lock()
    _instance = None

    def __init__(self):
        self._config = oci.config.from_file("~/.oci/config")
        oci.config.validate_config(self._config)

        # Create clients once — reuse everywhere
        self._compute = None
        self._network = None
        self._object_storage = None
        self._identity = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @property
    def config(self):
        return self._config

    @property
    def compute(self):
        if self._compute is None:
            self._compute = oci.core.ComputeClient(
                self._config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
            )
        return self._compute

    @property
    def network(self):
        if self._network is None:
            self._network = oci.core.VirtualNetworkClient(
                self._config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
            )
        return self._network

    @property
    def object_storage(self):
        if self._object_storage is None:
            self._object_storage = oci.object_storage.ObjectStorageClient(
                self._config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
            )
        return self._object_storage

    @property
    def identity(self):
        if self._identity is None:
            self._identity = oci.identity.IdentityClient(
                self._config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
            )
        return self._identity


# Usage: never create clients directly
clients = OCIClients.get()
instances = clients.compute.list_instances(
    compartment_id=clients.config["tenancy"]
)
```

### Step 2: Timeout Configuration

OCI SDK has no connection timeout by default. Set both connection and read timeouts explicitly:

```python
import oci

config = oci.config.from_file("~/.oci/config")

# Compute: 10s connect, 60s read
compute = oci.core.ComputeClient(
    config,
    timeout=(10, 60)  # (connect_timeout, read_timeout) in seconds
)

# Object Storage: 10s connect, 300s read (large uploads)
object_storage = oci.object_storage.ObjectStorageClient(
    config,
    timeout=(10, 300)
)

# Database: 10s connect, 120s read (long queries)
database = oci.database.DatabaseClient(
    config,
    timeout=(10, 120)
)
```

### Step 3: Exponential Backoff Retry Strategy

The built-in `DEFAULT_RETRY_STRATEGY` retries on 429, 500, 502, 503, 504. For custom control:

```python
import oci

custom_retry = oci.retry.RetryStrategyBuilder(
    max_attempts_check=True,
    max_attempts=5,
    total_elapsed_time_check=True,
    total_elapsed_time_seconds=300,
    retry_max_wait_between_calls_seconds=30,
    retry_base_sleep_time_seconds=2,
    service_error_check=True,
    service_error_retry_on_any_5xx=True,
    service_error_retry_config={
        429: []  # Retry on all 429 errors (no Retry-After header in OCI)
    },
    backoff_type=oci.retry.BACKOFF_DECORRELATED_JITTER
).get_retry_strategy()

compute = oci.core.ComputeClient(config, retry_strategy=custom_retry)
```

### Step 4: Manual Retry with Error Classification

For fine-grained control over which errors to retry:

```python
import time
import random
import oci

def call_with_retry(fn, max_retries=5, base_delay=2):
    """Execute an OCI SDK call with exponential backoff.

    Retries on: 429 TooManyRequests, 500 InternalError, -1 timeout.
    Raises immediately on: 401, 404, 400.
    """
    for attempt in range(max_retries):
        try:
            return fn()
        except oci.exceptions.ServiceError as e:
            if e.status in (429, 500, 502, 503, 504) or e.status == -1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Attempt {attempt + 1} failed ({e.status}). Retry in {delay:.1f}s")
                time.sleep(delay)
            else:
                raise  # 401, 404, 400 — don't retry
    raise RuntimeError(f"Failed after {max_retries} retries")

# Usage
config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)

instances = call_with_retry(
    lambda: compute.list_instances(compartment_id=config["tenancy"])
)
```

### Step 5: Pagination Helper

OCI API responses are paginated. Use the built-in paginator instead of manual `opc-next-page` handling:

```python
import oci

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)

# Automatic pagination — returns ALL instances
all_instances = oci.pagination.list_call_get_all_results(
    compute.list_instances,
    compartment_id=config["tenancy"]
).data

print(f"Total instances: {len(all_instances)}")

# Lazy pagination — yields pages (memory-efficient for large datasets)
for page in oci.pagination.list_call_get_all_results_generator(
    compute.list_instances,
    "response",
    compartment_id=config["tenancy"]
):
    for inst in page.data:
        print(f"{inst.display_name}: {inst.lifecycle_state}")
```

### Step 6: Composite Operations (Wait for State)

Use composite clients to launch-and-wait in one call:

```python
import oci

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)
compute_composite = oci.core.ComputeClientCompositeOperations(compute)

# Launch and wait for RUNNING state
launch_details = oci.core.models.LaunchInstanceDetails(
    compartment_id=config["tenancy"],
    availability_domain="Uocm:US-ASHBURN-AD-1",
    display_name="sdk-pattern-demo",
    shape="VM.Standard.E4.Flex",
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
        ocpus=1, memory_in_gbs=8
    ),
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        image_id="ocid1.image.oc1.iad.aaaa..."
    ),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id="ocid1.subnet.oc1.iad.aaaa..."
    )
)

response = compute_composite.launch_instance_and_wait_for_state(
    launch_details,
    wait_for_states=[
        oci.core.models.Instance.LIFECYCLE_STATE_RUNNING
    ]
)
print(f"Instance running: {response.data.id}")
```

## Output

After applying these patterns you have:
- A thread-safe singleton client that avoids the Instance Principal memory leak
- Explicit timeout configuration for each service client (connect + read)
- Exponential backoff retry handling 429, 500, and timeout errors
- Automatic pagination for listing large resource sets
- Composite operations that wait for resource state transitions

## Error Handling

| Error | Code | Retry? | Notes |
|-------|------|--------|-------|
| TooManyRequests | 429 | Yes | OCI does not send Retry-After; use decorrelated jitter |
| InternalError | 500 | Yes | Transient OCI service error |
| NotAuthenticated | 401 | No | Config or key issue — fix credentials first |
| NotAuthorizedOrNotFound | 404 | No | IAM policy or wrong OCID |
| ServiceError status -1 | -1 | Yes | Connection timeout — increase timeout tuple |
| CERTIFICATE_VERIFY_FAILED | — | No | SSL issue; see `oraclecloud-common-errors` |

## Examples

**Quick health check with timeout and retry:**

```python
import oci

config = oci.config.from_file("~/.oci/config")
identity = oci.identity.IdentityClient(
    config,
    timeout=(5, 15),
    retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
)
regions = identity.list_regions().data
print(f"Connected. {len(regions)} regions available.")
```

## Resources

- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — full client API and retry configuration
- [OCI SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — timeout and auth debugging
- [OCI API Reference](https://docs.oracle.com/en-us/iaas/api/) — REST API specs for all services
- [OCI Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — SDK bugs and workarounds
- [OCI Pricing](https://www.oracle.com/cloud/pricing/) — service cost reference

## Next Steps

Apply these patterns in `oraclecloud-hello-world` for compute, or see `oraclecloud-common-errors` for the complete error diagnostic reference when retry strategies surface persistent failures.
