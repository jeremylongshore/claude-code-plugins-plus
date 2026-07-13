# Azure Blob Storage Integration

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
