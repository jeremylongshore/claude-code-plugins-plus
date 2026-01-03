---
name: klingai-storage-integration
description: |
  Integrate Kling AI video output with cloud storage providers. Use when storing generated
  videos in S3, GCS, or Azure Blob. Trigger with phrases like 'klingai storage', 'save klingai video',
  'kling ai cloud storage', 'klingai s3 upload'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Storage Integration

## Overview

This skill demonstrates how to download and store generated videos in cloud storage services including AWS S3, Google Cloud Storage, and Azure Blob Storage.

## Prerequisites

- Kling AI API key configured
- Cloud storage credentials (AWS, GCP, or Azure)
- Python 3.8+ with cloud SDKs installed

## Instructions

Follow these steps to integrate storage:

1. **Configure Storage**: Set up cloud storage credentials
2. **Download Video**: Fetch generated video from Kling AI
3. **Upload to Cloud**: Store in your preferred provider
4. **Generate URLs**: Create access URLs (signed or public)
5. **Clean Up**: Remove temporary files

## AWS S3 Integration

```python
import boto3
import requests
import os
from typing import Optional
from datetime import datetime
import hashlib

class S3VideoStorage:
    """Store Kling AI videos in AWS S3."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "klingai-videos",
        region: str = "us-east-1"
    ):
        self.bucket = bucket
        self.prefix = prefix
        self.s3 = boto3.client("s3", region_name=region)

    def store_video(
        self,
        video_url: str,
        job_id: str,
        metadata: dict = None
    ) -> dict:
        """Download video from Kling AI and upload to S3."""
        # Download video
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        # Generate unique key
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        key = f"{self.prefix}/{timestamp}/{job_id}.mp4"

        # Calculate content hash
        content = response.content
        content_hash = hashlib.md5(content).hexdigest()

        # Prepare metadata
        s3_metadata = {
            "job_id": job_id,
            "source": "klingai",
            "content_hash": content_hash,
        }
        if metadata:
            s3_metadata.update({k: str(v) for k, v in metadata.items()})

        # Upload to S3
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType="video/mp4",
            Metadata=s3_metadata
        )

        return {
            "bucket": self.bucket,
            "key": key,
            "size_bytes": len(content),
            "content_hash": content_hash,
            "s3_uri": f"s3://{self.bucket}/{key}"
        }

    def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed URL for video access."""
        url = self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in
        )
        return url

    def get_public_url(self, key: str) -> str:
        """Get public URL (bucket must allow public access)."""
        return f"https://{self.bucket}.s3.amazonaws.com/{key}"

    def list_videos(self, prefix: str = None) -> list:
        """List stored videos."""
        search_prefix = prefix or self.prefix

        paginator = self.s3.get_paginator("list_objects_v2")
        videos = []

        for page in paginator.paginate(Bucket=self.bucket, Prefix=search_prefix):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".mp4"):
                    videos.append({
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "modified": obj["LastModified"].isoformat()
                    })

        return videos

# Usage
storage = S3VideoStorage(bucket="my-video-bucket")

# Store video after generation
result = storage.store_video(
    video_url="https://klingai-output.com/video.mp4",
    job_id="vid_abc123",
    metadata={"prompt": "sunset over ocean", "model": "kling-v1.5"}
)

print(f"Stored at: {result['s3_uri']}")

# Get download URL
url = storage.get_signed_url(result["key"])
print(f"Download URL: {url}")
```

## Google Cloud Storage Integration

