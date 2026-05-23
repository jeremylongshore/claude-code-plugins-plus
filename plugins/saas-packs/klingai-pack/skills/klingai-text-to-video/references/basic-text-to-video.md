# Basic Text-To-Video

## Basic Text-to-Video

```python
import os
import requests
import time

def text_to_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    model: str = "kling-v1.5"
) -> dict:
    """Generate video from text prompt."""

    headers = {
        "Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}",
        "Content-Type": "application/json"
    }

    # Submit generation request
    response = requests.post(
        "https://api.klingai.com/v1/videos/text2video",
        headers=headers,
        json={
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }
    )
    response.raise_for_status()
    job_id = response.json()["job_id"]

    # Wait for completion
    while True:
        status_response = requests.get(
            f"https://api.klingai.com/v1/videos/{job_id}",
            headers=headers
        )
        result = status_response.json()

        if result["status"] == "completed":
            return result
        elif result["status"] == "failed":
            raise Exception(f"Generation failed: {result.get('error')}")

        time.sleep(5)

# Usage
result = text_to_video(
    prompt="A majestic eagle soaring over snow-capped mountains at golden hour",
    duration=10,
    aspect_ratio="16:9"
)
print(f"Video URL: {result['video_url']}")
```
