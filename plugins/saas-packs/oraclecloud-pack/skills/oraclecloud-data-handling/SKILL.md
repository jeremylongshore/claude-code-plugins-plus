---
name: oraclecloud-data-handling
description: "Manage OCI Object Storage \u2014 buckets, uploads, PARs, and lifecycle\
  \ policies.\nUse when uploading objects, creating pre-authenticated requests, or\
  \ configuring lifecycle rules.\nTrigger with \"oci object storage\", \"oci bucket\"\
  , \"par url\", \"multipart upload\", \"oci lifecycle\".\n"
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
# OCI Object Storage — Buckets, PARs & Lifecycle

## Overview

Manage OCI Object Storage using the Python SDK. Object Storage is OCI's S3 equivalent, but PAR (Pre-Authenticated Request) URLs expire silently with no error — the URL just returns 404. Multipart uploads over 50GB require manual part management. Lifecycle policies can delete data unexpectedly if misconfigured. This skill covers the safe patterns for all of these operations.

**Purpose:** Upload, download, and share objects safely with proper PAR expiry management and lifecycle policy configuration.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **Config file** at `~/.oci/config` with fields: `user`, `fingerprint`, `tenancy`, `region`, `key_file`
- **IAM policy** — `Allow group Developers to manage objects in compartment <name>`
- **Python 3.8+**

## Instructions

### Step 1: Discover Namespace and Create a Bucket

Every OCI tenancy has a unique Object Storage namespace. You must discover it before any operation.

```python
import oci
from datetime import datetime, timedelta

config = oci.config.from_file("~/.oci/config")
storage = oci.object_storage.ObjectStorageClient(config)

# Namespace is tenancy-specific — discover it, never hardcode
namespace = storage.get_namespace().data
print(f"Namespace: {namespace}")

# Create bucket
bucket = storage.create_bucket(
    namespace_name=namespace,
    create_bucket_details=oci.object_storage.models.CreateBucketDetails(
        compartment_id=config["tenancy"],
        name="app-data-bucket",
        storage_tier="Standard",
        public_access_type="NoPublicAccess",
        versioning="Enabled",  # Protect against accidental deletes
    ),
).data
print(f"Bucket created: {bucket.name}")
```

### Step 2: Upload Objects (Simple and Multipart)

Use simple upload for files under 50MB. For larger files, use the UploadManager which handles multipart automatically.

```python
# Simple upload (< 50MB)
with open("report.csv", "rb") as f:
    storage.put_object(
        namespace_name=namespace,
        bucket_name="app-data-bucket",
        object_name="reports/2026/report.csv",
        put_object_body=f,
        content_type="text/csv",
    )
print("Simple upload complete")

# Multipart upload for large files (UploadManager handles chunking)
from oci.object_storage import UploadManager

upload_manager = UploadManager(storage)
response = upload_manager.upload_file(
    namespace_name=namespace,
    bucket_name="app-data-bucket",
    object_name="backups/large-dump.tar.gz",
    file_path="/tmp/large-dump.tar.gz",
    part_size=64 * 1024 * 1024,  # 64MB parts
    allow_multipart_uploads=True,
)
print(f"Multipart upload complete: {response.status}")
```

### Step 3: Download and List Objects

```python
# List objects with prefix
objects = storage.list_objects(
    namespace_name=namespace,
    bucket_name="app-data-bucket",
    prefix="reports/",
).data

for obj in objects.objects:
    print(f"{obj.name} | {obj.size} bytes | {obj.time_modified}")

# Download an object
response = storage.get_object(
    namespace_name=namespace,
    bucket_name="app-data-bucket",
    object_name="reports/2026/report.csv",
)
with open("downloaded-report.csv", "wb") as f:
    for chunk in response.data.raw.stream(1024 * 1024):
        f.write(chunk)
print("Download complete")
```

### Step 4: Create Pre-Authenticated Requests (PARs) Safely

PARs are OCI's signed URLs. **Critical gotcha:** expired PARs return 404 NotFound, not 401 or 403. Callers assume the object was deleted when it is actually just the PAR that expired.

