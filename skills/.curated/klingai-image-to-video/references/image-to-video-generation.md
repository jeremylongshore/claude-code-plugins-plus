# Image-To-Video Generation

## Image-to-Video Generation

```python
import requests
import base64
import os
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class ImageToVideoParams:
    image_path: str
    prompt: str
    duration: int = 5  # 5 or 10 seconds
    model: str = "kling-v1.5"
    motion_strength: float = 0.5  # 0.0 to 1.0
    camera_motion: Optional[str] = None  # zoom_in, zoom_out, pan_left, pan_right
    seed: Optional[int] = None

class KlingAIImageToVideo:
    """Generate videos from static images."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ["KLINGAI_API_KEY"]
        self.base_url = "https://api.klingai.com/v1"

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def get_image_type(self, image_path: str) -> str:
        """Get MIME type for image."""
        suffix = Path(image_path).suffix.lower()
        types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp"
        }
        return types.get(suffix, "image/jpeg")

    def validate_image(self, image_path: str) -> Dict:
        """Validate image for API requirements."""
        from PIL import Image

        path = Path(image_path)

        if not path.exists():
            return {"valid": False, "error": "Image file not found"}

        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 10:
            return {"valid": False, "error": f"Image too large: {size_mb:.1f}MB (max 10MB)"}

        # Check format
        if path.suffix.lower() not in [".png", ".jpg", ".jpeg", ".webp"]:
            return {"valid": False, "error": f"Unsupported format: {path.suffix}"}

        # Check dimensions
        with Image.open(image_path) as img:
            width, height = img.size
            aspect = width / height

            # Check minimum dimensions
            if width < 512 or height < 512:
                return {"valid": False, "error": f"Image too small: {width}x{height} (min 512x512)"}

            return {
                "valid": True,
                "width": width,
                "height": height,
                "aspect_ratio": round(aspect, 2),
                "size_mb": round(size_mb, 2),
                "format": path.suffix.lower()
            }

    def generate(self, params: ImageToVideoParams) -> Dict:
        """Generate video from image."""
        # Validate image first
        validation = self.validate_image(params.image_path)
        if not validation["valid"]:
            raise ValueError(validation["error"])

        # Encode image
        image_data = self.encode_image(params.image_path)
        image_type = self.get_image_type(params.image_path)

        # Build request
        request_body = {
            "image": f"data:{image_type};base64,{image_data}",
            "prompt": params.prompt,
            "duration": params.duration,
            "model": params.model,
            "motion_strength": params.motion_strength,
        }

        if params.camera_motion:
            request_body["camera_motion"] = params.camera_motion

        if params.seed:
            request_body["seed"] = params.seed

        # Submit request
        response = requests.post(
            f"{self.base_url}/videos/image-to-video",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=request_body
        )
        response.raise_for_status()

        return response.json()

    def generate_with_poll(self, params: ImageToVideoParams, timeout: int = 600) -> Dict:
        """Generate video and wait for completion."""
        import time

        # Submit job
        result = self.generate(params)
        job_id = result["job_id"]
        print(f"Job submitted: {job_id}")

        # Poll for completion
        start = time.time()
        while time.time() - start < timeout:
            status_response = requests.get(
                f"{self.base_url}/videos/{job_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            status_data = status_response.json()

            if status_data["status"] == "completed":
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "video_url": status_data["video_url"],
                    "thumbnail_url": status_data.get("thumbnail_url")
                }
            elif status_data["status"] == "failed":
                raise Exception(f"Generation failed: {status_data.get('error')}")

            print(f"Status: {status_data['status']}")
            time.sleep(5)

        raise TimeoutError("Video generation timed out")

# Usage
client = KlingAIImageToVideo()

# Validate image
validation = client.validate_image("my_image.png")
print(f"Image valid: {validation['valid']}")

# Generate video
params = ImageToVideoParams(
    image_path="my_image.png",
    prompt="The scene comes alive with gentle movement, leaves rustling in the wind",
    duration=5,
    motion_strength=0.6,
    camera_motion="zoom_in"
)

result = client.generate_with_poll(params)
print(f"Video URL: {result['video_url']}")
```
