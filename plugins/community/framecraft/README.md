# framecraft

Generate polished demo videos from a single prompt. Orchestrates Playwright, FFmpeg, and Edge TTS MCP servers to produce 1920x1080 videos with voiceover, transitions, and CSS animations.

## Skills

| Skill | Description |
|-------|-------------|
| `demo-video` | Auto-activates when the user asks to create demo videos, product walkthroughs, or feature showcases |

## Installation

```bash
claude plugin marketplace add jeremylongshore/claude-code-plugins
ccpi install framecraft
```

Or via npm skills registry:
```bash
npx skills add vaddisrinivas/framecraft
```

## Requirements

- Python 3.11+, FFmpeg, Playwright chromium
- Internet connection for Edge TTS voice synthesis (neural voices, free, no API key)
- Edge TTS requires network connectivity for voice generation — no offline fallback

## Permissions

This skill requests scoped Bash access to:
- `Bash(uv:*)` — Run Python environment via uv package manager
- `Bash(ffmpeg:*)` — Run FFmpeg for video compositing and audio mixing
- `Bash(python:*)` — Execute Python scripts for pipeline orchestration

These permissions are required because framecraft orchestrates external command-line tools (Playwright, FFmpeg, Edge TTS) that must be invoked via shell. The scopes ensure Bash calls are restricted to these three tools only.

**Contact:** vaddisrinivas170497@gmail.com

## Links

- [Source Repository](https://github.com/vaddisrinivas/framecraft)
- [License: MIT](https://github.com/vaddisrinivas/framecraft/blob/master/LICENSE)