```python
# Create a PAR with explicit expiry
par = storage.create_preauthenticated_request(
    namespace_name=namespace,
    bucket_name="app-data-bucket",
    create_preauthenticated_request_details=oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name="partner-download-2026q1",
        access_type="ObjectRead",
        object_name="reports/2026/report.csv",
        time_expires=datetime.utcnow() + timedelta(hours=24),
    ),
).data

par_url = f"https://objectstorage.{config['region']}.oraclecloud.com{par.access_uri}"
print(f"PAR URL (expires in 24h): {par_url}")
print(f"PAR ID (save for revocation): {par.id}")

# List active PARs to audit expiry
pars = storage.list_preauthenticated_requests(
    namespace_name=namespace,
    bucket_name="app-data-bucket",
).data

for p in pars:
    remaining = p.time_expires - datetime.utcnow()
    print(f"{p.name} | expires: {p.time_expires} | remaining: {remaining}")

# Revoke a PAR before expiry
storage.delete_preauthenticated_request(
    namespace_name=namespace,
    bucket_name="app-data-bucket",
    par_id=par.id,
)
print("PAR revoked")
```

### Step 5: Configure Lifecycle Policies

Lifecycle rules can auto-archive or delete objects. **Warning:** A rule with `time_amount=30` and `action=DELETE` will permanently delete objects after 30 days with no recovery unless versioning is enabled.

```python
storage.put_object_lifecycle_policy(
    namespace_name=namespace,
    bucket_name="app-data-bucket",
    put_object_lifecycle_policy_details=oci.object_storage.models.PutObjectLifecyclePolicyDetails(
        items=[
            oci.object_storage.models.ObjectLifecycleRule(
                name="archive-old-reports",
                action="ARCHIVE",
                time_amount=90,
                time_unit="DAYS",
                is_enabled=True,
                object_name_filter=oci.object_storage.models.ObjectNameFilter(
                    inclusion_prefixes=["reports/"],
                ),
            ),
            oci.object_storage.models.ObjectLifecycleRule(
                name="delete-temp-files",
                action="DELETE",
                time_amount=7,
                time_unit="DAYS",
                is_enabled=True,
                object_name_filter=oci.object_storage.models.ObjectNameFilter(
                    inclusion_prefixes=["tmp/"],
                ),
            ),
        ]
    ),
)
print("Lifecycle policies applied")
```

## Output

Successful completion produces:
- A versioned Object Storage bucket with no public access
- Simple upload for small files and UploadManager for large files (automatic multipart)
- PAR URLs with explicit expiry and audit/revocation workflow
- Lifecycle policies that archive old data and clean up temp files

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Bucket not found | 404 NotAuthorizedOrNotFound | Wrong namespace, bucket name, or IAM | Verify namespace with `get_namespace()`, check IAM policy |
| PAR returns 404 | 404 | PAR expired (not the object) | List PARs to check expiry; create a new PAR |
| Object too large | 400 InvalidParameter | Simple upload > 50MB | Use UploadManager with `allow_multipart_uploads=True` |
| Not authenticated | 401 NotAuthenticated | Bad API key or config | Verify `~/.oci/config` key_file and fingerprint |
| Rate limited | 429 TooManyRequests | Too many API calls | Add backoff; OCI does not return Retry-After header |
| SSL error | N/A CERTIFICATE_VERIFY_FAILED | Corporate proxy or cert issue | Set `SSL_CERT_FILE` env var or configure SDK cert bundle |

## Examples

**Quick bucket list via CLI:**

```bash
oci os bucket list \
  --compartment-id <OCID> \
  --query "data[*].{Name:name,Versioning:versioning}" \
  --output table
```

**Check all active PARs across buckets:**

```python
buckets = storage.list_buckets(
    namespace_name=namespace,
    compartment_id=config["tenancy"],
).data

for b in buckets:
    pars = storage.list_preauthenticated_requests(
        namespace_name=namespace,
        bucket_name=b.name,
    ).data
    if pars:
        print(f"\n{b.name}:")
        for p in pars:
            print(f"  {p.name} | expires: {p.time_expires}")
```

## Resources

- [Object Storage Overview](https://docs.oracle.com/en-us/iaas/Content/) — buckets, objects, and tiers
- [Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — ObjectStorageClient API
- [API Reference](https://docs.oracle.com/en-us/iaas/api/) — REST endpoints for Object Storage
- [CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — `oci os` commands
- [Pricing](https://www.oracle.com/cloud/pricing/) — Object Storage pricing tiers

## Next Steps

After setting up Object Storage, see `oraclecloud-query-transform` to monitor storage metrics via MQL, or `oraclecloud-schema-migration` if you need to export database data into Object Storage buckets.
