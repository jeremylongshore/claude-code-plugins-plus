---
name: klingai-model-catalog
description: |
  Explore Kling AI models, versions, and capabilities for video and image generation. Use when
  selecting models or comparing features. Trigger with phrases like 'kling ai models',
  'klingai capabilities', 'kling video models', 'klingai features'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, models, reference]

---
# Kling AI Model Catalog

## Overview

Kling AI offers multiple model versions across video generation, image generation, lip sync, virtual try-on, and effects. Each version trades off quality, speed, and cost. This skill is the reference for choosing the right model.

## Video Generation Models

| Model ID | Supports | Max Duration | Resolution | Speed | Quality |
|----------|----------|-------------|------------|-------|---------|
| `kling-v1` | T2V, I2V | 10s | 720p | Fast | Good |
| `kling-v1-5` | I2V only | 10s | 1080p | Fast | Better |
| `kling-v1-6` | T2V, I2V | 10s | 1080p | Medium | Better+ |
| `kling-v2-master` | T2V, I2V | 10s | 1080p | Medium | High |
| `kling-v2-1` | I2V only | 10s | 1080p | Medium | High |
| `kling-v2-1-master` | T2V, I2V | 10s | 1080p | Medium | High |
| `kling-v2-5-turbo` | T2V, I2V | 10s | 1080p 30fps | Fast | High |
| `kling-v2-6` | T2V, I2V | 10s | 1080p 30-48fps | Medium | Highest |

**T2V** = text-to-video, **I2V** = image-to-video

### Kling v2.5 Turbo (Recommended for Speed)
- 40% faster than v2.0
- Up to 1080p at 30 FPS
- Best cost/quality ratio for production pipelines

### Kling v2.6 (Recommended for Quality)
- Native audio generation (voice, SFX, ambient in one pass)
- 1080p at 30-48 FPS
- Set `motion_has_audio: true` for synchronized audio

## Image Generation Models (Kolors)

| Model ID | Purpose | Resolution |
|----------|---------|------------|
| `kolors-v1-5` | Face/subject reference | Up to 2048x2048 |
| `kolors-v2-0` | Image restyle | Up to 2048x2048 |
| `kolors-v2-1` | Text-to-image | Up to 2048x2048 |

## Specialty Models

| Feature | Endpoint | Model Versions |
|---------|----------|----------------|
| **Lip Sync** | `/v1/videos/lip-sync` | v1.6+ |
| **Virtual Try-On** | `/v1/images/kolors-virtual-try-on` | v1.5 |
| **Video Extension** | `/v1/videos/video-extend` | All video models |
| **Effects** | `/v1/videos/effects` | v1.6+ |
| **Motion Control** | T2V/I2V with `camera_control` | v1.6+ |

## Mode Selection

Every video generation accepts a `mode` parameter:

| Mode | Credits (5s) | Credits (10s) | Use Case |
|------|-------------|---------------|----------|
| `standard` | 10 | 20 | Drafts, previews, iteration |
| `professional` | 35 | 70 | Final output, client delivery |

## Model Selection Decision Tree

```
Need fastest generation?
  → kling-v2-5-turbo + standard mode

Need highest quality?
  → kling-v2-6 + professional mode

Need audio in the video?
  → kling-v2-6 with motion_has_audio: true

Image-to-video only?
  → kling-v2-1 (optimized for I2V)

Budget-conscious production?
  → kling-v2-5-turbo + standard mode (10 credits/5s)

Legacy compatibility?
  → kling-v1-6 (stable, well-documented)
```

## API Usage

```python
# Specify model in any video generation request
response = requests.post(f"{BASE}/videos/text2video", headers=headers, json={
    "model_name": "kling-v2-6",       # model version
    "mode": "professional",            # standard or professional
    "prompt": "A futuristic city at sunset with flying cars",
    "duration": "5",
    "aspect_ratio": "16:9",
})
```

## Aspect Ratios (All Models)

| Ratio | Use Case |
|-------|----------|
| `16:9` | Landscape, YouTube, presentations |
| `9:16` | Vertical, TikTok, Reels, Stories |
| `1:1` | Square, Instagram, thumbnails |
| `4:3` | Classic TV, presentations |
| `3:4` | Portrait photos |
| `3:2` | Standard photography |
| `2:3` | Tall portrait |
| `21:9` | Ultra-wide, cinematic |

## Resources

- [Model Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/skillsMap)
- [Video Duration Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/videoDuration)
- [Pricing](https://app.klingai.com/global/dev/document-api/productBilling/prePaidResourcePackage)
