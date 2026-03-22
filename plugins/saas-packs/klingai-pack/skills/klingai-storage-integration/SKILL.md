---
name: klingai-storage-integration
description: |
  Download and store Kling AI generated videos in cloud storage (S3, GCS, Azure). Use when
  persisting videos or building CDN pipelines. Trigger with phrases like 'klingai storage',
  'save klingai video', 'kling ai s3 upload', 'klingai cloud storage'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, storage, s3, gcs]

---
# Kling AI Storage Integration

## Overview

Kling AI video URLs from `task_result.videos[].url` are temporary CDN links that expire. You must download and store videos in your own storage. This skill covers S3, GCS, and Azure Blob.

## Download from Kling CDN

```python
import requests
import os

def download_video(video_url: str, output_dir: str = "output") -> str:
    """Download generated video from Kling CDN."""
    os.makedirs(output_dir, exist_ok=True)

    # Extract filename or generate one
    filename = video_url.split("/")[-1].split("?")[0]
    if not filename.endswith(".mp4"):
        filename = f"kling_{int(time.time())}.mp4"

    filepath = os.path.join(output_dir, filename)
    response = requests.get(video_url, stream=True, timeout=120)
    response.raise_for_status()

    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"Downloaded: {filepath} ({size_mb:.1f} MB)")
    return filepath
```

## Upload to AWS S3

```python
import boto3

def upload_to_s3(filepath: str, bucket: str, key_prefix: str = "kling-videos/") -> str:
    """Upload video to S3 and return public URL."""
    s3 = boto3.client("s3")
    filename = os.path.basename(filepath)
    s3_key = f"{key_prefix}{filename}"

    s3.upload_file(
        filepath, bucket, s3_key,
        ExtraArgs={"ContentType": "video/mp4", "CacheControl": "max-age=86400"}
    )

    url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"
    print(f"Uploaded to S3: {url}")
    return url

# Generate signed URL for private buckets
def get_signed_url(bucket: str, key: str, expiry: int = 3600) -> str:
    s3 = boto3.client("s3")
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry,
    )
```

## Upload to Google Cloud Storage

```python
from google.cloud import storage

def upload_to_gcs(filepath: str, bucket_name: str, prefix: str = "kling-videos/") -> str:
    """Upload video to GCS and return public URL."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    filename = os.path.basename(filepath)
    blob = bucket.blob(f"{prefix}{filename}")

    blob.upload_from_filename(filepath, content_type="video/mp4")
    blob.make_public()  # or use signed URLs for private access

    print(f"Uploaded to GCS: {blob.public_url}")
    return blob.public_url

# Signed URL for private access
def get_gcs_signed_url(bucket_name: str, blob_name: str, expiry_min: int = 60) -> str:
    from datetime import timedelta
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(expiration=timedelta(minutes=expiry_min))
```

## Upload to Azure Blob Storage

```python
from azure.storage.blob import BlobServiceClient

def upload_to_azure(filepath: str, container: str,
                    connection_string: str = None) -> str:
    """Upload video to Azure Blob Storage."""
    conn_str = connection_string or os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    client = BlobServiceClient.from_connection_string(conn_str)
    filename = os.path.basename(filepath)
    blob_client = client.get_blob_client(container=container, blob=f"kling-videos/{filename}")

    with open(filepath, "rb") as f:
        blob_client.upload_blob(f, content_type="video/mp4", overwrite=True)

    url = blob_client.url
    print(f"Uploaded to Azure: {url}")
    return url
```

## End-to-End Pipeline

```python
def generate_and_store(prompt: str, bucket: str, provider: str = "s3"):
    """Generate video with Kling AI and store in cloud."""
    # 1. Generate
    r = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
        "model_name": "kling-v2-master",
        "prompt": prompt,
        "duration": "5",
        "mode": "standard",
    }).json()
    task_id = r["data"]["task_id"]

    # 2. Poll
    result = poll_task("/videos/text2video", task_id)
    video_url = result["videos"][0]["url"]

    # 3. Download
    filepath = download_video(video_url)

    # 4. Upload
    if provider == "s3":
        return upload_to_s3(filepath, bucket)
    elif provider == "gcs":
        return upload_to_gcs(filepath, bucket)
    elif provider == "azure":
        return upload_to_azure(filepath, bucket)

    # 5. Cleanup temp file
    os.remove(filepath)
```

## Metadata Preservation

```python
import json

def save_with_metadata(filepath: str, task_id: str, prompt: str, model: str):
    """Save video metadata alongside the file."""
    meta = {
        "task_id": task_id,
        "prompt": prompt,
        "model": model,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "filename": os.path.basename(filepath),
    }
    meta_path = filepath.replace(".mp4", ".meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    return meta_path
```

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [AWS S3 SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Google Cloud Storage](https://cloud.google.com/storage/docs)
