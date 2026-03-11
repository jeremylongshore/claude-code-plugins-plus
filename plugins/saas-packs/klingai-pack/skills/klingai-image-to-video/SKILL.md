---
name: klingai-image-to-video
description: |
  Generate videos from static images using Kling AI. Use when animating images, creating
  motion from stills, or building image-based content. Trigger with phrases like 'klingai image to video',
  'kling ai animate image', 'klingai img2vid', 'animate picture klingai'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Klingai Image To Video

## Overview

This skill demonstrates using Kling AI's image-to-video capabilities to animate static images, including motion control, style preservation, and seamless transitions.

## Prerequisites

- Kling AI API key configured
- Source image (PNG, JPG, WEBP)
- Python 3.8+ with image processing libraries

## Instructions

Follow these steps for image-to-video:

1. **Prepare Image**: Ensure image meets requirements
2. **Configure Motion**: Define animation parameters
3. **Generate Video**: Submit to API
4. **Review Output**: Verify animation quality
5. **Iterate**: Refine motion settings

## Output

Successful execution produces:
- Animated video from static image
- Controlled motion and camera effects
- Style-preserved animation
- Multiple output formats

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Image-to-Video](https://docs.klingai.com/image-to-video)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [Motion Control Guide](https://docs.klingai.com/motion)
