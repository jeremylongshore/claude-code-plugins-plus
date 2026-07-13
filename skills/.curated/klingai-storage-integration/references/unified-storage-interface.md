# Unified Storage Interface

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

    return providersprovider

# Usage - easily switch providers
storage = get_storage("s3", bucket="my-bucket")
# or
storage = get_storage("gcs", bucket="my-bucket")
```
