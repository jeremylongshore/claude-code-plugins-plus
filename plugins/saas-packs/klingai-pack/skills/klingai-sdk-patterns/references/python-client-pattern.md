# Python Client Pattern

## Python Client Pattern

```python
import os
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class VideoResult:
    job_id: str
    status: JobStatus
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    error: Optional[str] = None
    duration: Optional[int] = None
    metadata: Optional[Dict] = None

class KlingAIClient:
    """Production-ready Kling AI client."""

    DEFAULT_BASE_URL = "https://api.klingai.com/v1"
    DEFAULT_TIMEOUT = 30
    DEFAULT_POLL_INTERVAL = 5
    DEFAULT_MAX_WAIT = 600

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.environ.get("KLINGAI_API_KEY")
        if not self.api_key:
            raise ValueError("KLINGAI_API_KEY required")

        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout

        # Configure session with retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        model: str = "kling-v1.5",
        aspect_ratio: str = "16:9",
        **kwargs
    ) -> str:
        """Submit text-to-video generation job."""
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            **kwargs
        }
        result = self._request("POST", "/videos/text2video", json=payload)
        return result["job_id"]

    def image_to_video(
        self,
        image_url: str,
        motion_prompt: str,
        duration: int = 5,
        model: str = "kling-v1.5",
        **kwargs
    ) -> str:
        """Submit image-to-video generation job."""
        payload = {
            "model": model,
            "image_url": image_url,
            "motion_prompt": motion_prompt,
            "duration": duration,
            **kwargs
        }
        result = self._request("POST", "/videos/image2video", json=payload)
        return result["job_id"]

    def get_job_status(self, job_id: str) -> VideoResult:
        """Get current status of a generation job."""
        result = self._request("GET", f"/videos/{job_id}")
        return VideoResult(
            job_id=job_id,
            status=JobStatus(result["status"]),
            video_url=result.get("video_url"),
            thumbnail_url=result.get("thumbnail_url"),
            error=result.get("error"),
            duration=result.get("duration"),
            metadata=result
        )

    def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        max_wait: int = DEFAULT_MAX_WAIT,
        callback: Optional[callable] = None
    ) -> VideoResult:
        """Wait for job completion with polling."""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            result = self.get_job_status(job_id)

            if callback:
                callback(result)

            if result.status == JobStatus.COMPLETED:
                return result
            elif result.status == JobStatus.FAILED:
                raise Exception(f"Generation failed: {result.error}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Job {job_id} timed out after {max_wait}s")

    def generate_video(
        self,
        prompt: str,
        wait: bool = True,
        **kwargs
    ) -> VideoResult:
        """High-level method: generate video and optionally wait."""
        job_id = self.text_to_video(prompt, **kwargs)

        if wait:
            return self.wait_for_completion(job_id)

        return VideoResult(job_id=job_id, status=JobStatus.PENDING)

# Usage
client = KlingAIClient()
result = client.generate_video(
    prompt="A cat playing piano in a jazz club",
    duration=10,
    model="kling-v1.5"
)
print(f"Video URL: {result.video_url}")
```
