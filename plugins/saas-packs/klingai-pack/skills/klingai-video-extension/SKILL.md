---
name: klingai-video-extension
description: |
  Execute extend video duration using Kling AI continuation features. Use when creating longer videos
  from shorter clips or building seamless sequences. Trigger with phrases like 'klingai extend video',
  'kling ai video continuation', 'klingai longer video', 'extend klingai clip'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Video Extension

## Overview

This skill demonstrates extending video duration using Kling AI's continuation features, including seamless extensions, multi-segment generation, and narrative continuation.

## Prerequisites

- Kling AI API key configured
- Existing video or generation job
- Python 3.8+

## Instructions

Follow these steps for video extension:

1. **Get Base Video**: Have initial video ready
2. **Configure Extension**: Set continuation parameters
3. **Generate Extension**: Submit continuation request
4. **Merge Segments**: Combine video parts
5. **Review Continuity**: Check seamless transitions

## Output

Successful execution produces:
- Extended video sequences
- Seamless segment transitions
- Multi-segment concatenation
- Loop-ready videos

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Video Extension](https://docs.klingai.com/extend)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Video Concatenation](https://trac.ffmpeg.org/wiki/Concatenate)