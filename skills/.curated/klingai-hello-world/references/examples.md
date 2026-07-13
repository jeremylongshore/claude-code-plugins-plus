# Examples

## Example 1: Python — Your First Video in 10 Lines

The minimal working example to verify your Kling AI setup and generate
a test video.

```python
import os, time, requests

API_KEY = os.environ["KLINGAI_API_KEY"]
BASE = "https://api.klingai.com/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Submit a text-to-video request
job = requests.post(f"{BASE}/videos/text2video", headers=HEADERS, json={
    "prompt": "A golden retriever running through a sunny meadow, cinematic quality",
    "duration": 5,
    "aspect_ratio": "16:9"
}).json()

print(f"Job ID: {job['job_id']}")

# Poll until complete
while True:
    result = requests.get(f"{BASE}/videos/{job['job_id']}", headers=HEADERS).json()
    if result["status"] == "completed":
        print(f"Video URL: {result['video_url']}")
        break
    elif result["status"] == "failed":
        print(f"Failed: {result.get('error')}")
        break
    time.sleep(5)
```

**Expected output:**

```
Job ID: vid_a1b2c3d4e5f6
Status: processing
Status: processing
Status: completed
Video URL: https://cdn.klingai.com/videos/vid_a1b2c3d4e5f6.mp4
```

## Example 2: cURL — Quick API Verification

Test your API key and connectivity without writing any code.

```bash
# Set your API key
export KLINGAI_API_KEY="your-api-key-here"

# Submit a generation request
JOB_ID=$(curl -s -X POST https://api.klingai.com/v1/videos/text2video \
  -H "Authorization: Bearer $KLINGAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Ocean waves crashing on a rocky coastline at sunset",
    "duration": 5,
    "aspect_ratio": "16:9"
  }' | jq -r '.job_id')

echo "Submitted job: $JOB_ID"

# Check status (run multiple times until completed)
curl -s "https://api.klingai.com/v1/videos/$JOB_ID" \
  -H "Authorization: Bearer $KLINGAI_API_KEY" | jq '{status, video_url, duration}'
```

**Expected response (when complete):**

```json
{
  "status": "completed",
  "video_url": "https://cdn.klingai.com/videos/vid_x7y8z9.mp4",
  "duration": 5
}
```

## Example 3: TypeScript/Node.js — Async/Await Pattern

A clean TypeScript implementation using native fetch with proper error handling.

```typescript
const KLINGAI_API_KEY = process.env.KLINGAI_API_KEY!;
const BASE_URL = "https://api.klingai.com/v1";

interface KlingJob {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  video_url?: string;
  thumbnail_url?: string;
  duration?: number;
  resolution?: string;
  error?: string;
}

async function createVideo(prompt: string): Promise<string> {
  const response = await fetch(`${BASE_URL}/videos/text2video`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${KLINGAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      prompt,
      duration: 5,
      aspect_ratio: "16:9",
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${await response.text()}`);
  }

  const data = await response.json();
  return data.job_id;
}

async function waitForVideo(jobId: string, timeoutMs = 300_000): Promise<KlingJob> {
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    const response = await fetch(`${BASE_URL}/videos/${jobId}`, {
      headers: { Authorization: `Bearer ${KLINGAI_API_KEY}` },
    });

    const result: KlingJob = await response.json();

    if (result.status === "completed") return result;
    if (result.status === "failed") throw new Error(`Failed: ${result.error}`);

    console.log(`Status: ${result.status}...`);
    await new Promise((r) => setTimeout(r, 5000));
  }

  throw new Error("Timeout waiting for video generation");
}

// Run
async function main() {
  const prompt = "A timelapse of clouds moving over a mountain range, 4K cinematic";
  console.log(`Generating: "${prompt}"`);

  const jobId = await createVideo(prompt);
  console.log(`Job ID: ${jobId}`);

  const result = await waitForVideo(jobId);
  console.log(`Video: ${result.video_url}`);
  console.log(`Thumbnail: ${result.thumbnail_url}`);
  console.log(`Resolution: ${result.resolution}`);
}

main().catch(console.error);
```

## Example 4: Python — Download the Generated Video

Extend the basic example to actually download the video file to disk.

```python
import os, time, requests
from pathlib import Path

