---
name: klingai-camera-control
description: |
  Control camera movements in Kling AI video generation. Use when creating cinematic shots,
  pans, tilts, zooms, or dolly moves. Trigger with phrases like 'klingai camera',
  'kling ai camera motion', 'klingai cinematic', 'klingai pan zoom'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, camera-control, cinematic]

---
# Kling AI Camera Control

## Overview

Add controlled camera movements to text-to-video and image-to-video generation using the `camera_control` parameter. Supports pan, tilt, zoom, roll, and dolly. Available on v1.6+ models.

**Supports:** `POST /v1/videos/text2video` and `POST /v1/videos/image2video`

## Camera Control Parameters

```python
"camera_control": {
    "type": "simple",     # "simple" = one movement axis
    "config": {
        "horizontal": 0,  # Pan: -10 (left) to 10 (right)
        "vertical": 0,    # Tilt: -10 (down) to 10 (up)
        "zoom": 0,         # Zoom: -10 (out) to 10 (in)
        "roll": 0,         # Roll: -10 (CCW) to 10 (CW)
        "pan": 0,          # Dolly: -10 (left) to 10 (right)
        "tilt": 0,         # Dolly: -10 (down) to 10 (up)
    }
}
```

**Rule:** For `type: "simple"`, only ONE field in `config` can be non-zero.

## Cinematic Shot Examples

### Slow Pan Right

```python
response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-6",
    "prompt": "A medieval castle on a cliff at sunrise, fog in the valley below",
    "duration": "5",
    "mode": "professional",
    "camera_control": {
        "type": "simple",
        "config": {"horizontal": 5, "vertical": 0, "zoom": 0, "roll": 0, "pan": 0, "tilt": 0}
    },
})
```

### Dramatic Zoom In

```python
response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-6",
    "prompt": "Close-up of a tiger's face, intense eyes, jungle background",
    "duration": "5",
    "mode": "professional",
    "camera_control": {
        "type": "simple",
        "config": {"horizontal": 0, "vertical": 0, "zoom": 7, "roll": 0, "pan": 0, "tilt": 0}
    },
})
```

### Tilt Up Reveal

```python
response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-6",
    "prompt": "A skyscraper, starting from the base looking up, glass and steel",
    "duration": "5",
    "mode": "standard",
    "camera_control": {
        "type": "simple",
        "config": {"horizontal": 0, "vertical": 8, "zoom": 0, "roll": 0, "pan": 0, "tilt": 0}
    },
})
```

### Dolly Forward

```python
response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-master",
    "prompt": "Walking through a dark forest, trees on both sides, moonlight filtering through",
    "duration": "5",
    "mode": "standard",
    "camera_control": {
        "type": "simple",
        "config": {"horizontal": 0, "vertical": 0, "zoom": 0, "roll": 0, "pan": 0, "tilt": 5}
    },
})
```

## Camera Control with Image-to-Video

```python
# Animate a landscape photo with a slow zoom out
response = requests.post(f"{BASE}/videos/image2video", headers=get_headers(), json={
    "model_name": "kling-v2-1",
    "image": "https://example.com/landscape.jpg",
    "prompt": "Gentle wind, clouds moving slowly",
    "duration": "5",
    "camera_control": {
        "type": "simple",
        "config": {"horizontal": 0, "vertical": 0, "zoom": -5, "roll": 0, "pan": 0, "tilt": 0}
    },
})
```

**Important:** For image-to-video, `camera_control` is mutually exclusive with `image_tail`, `dynamic_masks`, and `static_mask`.

## Shot Type Quick Reference

| Shot Type | Config Field | Value | Description |
|-----------|-------------|-------|-------------|
| Pan right | `horizontal` | 5-8 | Slow pan, good for landscapes |
| Pan left | `horizontal` | -5 to -8 | Reveal from right to left |
| Tilt up | `vertical` | 5-8 | Upward reveal (buildings, trees) |
| Tilt down | `vertical` | -5 to -8 | Downward motion |
| Zoom in | `zoom` | 5-10 | Focus on subject, dramatic |
| Zoom out | `zoom` | -5 to -10 | Reveal, establishing shot |
| Dutch tilt | `roll` | 3-5 | Unsettling, artistic angle |
| Push in | `tilt` | 3-5 | Dolly forward (depth effect) |
| Pull back | `tilt` | -3 to -5 | Dolly backward (reveal) |

## Intensity Guidelines

| Value Range | Effect |
|-------------|--------|
| 1-3 | Subtle, barely perceptible |
| 4-6 | Moderate, natural-feeling |
| 7-8 | Strong, dramatic |
| 9-10 | Maximum, may feel unnatural |

**Recommendation:** Start at 4-6 for most cinematic shots. Go higher for dramatic reveals or action sequences.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `400` invalid camera config | Multiple non-zero values in simple mode | Set only one field to non-zero |
| Jerky motion | Value too high | Reduce to 4-6 range |
| No visible movement | Value too low (1-2) | Increase to 3+ |
| Mutual exclusivity error | Combined with masks/image_tail | Use only camera_control OR masks |

## Resources

- [Camera Control Guide](https://app.klingai.com/global/quickstart/ai-camera-control-guide)
- [Motion Control Guide](https://app.klingai.com/global/quickstart/motion-control-user-guide)
- [Developer Portal](https://app.klingai.com/global/dev)
