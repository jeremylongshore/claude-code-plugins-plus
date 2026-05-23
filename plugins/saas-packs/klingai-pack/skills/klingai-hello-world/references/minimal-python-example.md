# Minimal Python Example

## Minimal Python Example

```python
import os
import time
import requests

KLINGAI_API_KEY = os.environ["KLINGAI_API_KEY"]
BASE_URL = "https://api.klingai.com/v1"

headers = {
    "Authorization": f"Bearer {KLINGAI_API_KEY}",
    "Content-Type": "application/json"
}

# Step 1: Submit video generation request
def create_video(prompt: str) -> str:
    """Submit a video generation job and return the job ID."""
    response = requests.post(
        f"{BASE_URL}/videos/text2video",
        headers=headers,
        json={
            "prompt": prompt,
            "duration": 5,  # 5 seconds
            "aspect_ratio": "16:9"
        }
    )
    response.raise_for_status()
    return response.json()["job_id"]

# Step 2: Poll for completion
def wait_for_video(job_id: str, timeout: int = 300) -> dict:
    """Wait for video generation to complete."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(
            f"{BASE_URL}/videos/{job_id}",
            headers=headers
        )
        response.raise_for_status()
        result = response.json()

        status = result["status"]
        print(f"Status: {status}")

        if status == "completed":
            return result
        elif status == "failed":
            raise Exception(f"Generation failed: {result.get('error')}")

        time.sleep(5)  # Poll every 5 seconds

    raise TimeoutError("Video generation timed out")

# Step 3: Run hello world
def main():
    print("🎬 Kling AI Hello World")
    print("=" * 40)

    prompt = "A golden retriever running through a sunny meadow, cinematic quality"

    print(f"Prompt: {prompt}")
    print("Submitting generation request...")

    job_id = create_video(prompt)
    print(f"Job ID: {job_id}")

    print("Waiting for completion...")
    result = wait_for_video(job_id)

    print("\n✅ Video generated successfully!")
    print(f"Video URL: {result['video_url']}")
    print(f"Duration: {result['duration']}s")
    print(f"Resolution: {result['resolution']}")

if __name__ == "__main__":
    main()
```
