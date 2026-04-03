---
name: demo-video
description: |
  Generate polished demo videos from a single prompt. Use when the user asks
  to create a demo video, product walkthrough, feature showcase, or animated
  presentation. Trigger with "make a demo video", "create a product video",
  "demo walkthrough", or "feature showcase video".
allowed-tools: Read, Write, Edit, Bash(uv:*), Bash(ffmpeg:*), Bash(python:*), Glob
version: 1.0.0
author: vaddisrinivas <https://github.com/vaddisrinivas>
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

## Installation

Install the full framecraft plugin for complete MCP integration:

```bash
claude plugin install framecraft
```

Or install directly from GitHub:

```bash
npx skills add vaddisrinivas/framecraft
```

## How It Works

1. **Story design** -- Choose a narrative arc (problem-solution, hero journey, before-after)
2. **Scene authoring** -- Write HTML scenes with CSS animations, or use built-in templates
3. **Rendering** -- Playwright captures frames, Edge TTS generates voiceover, FFmpeg composites

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

## Output

- 1920x1080 MP4 video with voiceover and transitions
- Individual scene previews for iteration
- Validation report for quality assurance

## Repository

Full source, templates, and examples: [github.com/vaddisrinivas/framecraft](https://github.com/vaddisrinivas/framecraft)
