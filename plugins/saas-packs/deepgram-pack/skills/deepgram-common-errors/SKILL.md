---
name: deepgram-common-errors
description: |
  Diagnose and fix common Deepgram errors and issues.
  Use when troubleshooting Deepgram API errors, debugging transcription failures,
  or resolving integration issues.
  Trigger with phrases like "deepgram error", "deepgram not working",
  "fix deepgram", "deepgram troubleshoot", "transcription failed".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Common Errors

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive guide to diagnosing and fixing common Deepgram integration errors including authentication, audio processing, rate limiting, WebSocket, and transcription quality issues.

## Prerequisites
- Deepgram API key configured
- Access to application logs
- `curl` available for API testing

## Instructions

### Step 1: Quick Diagnostic
Test API connectivity with a simple curl request to verify key and endpoint.

### Step 2: Identify Error Category
Match the HTTP status code to the error reference table below.

### Step 3: Apply Fix
Follow the specific resolution for the error type.

### Step 4: Verify Resolution
Re-run the diagnostic to confirm the fix works.

## Output
- Error identified and categorized
- Root cause determined
- Fix applied and verified

## Error Handling

### Error Reference Table

| HTTP Code | Error Code | Common Cause | Solution |
|-----------|------------|--------------|----------|
| 400 | BAD_REQUEST | Invalid audio format | Check audio encoding, validate file header |
| 401 | INVALID_AUTH | Missing/invalid API key | Verify `DEEPGRAM_API_KEY`, check header format |
| 403 | ACCESS_DENIED | Permission denied | Check key permissions, verify account tier |
| 404 | NOT_FOUND | Invalid endpoint | Check API URL path |
| 413 | PAYLOAD_TOO_LARGE | File too large | Split audio with `ffmpeg -f segment` |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests | Implement exponential backoff with jitter |
| 500 | INTERNAL_ERROR | Server error | Retry with backoff, check status page |
| 503 | SERVICE_UNAVAILABLE | Service down | Check status.deepgram.com |

### WebSocket Errors
- **Connection Refused**: Check firewall rules, verify WSS URL
- **Connection Dropped**: Implement KeepAlive messages every 10 seconds

### Transcription Quality Issues
- Check audio sample rate (16kHz recommended)
- Verify audio is mono or stereo
- Test with known-good audio file
- Check language setting matches audio content
- Use `alternatives: 3, words: true` for debugging confidence scores

## Examples

### Quick API Test
```bash
set -euo pipefail
curl -X POST 'https://api.deepgram.com/v1/listen?model=nova-2' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: audio/wav" \
  --data-binary @test.wav
```

### Validate Audio File Header
Check first bytes: `52494646` (WAV), `fff3/fffb` (MP3), `664c6143` (FLAC), `4f676753` (OGG).

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Deepgram Error Codes](https://developers.deepgram.com/docs/error-handling)
- [Deepgram Status Page](https://status.deepgram.com)
- [Deepgram Support](https://developers.deepgram.com/support)