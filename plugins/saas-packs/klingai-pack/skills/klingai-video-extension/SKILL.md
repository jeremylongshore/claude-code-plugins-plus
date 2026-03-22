---
name: klingai-video-extension
description: |
  Extend video duration using Kling AI continuation. Use when creating longer videos from
  shorter clips or building sequences. Trigger with phrases like 'klingai extend video',
  'kling ai video continuation', 'klingai longer video', 'extend klingai clip'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, video-extension, continuation]

---
# Kling AI Video Extension

## Overview

Extend an existing video by appending additional seconds. The extension endpoint takes the `task_id` of a completed video and generates a seamless continuation.

**Endpoint:** `POST https://api.klingai.com/v1/videos/video-extend`

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task ID of the completed source video |
| `prompt` | string | No | Motion/scene description for extension |
| `duration` | string | No | Extension length: `"5"` (default) |
| `mode` | string | No | `"standard"` or `"professional"` |
| `model_name` | string | No | Default: `"kling-v2-master"` |
| `callback_url` | string | No | Webhook for completion |

## Basic Extension

```python
import jwt, time, os, requests

BASE = "https://api.klingai.com/v1"

def get_headers():
    ak, sk = os.environ["KLING_ACCESS_KEY"], os.environ["KLING_SECRET_KEY"]
    token = jwt.encode(
        {"iss": ak, "exp": int(time.time()) + 1800, "nbf": int(time.time()) - 5},
        sk, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"}
    )
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Step 1: Generate the initial 5s video
initial = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-master",
    "prompt": "A rocket launching from a desert landscape, cinematic",
    "duration": "5",
    "mode": "standard",
}).json()
initial_task_id = initial["data"]["task_id"]

# Wait for completion...
# (poll until task_status == "succeed")

# Step 2: Extend by 5 more seconds
extension = requests.post(f"{BASE}/videos/video-extend", headers=get_headers(), json={
    "task_id": initial_task_id,
    "prompt": "The rocket ascends through clouds into the stratosphere",
    "duration": "5",
    "mode": "standard",
}).json()
ext_task_id = extension["data"]["task_id"]

# Step 3: Poll extension task
while True:
    time.sleep(15)
    result = requests.get(
        f"{BASE}/videos/video-extend/{ext_task_id}", headers=get_headers()
    ).json()
    if result["data"]["task_status"] == "succeed":
        extended_url = result["data"]["task_result"]["videos"][0]["url"]
        print(f"Extended video: {extended_url}")
        break
    elif result["data"]["task_status"] == "failed":
        print(f"Failed: {result['data']['task_status_msg']}")
        break
```

## Chain Multiple Extensions

```python
def chain_extensions(initial_task_id: str, prompts: list[str],
                     duration: str = "5", mode: str = "standard") -> list[str]:
    """Chain multiple extensions to build a longer video."""
    current_task_id = initial_task_id
    video_urls = []

    for i, prompt in enumerate(prompts):
        print(f"Extension {i + 1}/{len(prompts)}: submitting...")

        # Submit extension
        r = requests.post(f"{BASE}/videos/video-extend", headers=get_headers(), json={
            "task_id": current_task_id,
            "prompt": prompt,
            "duration": duration,
            "mode": mode,
        }).json()
        ext_task_id = r["data"]["task_id"]

        # Poll for completion
        while True:
            time.sleep(15)
            result = requests.get(
                f"{BASE}/videos/video-extend/{ext_task_id}", headers=get_headers()
            ).json()
            status = result["data"]["task_status"]

            if status == "succeed":
                url = result["data"]["task_result"]["videos"][0]["url"]
                video_urls.append(url)
                current_task_id = ext_task_id  # next extension chains from this
                print(f"Extension {i + 1} complete: {url}")
                break
            elif status == "failed":
                raise RuntimeError(f"Extension {i + 1} failed: {result['data']['task_status_msg']}")

    return video_urls
```

## Usage: Build a 20-Second Video

```python
# Generate initial 5s
initial_r = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-master",
    "prompt": "Morning sunrise over a mountain lake, mist rising",
    "duration": "5",
    "mode": "standard",
}).json()
initial_id = initial_r["data"]["task_id"]
# ... poll until complete ...

# Chain 3 more extensions = 5 + 5 + 5 + 5 = 20 seconds total
extensions = chain_extensions(initial_id, [
    "Sun rises higher, birds begin flying across the lake",
    "A deer approaches the water's edge to drink",
    "Wide shot pulling back to reveal the full mountain range",
])
```

## Cost

Each extension costs the same as a new generation:

| Extension Duration | Standard | Professional |
|-------------------|----------|-------------|
| 5 seconds | 10 credits | 35 credits |

A 20-second video (initial + 3 extensions) costs 40 credits in standard mode.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Invalid `task_id` | Source task doesn't exist | Verify task_id is from a completed generation |
| Source not complete | Extending a task still processing | Wait for source task to reach `succeed` status |
| Extension failed | Prompt conflict with source | Align extension prompt with original scene |

## Resources

- [Video Extension API](https://app.klingai.com/global/dev/document-api/apiReference/model/videoExtension)
- [Developer Portal](https://app.klingai.com/global/dev)
