# Aws S3 Integration

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
