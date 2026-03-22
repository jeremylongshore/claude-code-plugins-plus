---
name: runway-core-workflow-b
description: |
  Runway core workflow b — AI video generation and creative AI platform.
  Use when working with Runway for video generation, image editing, or creative AI.
  Trigger with phrases like "runway core workflow b", "runway-core-workflow-b", "AI video generation".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, runway, ai, video-generation, creative]
compatible-with: claude-code, codex, openclaw
---

# Runway Core Workflow B

## Overview
Image-to-video and video-to-video generation: animate still images and transform existing videos.

## Prerequisites
- Completed `runway-core-workflow-a`

## Instructions

### Step 1: Image-to-Video
```python
from runwayml import RunwayML
client = RunwayML()

# Animate a still image
task = client.image_to_video.create(
    model='gen3a_turbo',
    prompt_image='https://your-cdn.com/landscape.jpg',  # URL to source image
    prompt_text='Camera slowly pans right revealing mountains, gentle wind in trees',
    duration=5,
)
result = task.wait_for_task_output()
print(f"Animated video: {result.output[0]}")
```

### Step 2: Image-to-Video with Data URI
```python
import base64

# Load local image as data URI
with open('photo.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()
    data_uri = f"data:image/jpeg;base64,{image_data}"

task = client.image_to_video.create(
    model='gen3a_turbo',
    prompt_image=data_uri,
    prompt_text='Subtle motion, gentle camera push in, atmospheric lighting',
    duration=5,
)
```

### Step 3: Video-to-Video (Style Transfer)
```python
# Transform an existing video with a new style
task = client.video_to_video.create(
    model='gen3a_turbo',
    prompt_video='https://your-cdn.com/input-video.mp4',
    prompt_text='Transform to watercolor painting style, soft colors, artistic brushstrokes',
)
result = task.wait_for_task_output()
print(f"Styled video: {result.output[0]}")
```

### Step 4: Image Specifications
```text
Supported formats: JPEG, PNG, WebP
Supported resolutions:
  - Gen-3 Alpha Turbo: 1280x768 or 768x1280
  - Input images are automatically resized
Max file size: 16MB (URL), varies for data URI
```

## Output
- Still images animated with motion prompts
- Local images encoded as data URIs
- Videos restyled with text prompts
- Proper image format handling

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `400 Invalid image` | Unsupported format | Use JPEG, PNG, or WebP |
| `413 Image too large` | File exceeds limit | Resize to under 16MB |
| Poor animation quality | Prompt doesn't describe motion | Add camera/motion keywords |
| Style transfer too subtle | Weak prompt | Be more specific about target style |

## Resources
- [Runway API Reference](https://docs.dev.runwayml.com/api/)
- [Input Parameters](https://docs.dev.runwayml.com/assets/inputs/)
- [SDKs](https://docs.dev.runwayml.com/api-details/sdks/)

## Next Steps
Error handling: `runway-common-errors`
