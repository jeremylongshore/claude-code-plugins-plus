---
name: runway-prod-checklist
description: |
  Runway prod checklist — AI video generation and creative AI platform.
  Use when working with Runway for video generation, image editing, or creative AI.
  Trigger with phrases like "runway prod checklist", "runway-prod-checklist", "AI video generation".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, runway, ai, video-generation, creative]
compatible-with: claude-code, codex, openclaw
---

# Runway Prod Checklist

## Overview
Implementation patterns for Runway prod checklist — AI video generation platform.

## Prerequisites
- Completed `runway-install-auth` setup

## Instructions

### Step 1: SDK Pattern
```python
from runwayml import RunwayML

client = RunwayML()

task = client.image_to_video.create(
    model='gen3a_turbo',
    prompt_text='A serene lake at dawn, mist rising, birds flying',
    duration=5,
)
result = task.wait_for_task_output()
if result.status == 'SUCCEEDED':
    print(f"Video: {result.output[0]}")
```

## Output
- Runway integration for prod checklist

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check RUNWAYML_API_SECRET |
| 402 Insufficient credits | No credits | Add credits at dev.runwayml.com |
| Task FAILED | Content policy | Adjust prompt |

## Resources
- [Runway API Documentation](https://docs.dev.runwayml.com/)
- [Python SDK](https://github.com/runwayml/sdk-python)

## Next Steps
See related Runway skills for more workflows.
