"""
Abstract interface for Cascade object storage.
"""

from abc import ABC, abstractmethod
from typing import Optional


class CascadeInterface(ABC):
    """Abstract interface for Cascade storage operations."""

    @abstractmethod
    async def upload_blob(
        self,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload a blob to Cascade.

        Args:
            data: Binary data to upload
            content_type: MIME type
            metadata: Optional metadata

        Returns:
            Cascade URI (e.g., cascade://sha256:<hash>)
        """
        pass

    @abstractmethod
    async def download_blob(self, uri: str) -> bytes:
        """
        Download a blob from Cascade by URI.

        Args:
            uri: Cascade URI

        Returns:
            Binary data
        """
        pass

    @abstractmethod
    async def delete_blob(self, uri: str) -> bool:
        """
        Delete a blob from Cascade.

        Args:
            uri: Cascade URI

        Returns:
            True if deleted, False if not found
        """
        pass
