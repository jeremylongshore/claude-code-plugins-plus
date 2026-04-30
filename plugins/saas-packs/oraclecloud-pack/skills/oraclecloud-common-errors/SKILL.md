---
name: oraclecloud-common-errors
description: 'Diagnose and fix Oracle Cloud Infrastructure API errors with real error
  codes and proven fixes.

  Use when encountering OCI ServiceError exceptions, auth failures, SSL issues, or
  timeout errors.

  Trigger with "oci error", "fix oraclecloud", "debug oci", "NotAuthorizedOrNotFound",
  "oci 401".

  '
allowed-tools: Read, Grep, Bash(oci:*), Bash(pip:*), Bash(openssl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Common Errors

## Overview

OCI API errors are notoriously cryptic. `NotAuthorizedOrNotFound` (404) could mean an IAM policy is missing **or** you typed the OCID wrong — the error is intentionally ambiguous for security. `NotAuthenticated` (401) covers six different config file problems. `CERTIFICATE_VERIFY_FAILED` has different fixes depending on your SDK language, OS, and whether you are behind a corporate proxy.

**Purpose:** A diagnostic decoder ring mapping every common OCI error to its real root cause and fix, with runnable diagnostic commands for each scenario.

## Prerequisites

- An OCI account with `~/.oci/config` configured (see `oraclecloud-install-auth`)
- **Python 3.8+** with `pip install oci` installed
- **OCI CLI** installed (`pip install oci-cli`) for diagnostic commands

## Instructions

### Authentication Errors (401 NotAuthenticated)

The 401 error has six distinct root causes. Run this diagnostic to isolate which one:

```python
import oci
import os

def diagnose_auth():
    """Diagnose OCI 401 NotAuthenticated errors."""
    config_path = os.path.expanduser("~/.oci/config")

    # Check 1: Config file exists
    if not os.path.exists(config_path):
        return "CAUSE: Config file missing. Run: oci setup config"

    config = oci.config.from_file(config_path)

    # Check 2: All required fields present
    required = ["user", "fingerprint", "tenancy", "region", "key_file"]
    for field in required:
        if field not in config or not config[field]:
            return f"CAUSE: Missing field '{field}' in ~/.oci/config"

    # Check 3: Key file exists
    key_path = os.path.expanduser(config["key_file"])
    if not os.path.exists(key_path):
        return f"CAUSE: Key file not found: {key_path}"

    # Check 4: Key is private (not public)
    with open(key_path, "r") as f:
        first_line = f.readline().strip()
    if "PUBLIC" in first_line:
        return "CAUSE: key_file points to PUBLIC key. Use the private key (no _public suffix)"

    # Check 5: Key file permissions
    perms = oct(os.stat(key_path).st_mode)[-3:]
    if perms != "600":
        return f"CAUSE: Key permissions are {perms}. Run: chmod 600 {key_path}"

    # Check 6: Fingerprint matches
    return "Config looks valid. Fingerprint mismatch? Verify in Console > User Settings > API Keys"

print(diagnose_auth())
```

**401 Root Cause Table:**

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `did not find a proper configuration for user` | Missing or malformed `~/.oci/config` | Recreate with `oci setup config` |
| `could not find private key` | `key_file` path wrong or file missing | Check path; key must exist at that location |
| `private key does not match` | Fingerprint in config does not match uploaded public key | Upload correct public key or regenerate pair |
| `key_file points to public key` | `key_file=~/.oci/oci_api_key_public.pem` | Change to `key_file=~/.oci/oci_api_key.pem` (private key) |
| `permission denied reading key` | Key file permissions too open | `chmod 600 ~/.oci/oci_api_key.pem` |
| `InvalidKeyId` | User OCID or tenancy OCID wrong | Verify OCIDs in Console > Profile > User Settings |

### Authorization Errors (404 NotAuthorizedOrNotFound)

This is the most confusing OCI error. A 404 means **either** the resource does not exist **or** you lack IAM permission to see it. OCI hides the distinction intentionally.

**Diagnostic steps:**

```bash
# Step 1: Verify the OCID format is correct
echo "ocid1.instance.oc1.iad.aaaa..." | grep -P '^ocid1\.\w+\.oc1\.'

# Step 2: Verify you can list resources in the compartment
oci compute instance list --compartment-id <COMPARTMENT_OCID> --limit 1

# Step 3: Check IAM policies affecting your user
oci iam policy list --compartment-id <TENANCY_OCID> --all \
  --query "data[?contains(statements[0], 'instances')]"
```

**Common IAM policy fixes:**

```
# Allow a group to manage compute in a compartment
allow group Developers to manage instances in compartment MyCompartment

# Allow a group to read all resources (useful for debugging)
allow group Developers to read all-resources in tenancy
```

### SSL Certificate Errors (CERTIFICATE_VERIFY_FAILED)

```python
# Diagnostic: check which CA bundle Python uses
import ssl
print(ssl.get_default_verify_paths())

# Fix 1: Install/update certifi
# pip install --upgrade certifi

# Fix 2: Point to system CA bundle (Linux)
import os
os.environ["REQUESTS_CA_BUNDLE"] = "/etc/ssl/certs/ca-certificates.crt"

# Fix 3: Corporate proxy — add proxy CA to certifi bundle
# cat proxy-ca.pem >> $(python -c "import certifi; print(certifi.where())")
```

**SSL Fix by Environment:**

| Environment | Fix |
|------------|-----|
| Linux (system Python) | `pip install --upgrade certifi` |
| macOS | `brew install ca-certificates` + update certifi |
| Corporate proxy | Add proxy CA cert to certifi bundle |
| Docker container | Copy CA bundle: `COPY ca-bundle.crt /etc/ssl/certs/` |
| Air-gapped | Set `REQUESTS_CA_BUNDLE` to local CA file |

### Rate Limit Errors (429 TooManyRequests)

OCI does **not** send a `Retry-After` header. You must implement your own backoff:

```python
import oci
import time
import random

def handle_rate_limit(fn, max_retries=5):
    """Handle OCI 429 errors. No Retry-After header — use jittered backoff."""
    for attempt in range(max_retries):
        try:
            return fn()
        except oci.exceptions.ServiceError as e:
            if e.status == 429:
                delay = (2 ** attempt) + random.uniform(0, 2)
                print(f"Rate limited. Waiting {delay:.1f}s (attempt {attempt + 1})")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError("Rate limit retries exhausted")

# Or use the built-in strategy
compute = oci.core.ComputeClient(
    config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
)
```

### Timeout Errors (ServiceError status -1)

A `ServiceError` with `status == -1` means the SDK timed out before the server responded:

```python
import oci

config = oci.config.from_file("~/.oci/config")

# Default has NO connection timeout. Always set both:
compute = oci.core.ComputeClient(
    config,
    timeout=(10, 60)  # (connect_timeout, read_timeout)
)

# Object Storage uploads need longer read timeout
object_storage = oci.object_storage.ObjectStorageClient(
    config,
    timeout=(10, 600)  # 10 min for large uploads
)
```

### Internal Server Errors (500 InternalError)

```python
import oci

# Check OCI service health first
# https://ocistatus.oraclecloud.com

# 500 errors are transient — use retry strategy
compute = oci.core.ComputeClient(
    oci.config.from_file("~/.oci/config"),
    retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY  # Retries 500, 502, 503, 504
)
```

## Output

After working through this diagnostic guide you will have:
- Identified the exact root cause of your OCI error from the error code and message
- A runnable diagnostic script for 401 auth errors that checks all six failure modes
- IAM policy statements to resolve 404 authorization errors
- Correct timeout and retry configuration for 429 and 500 errors
- SSL certificate fixes for your specific environment

## Error Handling

**Complete OCI Error Reference Table:**

| Error | Status | Exception | Root Cause | Fix |
|-------|--------|-----------|-----------|-----|
| NotAuthenticated | 401 | `ServiceError` | Wrong config, key, or fingerprint | Run `diagnose_auth()` above |
| NotAuthorizedOrNotFound | 404 | `ServiceError` | Missing IAM policy OR wrong OCID | Check OCID format, then IAM policies |
| TooManyRequests | 429 | `ServiceError` | Rate limit exceeded | Backoff with jitter (no Retry-After header) |
| InternalError | 500 | `ServiceError` | OCI service error | Retry; check https://ocistatus.oraclecloud.com |
| Timeout | -1 | `ServiceError` | No response in time | Set `timeout=(connect, read)` on client |
| CERTIFICATE_VERIFY_FAILED | — | `SSLError` | CA bundle outdated or proxy | Update certifi or set REQUESTS_CA_BUNDLE |
| InvalidParameter | 400 | `ServiceError` | Malformed request body | Check OCID format and required fields |
| Out of host capacity | 500 | `ServiceError` | No hosts available (ARM shapes) | Retry loop; see `oraclecloud-hello-world` |

## Examples

**One-command connectivity test:**

```bash
# Tests auth + network + SSL in one call
oci iam region list --output table 2>&1 || echo "FAILED — run oraclecloud-common-errors diagnostic"
```

**Catch-all error handler for scripts:**

```python
import oci
import sys

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)

try:
    compute.list_instances(compartment_id=config["tenancy"])
    print("OK")
except oci.exceptions.ServiceError as e:
    print(f"OCI Error: {e.status} {e.code}")
    print(f"Message: {e.message}")
    print(f"Request ID: {e.request_id}")  # Include this in support tickets
    if e.status == 401:
        print("ACTION: Check ~/.oci/config — see oraclecloud-install-auth")
    elif e.status == 404:
        print("ACTION: Verify OCID and IAM policies — see 404 section above")
    elif e.status == 429:
        print("ACTION: Rate limited — implement backoff")
    elif e.status == -1:
        print("ACTION: Timeout — increase client timeout values")
    sys.exit(1)
except oci.exceptions.ConfigFileNotFoundError:
    print("ACTION: ~/.oci/config not found. Run: oci setup config")
    sys.exit(1)
```

## Resources

- [OCI SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — official error resolution guide
- [OCI Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — active bugs and workarounds
- [OCI Status Page](https://ocistatus.oraclecloud.com) — real-time service health dashboard
- [OCI API Reference](https://docs.oracle.com/en-us/iaas/api/) — error response schemas per service
- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — exception class hierarchy
- [OCI IAM Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm) — policy syntax for 404 fixes

## Next Steps

Once errors are resolved, see `oraclecloud-sdk-patterns` for retry and timeout patterns to prevent errors proactively, or `oraclecloud-local-dev-loop` for a productive development workflow with fast feedback.
