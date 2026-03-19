---
name: deepgram-debug-bundle
description: |
  Collect Deepgram debug evidence for support and troubleshooting.
  Use when preparing support tickets, investigating issues,
  or collecting diagnostic information for Deepgram problems.
  Trigger with phrases like "deepgram debug", "deepgram support",
  "collect deepgram logs", "deepgram diagnostic", "deepgram debug bundle".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Collect comprehensive debug information for Deepgram support tickets and troubleshooting. Bundles environment info, API connectivity tests, request logs, audio analysis, and reproduction scripts into a single archive.

## Prerequisites
- Deepgram API key configured
- Access to application logs
- Sample audio file that reproduces issue

## Instructions

### Step 1: Collect Environment Info
Gather system and SDK version information (Node.js, Python, OS, SDK versions).

### Step 2: Test API Connectivity
Verify REST API and WebSocket endpoint reachability with `curl` against `api.deepgram.com`.

### Step 3: Capture Request/Response
Use `DeepgramDebugger` class to log full request/response details with timing and error capture.

### Step 4: Create Minimal Reproduction
Build a standalone script that reproduces the issue with the NASA podcast sample audio.

### Step 5: Analyze Audio (if applicable)
Run `ffprobe` analysis on the audio file to verify format, encoding, and duration.

### Step 6: Package Debug Bundle
Run `collect-debug-bundle.sh` to compile environment, connectivity, logs, and audio analysis into a `.tar.gz` archive.

## Output
- `deepgram-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `environment.txt` - System and SDK versions
  - `connectivity.txt` - API connectivity test results
  - `app-logs.txt` - Recent application logs (sanitized)
  - `audio-analysis.txt` - Audio file details (if provided)
  - `README.txt` - Bundle description and issue template

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| API connectivity fails | Invalid key or network | Verify `DEEPGRAM_API_KEY` and network access |
| Empty response | Silent or corrupt audio | Check audio format with `ffprobe` |
| SDK not found | Missing dependency | Run `npm list @deepgram/sdk` or `pip show deepgram-sdk` |

## Examples

### Support Ticket Template
Include: issue summary, environment details, request IDs, steps to reproduce, expected vs actual behavior, and attach the debug bundle archive.

### Quick Connectivity Test
```bash
set -euo pipefail
curl -s -o /dev/null -w "%{http_code}" \
  -X GET 'https://api.deepgram.com/v1/projects' \
  -H "Authorization: Token $DEEPGRAM_API_KEY"
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Deepgram Support Portal](https://developers.deepgram.com/support)
- [Deepgram Community Discord](https://discord.gg/deepgram)
- [Deepgram Status Page](https://status.deepgram.com)