```python
from google.cloud import storage
import requests
from typing import Optional
from datetime import datetime, timedelta

class GCSVideoStorage:
    """Store Kling AI videos in Google Cloud Storage."""

    def __init__(self, bucket: str, prefix: str = "klingai-videos"):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket)
        self.prefix = prefix

    def store_video(
        self,
        video_url: str,
        job_id: str,
        metadata: dict = None
    ) -> dict:
        """Download and upload video to GCS."""
        # Download video
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        # Generate blob name
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        blob_name = f"{self.prefix}/{timestamp}/{job_id}.mp4"

        # Create blob
        blob = self.bucket.blob(blob_name)

        # Set metadata
        blob.metadata = {"job_id": job_id, "source": "klingai"}
        if metadata:
            blob.metadata.update({k: str(v) for k, v in metadata.items()})

        # Upload
        blob.upload_from_string(
            response.content,
            content_type="video/mp4"
        )

        return {
            "bucket": self.bucket.name,
            "blob_name": blob_name,
            "size_bytes": blob.size,
            "gs_uri": f"gs://{self.bucket.name}/{blob_name}"
        }

    def get_signed_url(self, blob_name: str, expires_in: int = 3600) -> str:
        """Generate signed URL for video access."""
        blob = self.bucket.blob(blob_name)
        url = blob.generate_signed_url(
            expiration=timedelta(seconds=expires_in),
            method="GET"
        )
        return url

    def get_public_url(self, blob_name: str) -> str:
        """Get public URL (requires public access)."""
        return f"https://storage.googleapis.com/{self.bucket.name}/{blob_name}"

# Usage
storage = GCSVideoStorage(bucket="my-video-bucket")

result = storage.store_video(
    video_url="https://klingai-output.com/video.mp4",
    job_id="vid_abc123"
)

print(f"Stored at: {result['gs_uri']}")
```

## Azure Blob Storage Integration

```python
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
import requests
from datetime import datetime, timedelta

class AzureBlobVideoStorage:
    """Store Kling AI videos in Azure Blob Storage."""

    def __init__(
        self,
        connection_string: str,
        container: str,
        prefix: str = "klingai-videos"
    ):
        self.blob_service = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service.get_container_client(container)
        self.container = container
        self.prefix = prefix

    def store_video(
        self,
        video_url: str,
        job_id: str,
        metadata: dict = None
    ) -> dict:
        """Download and upload video to Azure Blob."""
        # Download video
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        # Generate blob name
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        blob_name = f"{self.prefix}/{timestamp}/{job_id}.mp4"

        # Get blob client
        blob_client = self.container_client.get_blob_client(blob_name)

        # Prepare metadata
        blob_metadata = {"job_id": job_id, "source": "klingai"}
        if metadata:
            blob_metadata.update({k: str(v) for k, v in metadata.items()})

        # Upload
        blob_client.upload_blob(
            response.content,
            content_type="video/mp4",
            metadata=blob_metadata,
            overwrite=True
        )

        return {
            "container": self.container,
            "blob_name": blob_name,
            "url": blob_client.url
        }

    def get_sas_url(self, blob_name: str, expires_in: int = 3600) -> str:
        """Generate SAS URL for video access."""
        blob_client = self.container_client.get_blob_client(blob_name)

        sas_token = generate_blob_sas(
            account_name=self.blob_service.account_name,
            container_name=self.container,
            blob_name=blob_name,
            account_key=self.blob_service.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(seconds=expires_in)
        )

        return f"{blob_client.url}?{sas_token}"

# Usage
storage = AzureBlobVideoStorage(
    connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"],
    container="videos"
)

result = storage.store_video(
    video_url="https://klingai-output.com/video.mp4",
    job_id="vid_abc123"
)
```

## Unified Storage Interface

```python
from abc import ABC, abstractmethod
from typing import Optional

class VideoStorage(ABC):
    """Abstract interface for video storage."""

    @abstractmethod
    def store_video(self, video_url: str, job_id: str, metadata: dict = None) -> dict:
        pass

    @abstractmethod
    def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        pass

def get_storage(provider: str, **kwargs) -> VideoStorage:
    """Factory function to get storage provider."""
    providers = {
        "s3": S3VideoStorage,
        "gcs": GCSVideoStorage,
        "azure": AzureBlobVideoStorage
    }

    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}")

    return providers[provider](**kwargs)

# Usage - easily switch providers
storage = get_storage("s3", bucket="my-bucket")
# or
storage = get_storage("gcs", bucket="my-bucket")
```

## Output

Successful execution produces:
- Downloaded video from Kling AI
- Uploaded to cloud storage
- Metadata preserved with video
- Signed URLs for secure access

## Error Handling

Common errors and solutions:
1. **Download Failed**: Check Kling AI URL validity and expiration
2. **Upload Permission**: Verify IAM/credentials have write access
3. **URL Expired**: Generate new signed URL

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [AWS S3 SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Google Cloud Storage](https://cloud.google.com/storage/docs)
- [Azure Blob Storage](https://docs.microsoft.com/en-us/azure/storage/blobs/)
