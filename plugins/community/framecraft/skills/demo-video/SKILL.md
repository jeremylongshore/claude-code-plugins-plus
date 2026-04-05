---
name: demo-video
description: |
  Generate polished demo videos from a single prompt. Use when the user asks
  to create a demo video, product walkthrough, feature showcase, or animated
  presentation. Trigger with "make a demo video", "create a product video",
  "demo walkthrough", or "feature showcase video".
allowed-tools: Read, Write, Edit, Bash, Glob
version: 1.0.0
author: Srinivas Vaddisrinivas <vaddisrinivas170497@gmail.com>
license: MIT
compatible-with: claude-code
tags: [video, demo, playwright, ffmpeg, edge-tts, mcp]
---
# Demo Video Generator

## Overview

Generate 1920x1080 demo videos with voiceover, transitions, and CSS animations from a single prompt. Orchestrates Playwright (HTML-to-frame rendering), FFmpeg (compositing and transitions), and Edge TTS (neural voiceover) MCP servers.

## Prerequisites

- Python 3.11+ and `uv` package manager
- FFmpeg installed (`ffmpeg -version`)
- Playwright chromium browser (`uv run playwright install chromium`)
- Internet connection for Edge TTS voice synthesis

## Instructions

Install the framecraft plugin from the marketplace:

```bash
claude plugin marketplace add jeremylongshore/claude-code-plugins-plus-skills
claude plugin install framecraft@claude-code-plugins-plus
```

### Quick Start

```bash
uv run python framecraft.py init my-demo        # scaffold a project
uv run python framecraft.py render scenes.json --auto-duration
uv run python framecraft.py validate output.mp4  # quality check
```

### MCP Orchestration

When Playwright, FFmpeg, and Edge TTS MCP servers are available, framecraft orchestrates them directly for maximum control over each frame and audio segment.

### Pipeline Fallback

When MCP servers are not available, framecraft runs an atomic CLI pipeline that handles everything in one call.

### Workflow

1. **Story design** -- Choose a narrative arc (problem-solution, hero journey, before-after)
2. **Scene authoring** -- Write HTML scenes with CSS animations, or use built-in templates
3. **Rendering** -- Playwright captures frames, Edge TTS generates voiceover, FFmpeg composites

## Output

- 1920x1080 MP4 video with voiceover and transitions
- Individual scene previews for iteration
- Validation report for quality assurance

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `ffmpeg: command not found` | FFmpeg not installed | Install via `brew install ffmpeg` or system package manager |
| `playwright._impl._errors.Error` | Chromium not installed | Run `uv run playwright install chromium` |
| `edge_tts.exceptions.NoAudioReceived` | TTS service unavailable | Check internet connection; retry after a few seconds |
| `FileNotFoundError: scenes.json` | Missing scene config | Run `uv run python framecraft.py init my-demo` first |
| Blank or black frames | HTML scene rendering failed | Check HTML syntax and ensure assets are accessible |

## Examples

```json
{
  "scenes": [
    {
      "title": "Meet YourApp",
      "subtitle": "The smarter way to manage tasks",
      "narration": "24 tasks. One dashboard. Zero stress.",
      "voice": "en-US-AndrewNeural",
      "bullets": ["Smart priorities", "Team sync", "One-click reports"],
      "duration": 0
    }
  ],
  "output": "demo.mp4",
  "width": 1920, "height": 1080,
  "voice": "en-US-AndrewNeural",
  "transition": "crossfade"
}
```

`duration: 0` = auto-detect from TTS length + 1.5s buffer.

## Resources

- Source repository with templates and pipeline: [github.com/vaddisrinivas/framecraft](https://github.com/vaddisrinivas/framecraft)
- [Edge TTS voice list](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Playwright documentation](https://playwright.dev/python/docs/intro)
- [FFmpeg documentation](https://ffmpeg.org/documentation.html)
