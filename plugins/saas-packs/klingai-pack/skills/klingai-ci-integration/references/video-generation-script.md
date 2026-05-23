# Video Generation Script

## Video Generation Script

```python
#!/usr/bin/env python3
# scripts/generate_video.py

import argparse
import json
import os
import sys
import time
import requests

def generate_video(prompt: str, duration: int, model: str) -> dict:
    """Generate video using Kling AI API."""
    api_key = os.environ["KLINGAI_API_KEY"]
    base_url = "https://api.klingai.com/v1"

    # Submit generation request
    print(f"Submitting video generation request...")
    print(f"  Prompt: {prompt[:50]}...")
    print(f"  Duration: {duration}s")
    print(f"  Model: {model}")

    response = requests.post(
        f"{base_url}/videos/text-to-video",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "prompt": prompt,
            "duration": duration,
            "model": model,
            "aspect_ratio": "16:9"
        }
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)

    job_id = response.json()["job_id"]
    print(f"Job submitted: {job_id}")

    # Poll for completion
    max_wait = 600  # 10 minutes
    poll_interval = 10
    elapsed = 0

    while elapsed < max_wait:
        response = requests.get(
            f"{base_url}/videos/{job_id}",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        data = response.json()
        status = data["status"]

        print(f"Status: {status} ({elapsed}s elapsed)")

        if status == "completed":
            return {
                "job_id": job_id,
                "status": "completed",
                "video_url": data["video_url"],
                "thumbnail_url": data.get("thumbnail_url"),
                "duration": duration,
                "model": model,
                "prompt": prompt
            }
        elif status == "failed":
            print(f"Error: Generation failed - {data.get('error')}")
            sys.exit(1)

        time.sleep(poll_interval)
        elapsed += poll_interval

    print("Error: Timeout waiting for video generation")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate video with Kling AI")
    parser.add_argument("--prompt", required=True, help="Video prompt")
    parser.add_argument("--duration", type=int, default=5, choices=[5, 10])
    parser.add_argument("--model", default="kling-v1.5")
    parser.add_argument("--output-json", help="Output JSON file path")

    args = parser.parse_args()

    result = generate_video(args.prompt, args.duration, args.model)

    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Result written to {args.output_json}")
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```
