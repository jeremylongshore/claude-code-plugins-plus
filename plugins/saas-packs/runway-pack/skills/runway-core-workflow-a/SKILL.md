---
name: runway-core-workflow-a
description: |
  Runway core workflow a — AI video generation and creative AI platform.
  Use when working with Runway for video generation, image editing, or creative AI.
  Trigger with phrases like "runway core workflow a", "runway-core-workflow-a", "AI video generation".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, runway, ai, video-generation, creative]
compatible-with: claude-code, codex, openclaw
---

# Runway Core Workflow A

## Overview
Advanced text-to-video generation: prompt engineering, model selection, parameter tuning, and batch generation.

## Prerequisites
- Completed `runway-hello-world`

## Instructions

### Step 1: Model Selection
```python
from runwayml import RunwayML
client = RunwayML()

# Available models:
# gen3a_turbo   — Fast, lower cost, good quality
# gen4_turbo    — Latest model, highest quality

task = client.image_to_video.create(
    model='gen4_turbo',
    prompt_text='A futuristic cityscape at night with flying cars and neon signs, cyberpunk aesthetic',
    duration=10,
    ratio='16:9',
)
result = task.wait_for_task_output()
```

### Step 2: Prompt Engineering Tips
```python
# Structure: Subject + Action + Setting + Style + Camera
prompts = [
    # Good: specific, visual, stylistic
    "A red fox walking through a snowy forest, soft winter light, documentary style, tracking shot",

    # Good: detailed motion and camera
    "Waves of golden wheat swaying in the wind, drone flyover, warm sunset, cinematic grain",

    # Bad: too abstract
    # "Something beautiful happening" — too vague
]
```

### Step 3: Batch Generation
```python
import asyncio

prompts = [
    "A butterfly emerging from a cocoon, macro lens, time-lapse, studio lighting",
    "Rain falling on a Tokyo street at night, reflections, neon, dolly zoom",
    "A chef preparing sushi in a traditional kitchen, close-up, warm lighting",
]

tasks = []
for prompt in prompts:
    task = client.image_to_video.create(
        model='gen3a_turbo',
        prompt_text=prompt,
        duration=5,
    )
    tasks.append(task)
    print(f"Queued: {task.id}")

# Wait for all
for task in tasks:
    result = task.wait_for_task_output()
    status = "OK" if result.status == "SUCCEEDED" else "FAILED"
    print(f"  {task.id}: {status}")
```

### Step 4: Output Format Options
```python
task = client.image_to_video.create(
    model='gen3a_turbo',
    prompt_text='Abstract paint mixing in slow motion, vibrant colors, black background',
    duration=5,
    ratio='9:16',      # Vertical for mobile/TikTok
    # ratio='16:9',    # Landscape for YouTube
    # ratio='1:1',     # Square for Instagram
)
```

## Output
- Videos generated with optimal model selection
- Prompt engineering best practices applied
- Batch generation for multiple videos
- Output in various aspect ratios

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Low quality | Gen3a_turbo for complex scene | Use gen4_turbo for higher quality |
| Content rejection | Policy violation | Remove violent/explicit content from prompt |
| Slow generation | High queue | Use turbo model or try later |
| Wrong aspect ratio | Not specified | Always set ratio explicitly |

## Resources
- [Runway API Documentation](https://docs.dev.runwayml.com/)
- [Input Parameters](https://docs.dev.runwayml.com/assets/inputs/)

## Next Steps
Image-to-video: `runway-core-workflow-b`
