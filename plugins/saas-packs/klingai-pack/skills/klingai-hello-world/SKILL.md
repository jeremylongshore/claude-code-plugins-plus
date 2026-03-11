---
name: klingai-hello-world
description: |
  Create your first Kling AI video generation with a simple example. Use when learning Kling AI
  or testing your setup. Trigger with phrases like 'kling ai hello world', 'first kling ai video',
  'klingai quickstart', 'test klingai'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Hello World

## Overview

This skill provides a minimal working example to generate your first AI video with Kling AI, verify your integration is functioning, and understand the basic request/response pattern.

## Prerequisites

- Kling AI API key configured
- Python 3.8+ or Node.js 18+
- HTTP client library installed

## Instructions

Follow these steps to create your first video:

1. **Verify Authentication**: Ensure your API key is configured
2. **Submit Generation Request**: Send a text-to-video request
3. **Poll for Status**: Check job status until complete
4. **Download Result**: Retrieve the generated video URL
5. **Verify Output**: Preview or download the video

## Output

Successful execution produces:
- Job ID for tracking
- Video URL for download/streaming
- Thumbnail URL for preview
- Generation metadata (duration, resolution, timing)

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Documentation](https://docs.klingai.com/)
- [Prompt Guide](https://docs.klingai.com/prompts)
- [API Reference](https://docs.klingai.com/api)