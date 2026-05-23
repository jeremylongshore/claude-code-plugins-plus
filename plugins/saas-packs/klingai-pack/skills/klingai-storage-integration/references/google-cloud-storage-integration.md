# Google Cloud Storage Integration

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
