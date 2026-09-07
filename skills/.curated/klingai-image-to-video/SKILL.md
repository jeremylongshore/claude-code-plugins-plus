---
name: klingai-image-to-video
description: 'Animate static images into video using Kling AI. Use when converting
  images to video,

  adding motion to stills, or building I2V pipelines. Trigger with phrases like ''klingai
  image to video'',

  ''kling ai animate image'', ''klingai img2vid'', ''animate picture klingai''.

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.18.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- kling-ai
- image-to-video
- video-generation
compatibility: Designed for Claude Code
---
# Kling AI Image-to-Video

## Overview

Animate static images using the `/v1/videos/image2video` endpoint. Supports motion prompts, camera control, dynamic masks (motion brush), static masks, and tail images for start-to-end transitions.

**Endpoint:** `POST https://api.klingai.com/v1/videos/image2video`

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_name` | string | Yes | `kling-v1-5`, `kling-v2-1`, `kling-v2-master`, etc. |
| `image` | string | Yes | URL of the source image (JPG, PNG, WebP) |
| `prompt` | string | No | Motion description for the animation |
| `negative_prompt` | string | No | What to exclude |
| `duration` | string | Yes | `"5"` or `"10"` seconds |
| `aspect_ratio` | string | No | `"16:9"` default |
| `mode` | string | No | `"standard"` or `"professional"` |
| `cfg_scale` | float | No | Prompt adherence (0.0-1.0) |
| `image_tail` | string | No | End-frame image URL (mutually exclusive with masks/camera) |
| `camera_control` | object | No | Camera movement (mutually exclusive with masks/image_tail) |
| `static_mask` | string | No | Mask image URL for fixed regions |
| `dynamic_masks` | array | No | Motion brush trajectories |
| `callback_url` | string | No | Webhook for completion |

## Basic Image-to-Video

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

# Animate a landscape photo
response = requests.post(f"{BASE}/videos/image2video", headers=get_headers(), json={
    "model_name": "kling-v2-1",
    "image": "https://example.com/landscape.jpg",
    "prompt": "Clouds slowly drifting across the sky, gentle wind rustling through trees",
    "negative_prompt": "static, frozen, blurry",
    "duration": "5",
    "mode": "standard",
})

task_id = response.json()["data"]["task_id"]

# Poll for result
while True:
    time.sleep(15)
    result = requests.get(
        f"{BASE}/videos/image2video/{task_id}", headers=get_headers()
    ).json()
    if result["data"]["task_status"] == "succeed":
        print(f"Video: {result['data']['task_result']['videos'][0]['url']}")
        break
    elif result["data"]["task_status"] == "failed":
        raise RuntimeError(result["data"]["task_status_msg"])
```

## Start-to-End Transition (image_tail)

Use `image_tail` to specify both the first and last frame. Kling interpolates the motion between them.

```python
response = requests.post(f"{BASE}/videos/image2video", headers=get_headers(), json={
    "model_name": "kling-v2-master",
    "image": "https://example.com/sunrise.jpg",        # first frame
    "image_tail": "https://example.com/sunset.jpg",    # last frame
    "prompt": "Time lapse of sun moving across the sky",
    "duration": "5",
    "mode": "professional",
})
```

## Motion Brush (dynamic_masks)

Draw motion paths for specific elements in the image. Up to 6 motion paths per image in v2.6.

```python
response = requests.post(f"{BASE}/videos/image2video", headers=get_headers(), json={
    "model_name": "kling-v2-6",
    "image": "https://example.com/person-standing.jpg",
    "prompt": "Person walking forward naturally",
    "duration": "5",
    "dynamic_masks": [
        {
            "mask": "https://example.com/person-mask.png",  # white = selected region
            "trajectories": [
                {"x": 0.5, "y": 0.7, "t": 0.0},   # start position (normalized 0-1)
                {"x": 0.5, "y": 0.5, "t": 0.5},   # midpoint
                {"x": 0.5, "y": 0.3, "t": 1.0},   # end position
            ]
        }
    ],
})
```

## Static Mask (freeze regions)

Keep specific areas of the image static while animating the rest.

```python
response = requests.post(f"{BASE}/videos/image2video", headers=get_headers(), json={
    "model_name": "kling-v2-master",
    "image": "https://example.com/scene.jpg",
    "prompt": "Water flowing in the river, birds flying",
    "duration": "5",
    "static_mask": "https://example.com/buildings-mask.png",  # white = frozen
})
```

## Mutual Exclusivity Rules

These features cannot be combined in a single request:

| Feature Set A | Feature Set B |
|--------------|--------------|
| `image_tail` | `dynamic_masks`, `static_mask`, `camera_control` |
| `dynamic_masks` / `static_mask` | `image_tail`, `camera_control` |
| `camera_control` | `image_tail`, `dynamic_masks`, `static_mask` |

## Image Requirements

| Constraint | Value |
|-----------|-------|
| Formats | JPG, PNG, WebP |
| Max size | 10 MB |
| Min resolution | 300x300 px |
| Max resolution | 4096x4096 px |
| Mask format | PNG with white (selected) / black (excluded) |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `400` invalid image | URL unreachable or wrong format | Verify image URL is publicly accessible |
| `400` mutual exclusivity | Combined incompatible features | Use only one feature set per request |
| `task_status: failed` | Image too complex or low quality | Use higher resolution, clearer source |
| Mask mismatch | Mask dimensions differ from source | Ensure mask matches source image dimensions |

## Prerequisites

- A Kling API credential stored in the runtime secret manager, an approved model and duration allowlist, and a per-job credit budget.
- A synthetic or rights-cleared source image and any mask or tail image, with consent recorded for identifiable people and permission to transform the asset.
- A private staging bucket and a review owner. New generations must remain draft-only and watermarked until policy, quality, and publication approval are recorded.

## Instructions

1. Resolve the source and mask references from an approved allowlist; reject data from untrusted URLs, missing provenance, or assets containing an identifiable person without documented consent.
2. Validate format, dimensions, feature mutual exclusivity, prompt length, and the requested duration before spending credits. Use a synthetic fixture for automated checks.
3. Deduplicate the request using a stable job key, submit only after the content-policy check passes, and keep the task and source in private staging storage.
4. Run one short, watermarked sandbox canary. Check motion, policy outcome, source fidelity, and the credit budget before requesting an owner approval for a larger or public render.
5. On approval, promote the exact task result by digest. On failure or withdrawal, stop downstream publication, remove staged media and temporary URLs, and restore the prior approved asset or job state.
6. Record a redacted receipt containing only opaque job and asset digests, policy and approval outcomes, budget outcome, retention deadline, and rollback reference.

## Output

Return a result containing the opaque task identifier, model and duration, status, output digest or private staging URL, canary/approval state, and cleanup or rollback reference. Do not put source images, mask URLs, prompts, face data, credentials, or unredacted provider responses in logs or receipts.

## Examples

For a safe automated check, use a synthetic landscape fixture and a private canary:

```text
source=fixture:synthetic-landscape-v3; rights=cleared; mode=standard;
duration=5; canary=watermarked-sandbox; policy=pass; approval=pending;
publish=false; contacts_exported=0; receipt=asset-sha256:opaque
```

Do not substitute a live customer photograph or publish the canary until consent, policy, quality, and owner approval are all recorded.

## Resources

- [Image-to-Video API](https://app.klingai.com/global/dev/document-api/apiReference/model/imageToVideo)
- [Motion Control Guide](https://app.klingai.com/global/quickstart/motion-control-user-guide)
