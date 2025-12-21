"""
Mock Cascade implementation using filesystem with content-addressed storage.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

from .interface import CascadeInterface


class MockCascadeFS(CascadeInterface):
    """Filesystem-backed mock Cascade with content-addressed storage."""

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize mock Cascade.

        Args:
            storage_dir: Directory for blob storage (default: ~/.lumera/cascade)
        """
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.lumera/cascade")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def upload_blob(
        self,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """Upload blob with content-addressed URI."""
        # Compute SHA-256 hash for content-addressed storage
        sha256_hash = hashlib.sha256(data).hexdigest()

        # Create URI
        uri = f"cascade://sha256:{sha256_hash}"

        # Store blob using hash-based directory structure (first 2 chars as subdir)
        subdir = self.storage_dir / sha256_hash[:2]
        subdir.mkdir(exist_ok=True)

        blob_path = subdir / sha256_hash

        # Write blob if it doesn't exist (deduplication)
        if not blob_path.exists():
            blob_path.write_bytes(data)

        # Store metadata if provided
        if metadata:
            meta_path = subdir / f"{sha256_hash}.meta"
            import json
            meta_path.write_text(json.dumps(metadata))

        return uri

    async def download_blob(self, uri: str) -> bytes:
        """Download blob by content-addressed URI."""
        # Parse URI: cascade://sha256:<hash>
        if not uri.startswith("cascade://sha256:"):
            raise ValueError(f"Invalid Cascade URI format: {uri}")

        sha256_hash = uri.replace("cascade://sha256:", "")

        # Locate blob
        subdir = self.storage_dir / sha256_hash[:2]
        blob_path = subdir / sha256_hash

        if not blob_path.exists():
            raise FileNotFoundError(f"Blob not found: {uri}")

        return blob_path.read_bytes()

    async def delete_blob(self, uri: str) -> bool:
        """Delete blob by URI."""
        if not uri.startswith("cascade://sha256:"):
            raise ValueError(f"Invalid Cascade URI format: {uri}")

        sha256_hash = uri.replace("cascade://sha256:", "")

        subdir = self.storage_dir / sha256_hash[:2]
        blob_path = subdir / sha256_hash
        meta_path = subdir / f"{sha256_hash}.meta"

        deleted = False
        if blob_path.exists():
            blob_path.unlink()
            deleted = True

        if meta_path.exists():
            meta_path.unlink()

        return deleted
