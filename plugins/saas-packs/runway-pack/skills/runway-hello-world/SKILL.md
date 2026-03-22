---
name: runway-hello-world
description: |
  Runway hello world — AI video generation and creative AI platform.
  Use when working with Runway for video generation, image editing, or creative AI.
  Trigger with phrases like "runway hello world", "runway-hello-world", "AI video generation".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, runway, ai, video-generation, creative]
compatible-with: claude-code, codex, openclaw
---

# Runway Hello World

## Overview
Generate your first AI video from a text prompt using Runway's Gen-3 Alpha model.

## Prerequisites
- Completed `runway-install-auth`
- API credits available in your Runway account

## Instructions

### Step 1: Text-to-Video Generation
```python
from runwayml import RunwayML

client = RunwayML()

# Create a text-to-video generation task
task = client.image_to_video.create(
    model='gen3a_turbo',
    prompt_text='A golden retriever running through a field of sunflowers, cinematic lighting, slow motion',
    duration=5,  # 5 or 10 seconds
    ratio='16:9',  # 16:9 or 9:16
)
print(f"Task created: {task.id}")
```

### Step 2: Poll for Completion
```python
import time

# The SDK has a built-in helper for polling
task_result = client.tasks.retrieve(task.id)

# Or poll manually
while task_result.status not in ('SUCCEEDED', 'FAILED'):
    time.sleep(5)
    task_result = client.tasks.retrieve(task.id)
    print(f"  Status: {task_result.status}")

if task_result.status == 'SUCCEEDED':
    print(f"Video URL: {task_result.output[0]}")
else:
    print(f"Failed: {task_result.failure}")
```

### Step 3: Download the Video
```python
import urllib.request

if task_result.status == 'SUCCEEDED':
    video_url = task_result.output[0]
    urllib.request.urlretrieve(video_url, 'output.mp4')
    print("Video saved to output.mp4")
```

### Step 4: Using the Built-in Wait Helper
```python
# Simpler approach — SDK polls automatically
task = client.image_to_video.create(
    model='gen3a_turbo',
    prompt_text='Ocean waves crashing on rocky cliffs at sunset, aerial view',
    duration=5,
)
# Wait for completion (default timeout: 10 minutes)
result = task.wait_for_task_output()
print(f"Video: {result.output[0]}")
```

## Output
- Video generation task created
- Task polled until completion
- Generated video URL retrieved
- Video downloaded to local file

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Task `FAILED` | Content policy violation | Adjust prompt to comply with content policy |
| `402 Insufficient credits` | No API credits | Add credits at dev.runwayml.com |
| Timeout | Generation taking too long | Increase timeout or use shorter duration |
| Low quality output | Prompt too vague | Add style keywords: "cinematic", "4K", "professional" |

## Resources
- [API Getting Started](https://docs.dev.runwayml.com/guides/using-the-api/)
- [API Reference](https://docs.dev.runwayml.com/api/)
- [Input Parameters](https://docs.dev.runwayml.com/assets/inputs/)

## Next Steps
Advanced text-to-video: `runway-core-workflow-a`