API_KEY = os.environ["KLINGAI_API_KEY"]
BASE = "https://api.klingai.com/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def generate_and_download(prompt: str, output_dir: str = "output") -> str:
    """Generate a video and download it to a local file."""
    Path(output_dir).mkdir(exist_ok=True)

    # Submit job
    resp = requests.post(f"{BASE}/videos/text2video", headers=HEADERS, json={
        "prompt": prompt,
        "duration": 5,
        "aspect_ratio": "16:9"
    })
    resp.raise_for_status()
    job_id = resp.json()["job_id"]
    print(f"Job submitted: {job_id}")

    # Poll for completion
    for _ in range(60):  # max 5 minutes at 5s intervals
        result = requests.get(f"{BASE}/videos/{job_id}", headers=HEADERS).json()
        if result["status"] == "completed":
            break
        if result["status"] == "failed":
            raise RuntimeError(f"Generation failed: {result.get('error')}")
        time.sleep(5)
    else:
        raise TimeoutError("Timed out after 5 minutes")

    # Download the video
    video_url = result["video_url"]
    output_path = os.path.join(output_dir, f"{job_id}.mp4")

    print(f"Downloading video...")
    video_data = requests.get(video_url)
    video_data.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(video_data.content)

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Saved: {output_path} ({file_size_mb:.1f} MB)")
    return output_path

# Run
path = generate_and_download("A cat sitting on a windowsill watching rain")
print(f"Video saved to: {path}")
```

**Expected output:**

```
Job submitted: vid_r4s5t6u7v8
Downloading video...
Saved: output/vid_r4s5t6u7v8.mp4 (12.3 MB)
Video saved to: output/vid_r4s5t6u7v8.mp4
```

## Example 5: Prompt Engineering Tips for Better Results

Effective prompts follow a structure: subject + action + style + quality modifiers.

**Good prompts (specific, descriptive):**

```python
prompts = {
    "nature": (
        "A bald eagle soaring over a misty mountain valley at dawn, "
        "golden sunlight breaking through clouds, slow motion, "
        "National Geographic cinematic quality, 4K"
    ),
    "urban": (
        "Time-lapse of a busy Tokyo intersection at night, neon signs "
        "reflecting on wet pavement, cars and pedestrians streaking by, "
        "long exposure effect, cyberpunk aesthetic"
    ),
    "abstract": (
        "Fluid ink drops expanding in water, deep blue and gold colors, "
        "macro photography, slow motion capture, black background, "
        "high contrast, artistic"
    ),
    "product": (
        "A white ceramic coffee mug on a wooden table, steam rising gently, "
        "warm morning light from a nearby window, shallow depth of field, "
        "cozy cafe atmosphere, product photography style"
    ),
}
```

**Poor prompts vs improved versions:**

```
Bad:  "A dog"
Good: "A golden retriever puppy playing in autumn leaves, warm afternoon light"

Bad:  "City at night"
Good: "Aerial view of Manhattan skyline at dusk, lights turning on in buildings"

Bad:  "Ocean"
Good: "Turquoise ocean waves seen from underwater, sunlight filtering through"
```

## Example 6: Error Handling and Retry Logic

Production-ready example with proper error handling for common failure modes.

```python
import os, time, requests
from requests.exceptions import ConnectionError, Timeout

API_KEY = os.environ["KLINGAI_API_KEY"]
BASE = "https://api.klingai.com/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def create_video_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Submit a video request with automatic retry on transient failures."""
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{BASE}/videos/text2video",
                headers=HEADERS,
                json={"prompt": prompt, "duration": 5, "aspect_ratio": "16:9"},
                timeout=30
            )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 30))
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue

            if resp.status_code == 401:
                raise ValueError("Invalid API key. Check KLINGAI_API_KEY env var.")

            if resp.status_code == 400:
                error = resp.json().get("error", "Unknown")
                raise ValueError(f"Bad request: {error}")

            resp.raise_for_status()
            return resp.json()["job_id"]

        except (ConnectionError, Timeout) as e:
            wait = 2 ** attempt * 5  # exponential backoff: 5s, 10s, 20s
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"Failed after {max_retries} attempts")

# Usage
try:
    job_id = create_video_with_retry("Sunset over a calm lake, reflections on water")
    print(f"Success: {job_id}")
except ValueError as e:
    print(f"Client error (do not retry): {e}")
except RuntimeError as e:
    print(f"Exhausted retries: {e}")
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
