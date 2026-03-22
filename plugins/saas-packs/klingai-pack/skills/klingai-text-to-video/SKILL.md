---
name: klingai-text-to-video
description: |
  Generate videos from text prompts with Kling AI. Use when creating videos from descriptions,
  learning prompt techniques, or building T2V pipelines. Trigger with phrases like 'kling ai text to video',
  'klingai prompt', 'generate video from text', 'text2video kling'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, text-to-video, video-generation]

---
# Kling AI Text-to-Video

## Overview

Generate videos from text prompts using the `/v1/videos/text2video` endpoint. Supports models v1 through v2.6, standard/professional modes, camera control, negative prompts, and native audio (v2.6+).

**Endpoint:** `POST https://api.klingai.com/v1/videos/text2video`

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_name` | string | Yes | Model version (see model catalog) |
| `prompt` | string | Yes | Video description, max 2500 chars |
| `negative_prompt` | string | No | What to exclude from generation |
| `duration` | string | Yes | `"5"` or `"10"` seconds |
| `aspect_ratio` | string | No | `"16:9"` (default), `"9:16"`, `"1:1"`, etc. |
| `mode` | string | No | `"standard"` (default) or `"professional"` |
| `cfg_scale` | float | No | Prompt adherence (0.0-1.0, default 0.5) |
| `camera_control` | object | No | Camera movement config |
| `callback_url` | string | No | Webhook URL for completion notification |

## Complete Example — Python

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

# Create text-to-video task
response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-6",
    "prompt": "Aerial drone shot of a coral reef at golden hour, "
              "tropical fish swimming through crystal clear water, "
              "sun rays penetrating the surface, cinematic 4K",
    "negative_prompt": "blurry, low quality, distorted, watermark",
    "duration": "5",
    "aspect_ratio": "16:9",
    "mode": "professional",
    "cfg_scale": 0.5,
})

task = response.json()
task_id = task["data"]["task_id"]

# Poll for completion
while True:
    time.sleep(15)
    result = requests.get(
        f"{BASE}/videos/text2video/{task_id}", headers=get_headers()
    ).json()

    status = result["data"]["task_status"]
    if status == "succeed":
        video = result["data"]["task_result"]["videos"][0]
        print(f"Video URL: {video['url']}")
        print(f"Duration: {video['duration']}s")
        break
    elif status == "failed":
        raise RuntimeError(result["data"]["task_status_msg"])
    # else: submitted/processing — keep polling
```

## With Camera Control

```python
# Camera movement types: pan, tilt, zoom, roll
response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-6",
    "prompt": "A medieval castle on a cliff at sunrise, fog in the valley",
    "duration": "5",
    "mode": "standard",
    "camera_control": {
        "type": "simple",
        "config": {
            "horizontal": 5,    # pan right (negative = left), range -10 to 10
            "vertical": 0,      # tilt (negative = down, positive = up)
            "zoom": 3,          # zoom in (positive) or out (negative)
            "roll": 0,          # rotation
            "pan": 0,           # dolly left/right
            "tilt": -2,         # dolly up/down
        }
    },
})
```

**Rule:** Only one non-zero field in `config` for `type: "simple"`.

## With Native Audio (v2.6 only)

```python
response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-6",
    "prompt": "A jazz band performing in a dimly lit club, saxophone solo, "
              "audience clapping, warm amber lighting",
    "duration": "10",
    "mode": "professional",
    "motion_has_audio": True,  # generates synchronized audio
})
```

## Prompt Engineering Tips

| Technique | Example |
|-----------|---------|
| Scene + action + style | "A samurai walking through cherry blossoms, cinematic slow motion" |
| Lighting cues | "golden hour", "neon-lit", "overcast diffused light" |
| Camera language | "close-up", "wide establishing shot", "tracking shot" |
| Negative prompt | "blurry, watermark, text overlay, distorted faces" |
| Material/texture | "brushed steel", "hand-painted watercolor", "photorealistic" |

## Cost Reference

| Duration | Standard | Professional |
|----------|----------|-------------|
| 5 seconds | 10 credits | 35 credits |
| 10 seconds | 20 credits | 70 credits |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `400` invalid prompt | Empty or >2500 chars | Check prompt length |
| `400` invalid model | Unsupported `model_name` | Use valid model ID from catalog |
| `402` insufficient credits | Not enough credits | Top up account |
| `task_status: failed` | Content policy violation or complexity | Simplify prompt, remove restricted content |

## Resources

- [Text-to-Video API](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Camera Control Guide](https://app.klingai.com/global/quickstart/ai-camera-control-guide)
- [Content Guidelines](https://app.klingai.com/global/dev/document-api/protocols/paidServiceProtocol)
