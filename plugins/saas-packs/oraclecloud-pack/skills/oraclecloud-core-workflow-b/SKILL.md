---
name: oraclecloud-core-workflow-b
description: |
  Execute Oracle Cloud secondary workflow: Object Storage Management.
  Trigger: "oraclecloud object storage management", "secondary oraclecloud workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud — Object Storage Management

## Overview
Secondary workflow complementing the primary workflow.

## Instructions

### Step 1: Create Bucket
```python
import oci

config = oci.config.from_file()
storage = oci.object_storage.ObjectStorageClient(config)
namespace = storage.get_namespace().data

bucket = storage.create_bucket(
    namespace_name=namespace,
    create_bucket_details=oci.object_storage.models.CreateBucketDetails(
        compartment_id=config['tenancy'],
        name='my-data-bucket',
        storage_tier='Standard',
        public_access_type='NoPublicAccess'
    )
)
print(f"Bucket created: {bucket.data.name}")
```

### Step 2: Upload Object
```python
with open('data.csv', 'rb') as f:
    storage.put_object(
        namespace_name=namespace,
        bucket_name='my-data-bucket',
        object_name='datasets/data.csv',
        put_object_body=f,
        content_type='text/csv'
    )
```

### Step 3: List and Download Objects
```python
objects = storage.list_objects(namespace, 'my-data-bucket', prefix='datasets/')
for obj in objects.data.objects:
    print(f"{obj.name} | {obj.size} bytes | {obj.time_modified}")

# Download
response = storage.get_object(namespace, 'my-data-bucket', 'datasets/data.csv')
with open('downloaded.csv', 'wb') as f:
    f.write(response.data.content)
```

### Step 4: Pre-Authenticated Request (Signed URL)
```python
par = storage.create_preauthenticated_request(
    namespace_name=namespace,
    bucket_name='my-data-bucket',
    create_preauthenticated_request_details=oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name='temp-access',
        access_type='ObjectRead',
        object_name='datasets/data.csv',
        time_expires=datetime.utcnow() + timedelta(hours=1)
    )
)
print(f"Signed URL: https://objectstorage.{config['region']}.oraclecloud.com{par.data.access_uri}")
```

## Resources
- [Oracle Cloud Docs](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-common-errors`.
