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
compatible-with: claude-code, codex, openclaw
---
# Klingai Text To Video

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

## Output

Successful execution produces:
- Generated video URL
- Thumbnail image
- Video metadata (duration, resolution)
- Generation parameters used

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Prompt Guide](https://docs.klingai.com/prompts)
- [Text-to-Video API Reference](https://docs.klingai.com/api/text2video)
- [Content Guidelines](https://klingai.com/content-policy)