---
name: klingai-model-catalog
description: |
  Explore Kling AI models and their capabilities for video generation. Use when selecting models
  or understanding features. Trigger with phrases like 'kling ai models', 'klingai capabilities',
  'kling video models', 'klingai features'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Model Catalog

## Overview

This skill provides a comprehensive guide to Kling AI's video generation models, their capabilities, recommended use cases, and how to select the right model for your needs.

## Prerequisites

- Kling AI API key configured
- Understanding of video generation concepts
- Knowledge of your use case requirements

## Instructions

Follow these steps to understand and select Kling AI models:

1. **Review Available Models**: Understand the model options
2. **Compare Capabilities**: Evaluate features vs requirements
3. **Test with Samples**: Try each model with your prompts
4. **Optimize Selection**: Choose based on quality/speed/cost tradeoffs
5. **Monitor Performance**: Track results and adjust as needed

## Available Models

### Kling 1.0 (Standard)
```
Model ID: kling-v1
Type: Text-to-Video, Image-to-Video

Capabilities:
- Video duration: 5-10 seconds
- Resolutions: 720p, 1080p
- Aspect ratios: 16:9, 9:16, 1:1
- Frame rate: 24 fps

Best for:
- Social media content
- Quick prototypes
- Standard quality needs
- Cost-sensitive projects

Pricing: ~$0.05 per second
```

### Kling 1.5 (Enhanced)
```
Model ID: kling-v1.5
Type: Text-to-Video, Image-to-Video

Capabilities:
- Video duration: 5-30 seconds
- Resolutions: 1080p, 4K
- Aspect ratios: 16:9, 9:16, 1:1, 4:3
- Frame rate: 24, 30, 60 fps
- Camera controls: Pan, zoom, tilt

Best for:
- Professional content
- Marketing videos
- High-quality productions
- Extended duration needs

Pricing: ~$0.10 per second
```

### Kling Pro (Premium)
```
Model ID: kling-pro
Type: Text-to-Video, Image-to-Video, Video Extension

Capabilities:
- Video duration: 5-60 seconds
- Resolutions: Up to 4K
- All aspect ratios supported
- Frame rate: Up to 60 fps
- Advanced camera controls
- Style transfer
- Character consistency

Best for:
- Film production
- High-end advertising
- Complex scenes
- Maximum quality

Pricing: ~$0.20 per second
```

## Model Comparison

```
Feature          | Kling 1.0 | Kling 1.5 | Kling Pro
-----------------|-----------|-----------|----------
Max Duration     | 10s       | 30s       | 60s
Max Resolution   | 1080p     | 4K        | 4K
Frame Rate       | 24 fps    | 60 fps    | 60 fps
Camera Controls  | Basic     | Advanced  | Full
Style Transfer   | No        | Limited   | Yes
Character Lock   | No        | No        | Yes
Cost per Second  | $0.05     | $0.10     | $0.20
Generation Speed | Fast      | Medium    | Slower
```

## Querying Available Models

```python
import requests
import os

def get_available_models():
    """Retrieve list of available models."""
    response = requests.get(
        "https://api.klingai.com/v1/models",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"}
    )
    return response.json()["models"]

models = get_available_models()
for model in models:
    print(f"Model: {model['id']}")
    print(f"  Name: {model['name']}")
    print(f"  Max Duration: {model['max_duration']}s")
    print(f"  Resolutions: {model['resolutions']}")
    print(f"  Price: ${model['price_per_second']}/second")
    print()
```

## Model Selection Logic

```python
def select_model(
    duration: int,
    resolution: str,
    quality: str = "standard",
    budget_per_second: float = 0.10
) -> str:
    """Select the best model for requirements."""

    # Duration constraints
    if duration > 30:
        return "kling-pro"

    # Quality requirements
    if quality == "premium" or resolution == "4k":
        if budget_per_second >= 0.20:
            return "kling-pro"
        return "kling-v1.5"

    # Budget optimization
    if budget_per_second < 0.10:
        return "kling-v1"

    # Default to enhanced
    return "kling-v1.5"

# Usage
model = select_model(duration=15, resolution="1080p", quality="high")
print(f"Recommended model: {model}")
```

## Generation Types

### Text-to-Video
```python
def text_to_video(prompt: str, model: str = "kling-v1.5"):
    """Generate video from text prompt."""
    response = requests.post(
        "https://api.klingai.com/v1/videos/text2video",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"},
        json={
            "model": model,
            "prompt": prompt,
            "duration": 10,
            "aspect_ratio": "16:9"
        }
    )
    return response.json()
```

### Image-to-Video
```python
def image_to_video(image_url: str, motion_prompt: str, model: str = "kling-v1.5"):
    """Animate an image into video."""
    response = requests.post(
        "https://api.klingai.com/v1/videos/image2video",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"},
        json={
            "model": model,
            "image_url": image_url,
            "motion_prompt": motion_prompt,
            "duration": 5
        }
    )
    return response.json()
```

### Video Extension
```python
def extend_video(video_id: str, additional_seconds: int):
    """Extend an existing video (Pro only)."""
    response = requests.post(
        "https://api.klingai.com/v1/videos/extend",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"},
        json={
            "model": "kling-pro",
            "source_video_id": video_id,
            "extend_duration": additional_seconds
        }
    )
    return response.json()
```

## Output

Successful execution produces:
- List of available models with capabilities
- Model recommendation based on requirements
- Understanding of pricing and tradeoffs

## Error Handling

Common errors and solutions:
1. **Model Not Available**: Check account tier and model access
2. **Feature Not Supported**: Verify model supports requested feature
3. **Duration Exceeded**: Use appropriate model for longer videos
4. **Resolution Not Supported**: Check model's supported resolutions

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Models Documentation](https://docs.klingai.com/models)
- [Pricing Calculator](https://klingai.com/pricing)
- [Feature Comparison](https://docs.klingai.com/features)
