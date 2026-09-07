---
name: klingai-model-catalog
description: 'Explore Kling AI models, versions, and capabilities for video and image
  generation. Use when

  selecting models or comparing features. Trigger with phrases like ''kling ai models'',

  ''klingai capabilities'', ''kling video models'', ''klingai features''.

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.18.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- kling-ai
- models
- reference
compatibility: Designed for Claude Code
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

## Prerequisites

- A dated snapshot of the provider's current model and capability documentation, a selection owner, an approved credit budget, and an explicit fallback model.
- Define the intended use, aspect ratio, duration, audio needs, quality/latency thresholds, and destination. Test with synthetic prompts and rights-cleared reference media only; confirm content-policy and likeness/consent requirements before submission.
- Use a sandbox project and draft/watermarked canaries. Production promotion requires owner approval and a rollback/removal plan for outputs that fail policy, rights, quality, or cost checks.

## Instructions

1. Translate the request into capability requirements, then verify each candidate's current support, limits, pricing mode, and policy constraints from the dated documentation snapshot.
2. Eliminate unsupported or unapproved candidates before generation. Run the smallest synthetic canary for the remaining candidates with `publish=false`, watermark/draft enabled, and an explicit credit ceiling.
3. Compare aggregate quality, latency, credit use, policy result, and rights review. Choose the model that satisfies the requirements and document why the fallback is acceptable.
4. Obtain approval before production use. Keep the selected model ID pinned, monitor the first staged release, and revert to the approved fallback if any threshold or policy check regresses.
5. Remove rejected, superseded, or unapproved canary media, revoke temporary access, and retain a redacted selection receipt rather than raw prompts or outputs.

## Output

Return a model-selection record with requirements, documentation snapshot date, candidate IDs and exclusions, synthetic fixture ID, aggregate canary metrics, estimated credits, policy/rights outcomes, selected model, fallback, approval state, rollout scope, retention deadline, and rollback/removal reference. Do not include prompts, media, likenesses, audio, signed URLs, identities, or secrets.

## Error Handling

- If documentation is stale, contradictory, or missing a capability, mark the candidate unknown and stop selection until verified; do not guess from a model name.
- If a candidate rejects content, lacks a required feature, exceeds budget, or fails quality/latency thresholds, quarantine and remove its canary output, then evaluate only an approved fallback.
- If the selected model becomes unavailable or changes behavior, pause promotion, restore the pinned fallback, reconcile in-flight tasks, and record the redacted rollback receipt.

## Examples

For a synthetic vertical draft, set `requirements=t2v,9:16,5s`, candidates `kling-v2-5-turbo,kling-v2-6`, `destination=sandbox-review`, `watermark=draft`, `publish=false`, and `credits_max=100`. Select only after `policy=pass`, `rights=pass`, and owner approval; otherwise remove both canary outputs.

## Resources

- [Model Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/skillsMap)
- [Video Duration Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/videoDuration)
- [Pricing](https://app.klingai.com/global/dev/document-api/productBilling/prePaidResourcePackage)
