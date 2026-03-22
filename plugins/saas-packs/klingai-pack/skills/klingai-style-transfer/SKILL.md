---
name: klingai-style-transfer
description: |
  Apply artistic styles and visual effects to Kling AI video generation. Use when creating
  stylized content or using effects API. Trigger with phrases like 'klingai style', 'kling ai effects',
  'klingai artistic video', 'stylize klingai video'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, style-transfer, effects]

---
# Kling AI Style Transfer & Effects

## Overview

Apply artistic styles through prompt engineering, use the Effects API for pre-built visual transformations, and leverage Kolors for image-based style references. Available on v1.6+ models.

## Style via Prompt Engineering

The most direct approach -- include style descriptors in your prompt:

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

# Style: Studio Ghibli watercolor
response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-6",
    "prompt": "A cozy cottage in a meadow, hand-painted watercolor style, "
              "soft pastel colors, Studio Ghibli aesthetic, gentle breeze",
    "negative_prompt": "photorealistic, harsh lighting, dark, gritty",
    "duration": "5",
    "mode": "professional",
    "cfg_scale": 0.7,  # higher = stricter prompt adherence
})
```

## Style Prompt Recipes

| Style | Prompt Keywords | cfg_scale |
|-------|----------------|-----------|
| Cinematic | "cinematic lighting, anamorphic lens, film grain, 35mm" | 0.5-0.6 |
| Anime | "anime style, cel-shaded, vibrant colors, clean lines" | 0.6-0.7 |
| Watercolor | "watercolor painting, soft edges, pastel, hand-painted" | 0.7-0.8 |
| Oil painting | "oil painting, thick brushstrokes, impasto, canvas texture" | 0.7-0.8 |
| Neon/cyberpunk | "neon lights, cyberpunk, rain, dark city, purple and blue" | 0.5-0.6 |
| Vintage film | "vintage 8mm film, warm tones, light leaks, soft focus" | 0.6-0.7 |
| Pixel art | "pixel art style, retro 16-bit, limited palette" | 0.8-0.9 |
| Photorealistic | "photorealistic, 4K, natural lighting, DSLR quality" | 0.4-0.5 |

## Effects API

The Effects API applies pre-built transformations to existing images. Available on v1.6+.

**Endpoint:** `POST https://api.klingai.com/v1/videos/effects`

```python
# Apply an effect to an image
response = requests.post(f"{BASE}/videos/effects", headers=get_headers(), json={
    "model_name": "kling-v1-6",
    "image": "https://example.com/portrait.jpg",
    "effect_type": "hug",           # effect to apply
    "duration": "5",
    "mode": "standard",
})

task_id = response.json()["data"]["task_id"]
# Poll for result as usual
```

## Available Effects

| Effect | Description |
|--------|-------------|
| `hug` | Embrace/hug motion between subjects |
| `kiss` | Kiss animation between subjects |
| `heart` | Heart gesture or heart-shaped framing |
| `expand` | Zoom/expand outward effect |
| `squish` | Compression/squish animation |

## Kolors Image Restyle

Use Kolors to restyle images before converting to video:

```python
# Generate styled image with Kolors
image_response = requests.post(f"{BASE}/images/kolors", headers=get_headers(), json={
    "prompt": "A cyberpunk city street, neon signs, rain-slicked roads",
    "aspect_ratio": "16:9",
    "imageCount": 1,
})

# Then use the generated image as input for I2V
image_url = image_response.json()["data"]["images"][0]["url"]
video_response = requests.post(f"{BASE}/videos/image2video", headers=get_headers(), json={
    "model_name": "kling-v2-1",
    "image": image_url,
    "prompt": "Camera slowly pushes forward through the rain, neon reflections",
    "duration": "5",
    "mode": "professional",
})
```

## cfg_scale Tuning

The `cfg_scale` parameter (0.0-1.0) controls how strictly the model follows your prompt:

| cfg_scale | Effect |
|-----------|--------|
| 0.0-0.3 | More creative freedom, may drift from prompt |
| 0.4-0.5 | Balanced (default), natural results |
| 0.6-0.7 | Stronger prompt adherence |
| 0.8-1.0 | Very strict, may reduce quality/naturalness |

**For style transfer:** Use 0.6-0.8 to ensure the style keywords are respected.

## Style Consistency Across Clips

```python
# Use a consistent style template for all clips in a project
STYLE_TEMPLATE = {
    "suffix": ", cinematic lighting, 35mm film grain, warm color grading, "
              "anamorphic lens flare, shallow depth of field",
    "negative": "cartoon, anime, painting, illustration, CGI, digital art",
    "cfg_scale": 0.6,
    "model": "kling-v2-6",
    "mode": "professional",
}

def styled_generation(scene_prompt: str):
    return requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
        "model_name": STYLE_TEMPLATE["model"],
        "prompt": scene_prompt + STYLE_TEMPLATE["suffix"],
        "negative_prompt": STYLE_TEMPLATE["negative"],
        "cfg_scale": STYLE_TEMPLATE["cfg_scale"],
        "duration": "5",
        "mode": STYLE_TEMPLATE["mode"],
    })
```

## Resources

- [Effects API](https://app.klingai.com/global/dev/document-api/apiReference/model/videoEffects)
- [Kolors API](https://app.klingai.com/global/dev/document-api/apiReference/model/imageGeneration)
- [Developer Portal](https://app.klingai.com/global/dev)
