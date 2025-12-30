---
name: klingai-text-to-video
description: |
  Generate videos from text prompts with Kling AI. Use when creating videos from descriptions or
  learning prompt techniques. Trigger with phrases like 'kling ai text to video', 'klingai prompt',
  'generate video from text', 'text2video kling'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Text-to-Video

## Overview

This skill covers text-to-video generation with Kling AI, including prompt engineering techniques, parameter optimization, and best practices for high-quality video output.

## Prerequisites

- Kling AI API key configured
- Understanding of video generation concepts
- Python 3.8+ or Node.js 18+

## Instructions

Follow these steps for text-to-video generation:

1. **Craft Your Prompt**: Write a descriptive, clear prompt
2. **Select Parameters**: Choose duration, resolution, aspect ratio
3. **Submit Request**: Send the generation request
4. **Monitor Progress**: Track job status
5. **Download Result**: Retrieve the generated video

## Basic Text-to-Video

```python
import os
import requests
import time

def text_to_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    model: str = "kling-v1.5"
) -> dict:
    """Generate video from text prompt."""

    headers = {
        "Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}",
        "Content-Type": "application/json"
    }

    # Submit generation request
    response = requests.post(
        "https://api.klingai.com/v1/videos/text2video",
        headers=headers,
        json={
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }
    )
    response.raise_for_status()
    job_id = response.json()["job_id"]

    # Wait for completion
    while True:
        status_response = requests.get(
            f"https://api.klingai.com/v1/videos/{job_id}",
            headers=headers
        )
        result = status_response.json()

        if result["status"] == "completed":
            return result
        elif result["status"] == "failed":
            raise Exception(f"Generation failed: {result.get('error')}")

        time.sleep(5)

# Usage
result = text_to_video(
    prompt="A majestic eagle soaring over snow-capped mountains at golden hour",
    duration=10,
    aspect_ratio="16:9"
)
print(f"Video URL: {result['video_url']}")
```

## Prompt Engineering

### Anatomy of a Good Prompt
```
[Subject] + [Action] + [Setting] + [Style] + [Quality Modifiers]

Example:
"A golden retriever [subject] running through tall grass [action]
in a sunny meadow [setting], cinematic lighting [style],
8K resolution, photorealistic [quality]"
```

### Prompt Templates

```python
PROMPT_TEMPLATES = {
    "cinematic": "{subject}, {action}, cinematic lighting, film grain, shallow depth of field, professional color grading",

    "nature": "{subject} in {setting}, golden hour lighting, National Geographic style, 8K resolution",

    "product": "{product} rotating slowly, studio lighting, white background, professional product photography",

    "social_media": "{subject}, {action}, trending on social media, vertical format, vibrant colors, engaging",

    "artistic": "{subject}, {style} art style, {mood} atmosphere, artistic interpretation, creative"
}

def generate_prompt(template: str, **kwargs) -> str:
    """Generate prompt from template."""
    return PROMPT_TEMPLATES[template].format(**kwargs)

# Usage
prompt = generate_prompt(
    "cinematic",
    subject="a vintage car",
    action="driving down a coastal highway at sunset"
)
```

### Good vs Bad Prompts

```
GOOD PROMPTS:
✓ "A hummingbird hovering near red flowers, macro photography, slow motion, nature documentary style"
✓ "Timelapse of storm clouds gathering over a cityscape, dramatic lighting, 4K cinematic"
✓ "A chef preparing sushi, close-up hands, professional kitchen, warm lighting"

BAD PROMPTS:
✗ "Video of stuff happening" (too vague)
✗ "A person walking and then running and then jumping and then swimming..." (too complex)
✗ "Make it look good" (no specific direction)
✗ "[Long paragraph with 500 words]" (too long, unfocused)
```

## Advanced Parameters

```python
def advanced_text_to_video(
    prompt: str,
    duration: int = 10,
    aspect_ratio: str = "16:9",
    model: str = "kling-v1.5",
    resolution: str = "1080p",
    frame_rate: int = 24,
    negative_prompt: str = None,
    seed: int = None,
    camera_motion: dict = None
) -> dict:
    """Generate video with advanced parameters."""

    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "frame_rate": frame_rate
    }

    # Optional parameters
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt

    if seed is not None:
        payload["seed"] = seed

    if camera_motion:
        payload["camera_motion"] = camera_motion

    response = requests.post(
        "https://api.klingai.com/v1/videos/text2video",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"},
        json=payload
    )
    return response.json()

# Usage with advanced parameters
result = advanced_text_to_video(
    prompt="A serene Japanese garden with cherry blossoms falling",
    duration=15,
    aspect_ratio="16:9",
    resolution="4k",
    frame_rate=30,
    negative_prompt="blurry, low quality, distorted",
    seed=42,  # For reproducibility
    camera_motion={
        "type": "slow_zoom",
        "direction": "in",
        "intensity": 0.3
    }
)
```

## Aspect Ratios

```python
ASPECT_RATIOS = {
    "16:9": "Landscape (YouTube, TV)",
    "9:16": "Portrait (TikTok, Reels, Shorts)",
    "1:1": "Square (Instagram posts)",
    "4:3": "Classic (presentations)",
    "21:9": "Ultra-wide (cinematic)"
}

def select_aspect_ratio(platform: str) -> str:
    """Select aspect ratio for target platform."""
    platform_ratios = {
        "youtube": "16:9",
        "tiktok": "9:16",
        "instagram_reels": "9:16",
        "instagram_post": "1:1",
        "twitter": "16:9",
        "linkedin": "16:9",
        "cinema": "21:9"
    }
    return platform_ratios.get(platform.lower(), "16:9")
```

## Batch Generation

```python
import asyncio
import aiohttp

async def batch_text_to_video(prompts: list[str], **kwargs) -> list[dict]:
    """Generate multiple videos concurrently."""

    async def generate_one(session, prompt):
        async with session.post(
            "https://api.klingai.com/v1/videos/text2video",
            json={"prompt": prompt, **kwargs}
        ) as response:
            return await response.json()

    headers = {
        "Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [generate_one(session, p) for p in prompts]
        return await asyncio.gather(*tasks)

# Usage
prompts = [
    "A sunset over the ocean",
    "A city skyline at night",
    "A forest in autumn"
]

results = asyncio.run(batch_text_to_video(prompts, duration=5))
```

## Quality Tips

```
1. Be Specific
   - Instead of "a dog", use "a golden retriever puppy"
   - Instead of "outside", use "in a sunny park with fall leaves"

2. Include Motion
   - "running", "flying", "spinning slowly"
   - Motion verbs help the AI understand what should happen

3. Specify Lighting
   - "golden hour", "studio lighting", "dramatic shadows"
   - Lighting dramatically affects mood and quality

4. Add Style Cues
   - "cinematic", "documentary style", "anime"
   - Style guides the overall aesthetic

5. Use Quality Modifiers
   - "8K", "photorealistic", "professional"
   - But don't overload with modifiers
```

## Output

Successful execution produces:
- Generated video URL
- Thumbnail image
- Video metadata (duration, resolution)
- Generation parameters used

## Error Handling

Common errors and solutions:
1. **Content Policy Violation**: Modify prompt to comply with guidelines
2. **Invalid Duration**: Check model's supported duration range
3. **Prompt Too Long**: Shorten and focus the prompt
4. **Low Quality Result**: Add quality modifiers, adjust parameters

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Prompt Guide](https://docs.klingai.com/prompts)
- [Text-to-Video API Reference](https://docs.klingai.com/api/text2video)
- [Content Guidelines](https://klingai.com/content-policy)
