---
name: klingai-hello-world
description: |
  Create your first Kling AI video generation with a simple example. Use when learning Kling AI
  or testing your setup. Trigger with phrases like 'kling ai hello world', 'first kling ai video',
  'klingai quickstart', 'test klingai'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Hello World

## Overview

This skill provides a minimal working example to generate your first AI video with Kling AI, verify your integration is functioning, and understand the basic request/response pattern.

## Prerequisites

- Kling AI API key configured
- Python 3.8+ or Node.js 18+
- HTTP client library installed

## Instructions

Follow these steps to create your first video:

1. **Verify Authentication**: Ensure your API key is configured
2. **Submit Generation Request**: Send a text-to-video request
3. **Poll for Status**: Check job status until complete
4. **Download Result**: Retrieve the generated video URL
5. **Verify Output**: Preview or download the video

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

## Minimal TypeScript Example

```typescript
import axios from 'axios';

const KLINGAI_API_KEY = process.env.KLINGAI_API_KEY!;
const BASE_URL = 'https://api.klingai.com/v1';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Authorization': `Bearer ${KLINGAI_API_KEY}`,
    'Content-Type': 'application/json'
  }
});

async function createVideo(prompt: string): Promise<string> {
  const response = await client.post('/videos/text2video', {
    prompt,
    duration: 5,
    aspect_ratio: '16:9'
  });
  return response.data.job_id;
}

async function waitForVideo(jobId: string, timeout = 300000): Promise<any> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const response = await client.get(`/videos/${jobId}`);
    const { status, video_url, error } = response.data;

    console.log(`Status: ${status}`);

    if (status === 'completed') {
      return response.data;
    } else if (status === 'failed') {
      throw new Error(`Generation failed: ${error}`);
    }

    await new Promise(r => setTimeout(r, 5000));
  }

  throw new Error('Video generation timed out');
}

async function main() {
  console.log('🎬 Kling AI Hello World');
  console.log('='.repeat(40));

  const prompt = 'A golden retriever running through a sunny meadow, cinematic quality';

  console.log(`Prompt: ${prompt}`);
  console.log('Submitting generation request...');

  const jobId = await createVideo(prompt);
  console.log(`Job ID: ${jobId}`);

  console.log('Waiting for completion...');
  const result = await waitForVideo(jobId);

  console.log('\n✅ Video generated successfully!');
  console.log(`Video URL: ${result.video_url}`);
}

main().catch(console.error);
```

## cURL Example

```bash
# Step 1: Submit request
JOB_ID=$(curl -s -X POST https://api.klingai.com/v1/videos/text2video \
  -H "Authorization: Bearer $KLINGAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A golden retriever running through a sunny meadow",
    "duration": 5,
    "aspect_ratio": "16:9"
  }' | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Step 2: Poll for status
while true; do
  STATUS=$(curl -s https://api.klingai.com/v1/videos/$JOB_ID \
    -H "Authorization: Bearer $KLINGAI_API_KEY" | jq -r '.status')

  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ]; then
    curl -s https://api.klingai.com/v1/videos/$JOB_ID \
      -H "Authorization: Bearer $KLINGAI_API_KEY" | jq '.video_url'
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Generation failed!"
    break
  fi

  sleep 5
done
```

## Understanding the Response

```json
{
  "job_id": "job_abc123",
  "status": "completed",
  "prompt": "A golden retriever running through a sunny meadow",
  "video_url": "https://cdn.klingai.com/videos/abc123.mp4",
  "thumbnail_url": "https://cdn.klingai.com/thumbnails/abc123.jpg",
  "duration": 5,
  "resolution": "1920x1080",
  "created_at": "2025-01-01T12:00:00Z",
  "completed_at": "2025-01-01T12:02:30Z"
}
```

## Prompt Tips

```
Good prompts:
✓ "A cat playing piano in a jazz club, warm lighting, cinematic"
✓ "Timelapse of flowers blooming in spring, macro photography"
✓ "Astronaut walking on Mars, red dust, realistic"

Avoid:
✗ "Video" (too vague)
✗ Very long paragraphs (keep it concise)
✗ Contradictory descriptions
```

## Output

Successful execution produces:
- Job ID for tracking
- Video URL for download/streaming
- Thumbnail URL for preview
- Generation metadata (duration, resolution, timing)

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key configuration
2. **400 Bad Request**: Validate prompt and parameters
3. **429 Rate Limited**: Wait and retry with backoff
4. **Content Policy Violation**: Modify prompt to comply with guidelines

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Documentation](https://docs.klingai.com/)
- [Prompt Guide](https://docs.klingai.com/prompts)
- [API Reference](https://docs.klingai.com/api)
